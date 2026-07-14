import json
import io
import os
import pypdf
import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage
from app.database import get_session, engine
from app.models.interview import Interview, Transcript, EvaluationReport, UserProfile, StudyPlan
from app.models.profile import CandidateProfile, JobProfile, GapAnalysis, CompanyProfile, InterviewBlueprint
from app.agents.interview_agent import interview_agent
from app.agents.interview_planner import normalize_interview_objectives, build_contextual_fallback_question
from app.agents.profiles import ROLE_PROFILES

from app.services.auth_service import auth_service

router = APIRouter(prefix="/api/v1/interviews", tags=["interviews"])

def log_structured_event(event_name: str, payload: dict):
    import json
    import os
    import datetime
    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "event": event_name,
        "payload": payload
    }
    try:
        os.makedirs("logs", exist_ok=True)
        with open(os.path.join("logs", "structured_trace.jsonl"), "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except Exception as e:
        print(f"Failed to write structured log: {e}")

# --- Request/Response Models ---
class InterviewCreate(BaseModel):
    role: str
    difficulty: str
    duration_minutes: int
    mode: Optional[str] = "quick"
    focus_topics: Optional[List[str]] = None
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None
    company_name: Optional[str] = None
    resume_path: Optional[str] = None

class PrepareInterviewCreate(BaseModel):
    role: str
    difficulty: str
    duration_minutes: int
    mode: Optional[str] = "quick"
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None
    company_name: Optional[str] = None
    resume_path: Optional[str] = None

class ParsePrivateFilePayload(BaseModel):
    resume_path: str

class InterviewRead(BaseModel):
    id: str
    role: str
    difficulty: str
    duration_minutes: int
    max_question_count: int
    question_count: int
    status: str
    mode: str
    focus_topics_json: Optional[str] = None
    resume_text: Optional[str] = None
    jd_text: Optional[str] = None
    gap_analysis_json: Optional[str] = None
    company_name: Optional[str] = None
    topic_tree_json: Optional[str] = None
    knowledge_model_json: Optional[str] = None
    concept_coverage_json: Optional[str] = None
    project_investigation_json: Optional[str] = None
    interview_objectives_json: Optional[str] = None
    interview_phase: Optional[str] = "INTRODUCTION"
    debug_dashboard_json: Optional[str] = "{}"
    created_at: datetime
    ended_at: Optional[datetime]


class TranscriptRead(BaseModel):
    sender: str
    text: str
    timestamp: datetime
    topic: Optional[str]
    score: Optional[int] = None
    reasoning_summary: Optional[str] = None
    secondary_topics: Optional[List[str]] = None
    difficulty: Optional[str] = None
    audio_url: Optional[str] = None
    turn_metadata_json: Optional[str] = None

class InterviewDetailRead(InterviewRead):
    transcripts: List[TranscriptRead]

class StudyPlanRead(BaseModel):
    id: str
    user_id: str
    associated_interview_id: Optional[str] = None
    roadmap: List[Dict[str, Any]]
    recommended_resources: List[Dict[str, Any]]
    practice_questions: List[str]
    status: str
    created_at: datetime

class CoachingRecommendationsRead(BaseModel):
    study_next: Optional[StudyPlanRead] = None
    next_interview: Optional[Dict[str, Any]] = None
    impactful_weaknesses: List[Dict[str, Any]]


class EvaluationReportRead(BaseModel):
    id: str
    interview_id: str
    overall_score: int
    technical_score: int
    communication_score: int
    explanation_score: int
    problem_solving_score: int
    behavioral_score: int
    summary: str
    strengths: List[str]
    categorized_weaknesses: Dict[str, List[str]]
    topic_performance: Dict[str, int]
    evaluation_version: str
    created_at: datetime
    
    # New fields dynamically loaded from raw_json
    ownership_score: Optional[int] = None
    interview_completion_score: Optional[int] = None
    evaluation_evidence: Optional[Dict[str, Any]] = None
    claim_verification_summary: Optional[Dict[str, List[str]]] = None
    learning_plan: Optional[Dict[str, List[str]]] = None
    recommendations: Optional[List[str]] = None
    hire_recommendation: Optional[str] = None
    confidence_level: Optional[str] = None

# --- Profile Models ---
class TopicMasteryDetail(BaseModel):
    average_score: float
    latest_score: int
    attempts: int
    trend_direction: str
    mastery_state: str

class ReadinessDetail(BaseModel):
    score: int
    confidence: str
    coverage_ratio: float

class RolePerformanceDetail(BaseModel):
    average_score: float
    attempts: int

class HistoryTrendDetail(BaseModel):
    date: str
    score: int
    role: str

class RecommendationDetail(BaseModel):
    type: str
    role: str
    focus_topics: List[str]
    reason: str

class UserProfileRead(BaseModel):
    user_id: str
    topic_mastery: Dict[str, TopicMasteryDetail]
    readiness_scores: Dict[str, ReadinessDetail]
    role_performance: Dict[str, RolePerformanceDetail]
    history_trends: List[HistoryTrendDetail]
    recommendations: List[RecommendationDetail]
    last_updated: datetime


# --- Helpers ---
def get_max_questions(duration: int) -> int:
    if duration <= 5:
        return 5
    elif duration <= 15:
        return 10
    else:
        return 15

def merge_gap_objectives(plan_objectives: Dict[str, Any], gap_analysis: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Makes resume/JD objectives first-class interview objectives instead of passive
    prompt context. Gap objectives are treated as must-verify because they are
    derived from the user's actual resume/JD.
    """
    normalized = normalize_interview_objectives(plan_objectives)
    if not gap_analysis:
        return normalized

    gap_objectives = normalize_interview_objectives(gap_analysis.get("interview_objectives"))
    merged_must = {}
    for name, status in gap_objectives.get("must_verify", {}).items():
        merged_must[name] = status
    for name, status in normalized.get("must_verify", {}).items():
        if name not in merged_must:
            merged_must[name] = status

    return {
        "must_verify": merged_must,
        "nice_to_verify": normalized.get("nice_to_verify", {})
    }

def build_reinterview_objectives(focus_topics: List[str], plan_objectives: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_interview_objectives(plan_objectives)
    focus_must = {}
    for topic in focus_topics[:5]:
        clean_topic = str(topic).strip()
        if clean_topic:
            focus_must[f"Verify improvement in {clean_topic}"] = "unverified"
    for name, status in normalized.get("must_verify", {}).items():
        if name not in focus_must:
            focus_must[name] = status
    return {
        "must_verify": focus_must or normalized.get("must_verify", {}),
        "nice_to_verify": normalized.get("nice_to_verify", {})
    }

def compute_evaluation_report(interview_id: str, db: Session) -> EvaluationReport:
    """
    Computes a hybrid evaluation report combining Gemini's full transcript review
    with the objective turn-by-turn scores collected during the session.
    """
    # 1. Fetch interview session
    interview = db.get(Interview, interview_id)
    if not interview:
        raise ValueError("Interview session not found.")
        
    # Check if a report already exists to prevent duplicate runs
    existing = db.exec(
        select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
    ).first()
    if existing:
        return existing
        
    # 2. Fetch all transcripts sorted chronologically
    statement = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.timestamp.asc())
    transcripts_list = db.exec(statement).all()
    
    # Run the deferred LLM terminology cleanup pass on all candidate turns concurrently
    from app.services.transcript_normalizer import normalize_transcript
    import asyncio
    
    async def normalize_all():
        tasks = []
        for t in transcripts_list:
            if t.sender == "candidate" and t.text:
                async def norm_task(trans_obj):
                    try:
                        trans_obj.text = await normalize_transcript(trans_obj.text, run_gemini=True)
                    except Exception as err:
                        print(f"[ERROR] Failed to normalize transcript {trans_obj.id} in evaluation: {err}")
                tasks.append(asyncio.create_task(norm_task(t)))
        if tasks:
            await asyncio.gather(*tasks)
            
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        loop.run_until_complete(normalize_all())
        db.add_all(transcripts_list)
        db.commit()
    except Exception as n_err:
        print(f"[WARNING] Deferred normalizer pass failed: {n_err}")
    
    # 3. Calculate objective Turn Score Average (Phase 2 scores)
    candidate_scores = [
        t.score for t in transcripts_list 
        if t.sender == "candidate" and t.score is not None and t.score > 0
    ]
    
    if candidate_scores:
        avg_score = sum(candidate_scores) / len(candidate_scores)
        base_score = avg_score * 20  # Scale 1-5 rating to 0-100 score
    else:
        base_score = 60 # Default fallback score
        
    # 4. Prep payload for the Evaluation Agent
    agent_transcripts_payload = []
    for t in transcripts_list:
        sec_topics = []
        if t.secondary_topics_json:
            try:
                sec_topics = json.loads(t.secondary_topics_json)
            except:
                pass
        agent_transcripts_payload.append({
            "sender": t.sender,
            "text": t.text,
            "topic": t.topic,
            "score": t.score,
            "reasoning_summary": t.reasoning_summary,
            "secondary_topics": sec_topics,
            "difficulty": t.difficulty
        })
        
    # 5. Execute Evaluation Agent (runs LLM context analysis)
    try:
        topic_tree = json.loads(interview.topic_tree_json) if interview.topic_tree_json else None
    except:
        topic_tree = None
    try:
        knowledge_model = json.loads(interview.knowledge_model_json) if interview.knowledge_model_json else None
    except:
        knowledge_model = None
    try:
        concept_coverage = json.loads(interview.concept_coverage_json) if interview.concept_coverage_json else None
    except:
        concept_coverage = None
    try:
        interview_objectives = json.loads(interview.interview_objectives_json) if interview.interview_objectives_json else None
    except:
        interview_objectives = None
    try:
        project_investigation = json.loads(interview.project_investigation_json) if interview.project_investigation_json else None
    except:
        project_investigation = None
        
    from app.agents.evaluation_agent import run_evaluation
    eval_data = run_evaluation(
        role=interview.role, 
        difficulty=interview.difficulty, 
        transcripts=agent_transcripts_payload,
        topic_tree=topic_tree,
        knowledge_model=knowledge_model,
        concept_coverage=concept_coverage,
        interview_objectives=interview_objectives,
        project_investigation=project_investigation
    )
    
    # 6. Apply Hybrid Score Calculation (60% LLM + 40% Objective Turn Score)
    def calculate_hybrid(llm_val):
        return int(0.6 * llm_val + 0.4 * base_score)
        
    tech_score = calculate_hybrid(eval_data.get("technical_score", 60))
    comm_score = calculate_hybrid(eval_data.get("communication_score", 60))
    expl_score = calculate_hybrid(eval_data.get("explanation_score", 60))
    prob_score = calculate_hybrid(eval_data.get("problem_solving_score", 60))
    beh_score = calculate_hybrid(eval_data.get("behavioral_score", 60))
    
    # Compute overall score
    llm_overall = eval_data.get("overall_score")
    if not llm_overall:
        # Default overall calculation as average of categories
        llm_overall = int(sum([
            eval_data.get("technical_score", 60),
            eval_data.get("communication_score", 60),
            eval_data.get("explanation_score", 60),
            eval_data.get("problem_solving_score", 60),
            eval_data.get("behavioral_score", 60)
        ]) / 5)
        
    overall_score = calculate_hybrid(llm_overall)
    
    # 7. Save report in DB
    report = EvaluationReport(
        interview_id=interview_id,
        overall_score=overall_score,
        technical_score=tech_score,
        communication_score=comm_score,
        explanation_score=expl_score,
        problem_solving_score=prob_score,
        behavioral_score=beh_score,
        summary=eval_data.get("summary", "No summary generated."),
        strengths_json=json.dumps(eval_data.get("strengths", [])),
        categorized_weaknesses_json=json.dumps(eval_data.get("categorized_weaknesses", {})),
        topic_performance_json=json.dumps(eval_data.get("topic_performance", {})),
        evaluation_version="v1.0",
        raw_json=eval_data.get("raw_json", "{}")
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    log_structured_event("Evaluation Generated", {
        "interview_id": interview_id,
        "overall_score": overall_score
    })
    
    # Trigger Memory Agent and Planning Agent to rebuild user profile and study plan
    try:
        from app.agents.memory_agent import update_user_profile
        profile_record = update_user_profile(db, interview.user_id)
        
        from app.agents.planning_agent import generate_study_plan
        generate_study_plan(db, profile_record, interview_id)
    except Exception as e:
        print(f"Memory Agent / Planning Agent update failed: {e}")
        
    return report


# --- Personalization Helpers ---
def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to parse PDF file: {e}")

def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8").strip()
    except Exception:
        return file_bytes.decode("latin-1").strip()

def generate_gap_analysis(resume_text: Optional[str], jd_text: Optional[str], db: Session, user_id: str = "default") -> Dict[str, Any]:
    """
    Calls Gemini to extract background details, required skills, and comparison objectives.
    Integrates results with the Memory System to calculate a Job-Specific Readiness Score.
    """
    if not resume_text and not jd_text:
        return {}
        
    extracted_resume = {"skills": [], "projects": [], "strengths": []}
    extracted_jd = {"required_skills": [], "responsibilities": []}
    gap_analysis = {"missing_skills": [], "focus_areas": []}
    interview_objectives = []
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    use_gemini = api_key and api_key != "placeholder_api_key" and api_key != "your_gemini_api_key_here"
    
    if use_gemini:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.3,
                google_api_key=api_key,
                response_mime_type="application/json",
                max_retries=1
            )
            
            system_prompt = (
                "You are an expert AI recruiting assistant specializing in technical gap analysis and interview personalization.\n"
                "You will be given a candidate's resume, a target job description (JD), or both. Analyze the inputs and return a JSON object.\n\n"
                "Instructions based on inputs:\n"
                "1. Resume-Only (if JD is empty):\n"
                "   - Extract candidate's skills, projects (title and description), and key strengths.\n"
                "   - Generate 3-5 specific 'interview_objectives' focusing on validating projects, deep-diving into claimed skills, and exploring strengths.\n"
                "   - Leave JD fields and missing skills empty.\n"
                "2. JD-Only (if Resume is empty):\n"
                "   - Extract target job required_skills and responsibilities.\n"
                "   - Generate 3-5 specific 'interview_objectives' focusing on assessing understanding of required technologies and responsibilities.\n"
                "   - Leave Resume fields empty.\n"
                "3. Resume + JD (if both are provided):\n"
                "   - Perform all extractions listed above.\n"
                "   - Compare the Resume against the JD to identify missing_skills (skills required by the JD but missing from the resume) and target focus_areas.\n"
                "   - Generate 3-5 specific 'interview_objectives' focusing on testing matching projects, probing missing skills, and addressing conceptual gaps.\n\n"
                "You MUST return a JSON object matching this schema:\n"
                "{\n"
                "  \"extracted_resume\": {\n"
                "    \"skills\": [\"skill1\", ...],\n"
                "    \"projects\": [{\"title\": \"Project Title\", \"description\": \"Summary of work...\"}],\n"
                "    \"strengths\": [\"strength1\", ...]\n"
                "  },\n"
                "  \"extracted_jd\": {\n"
                "    \"required_skills\": [\"required1\", ...],\n"
                "    \"responsibilities\": [\"responsibility1\", ...]\n"
                "  },\n"
                "  \"gap_analysis\": {\n"
                "    \"missing_skills\": [\"missing1\", ...],\n"
                "    \"focus_areas\": [\"focus1\", ...]\n"
                "  },\n"
                "  \"interview_objectives\": [\n"
                "    \"objective1\",\n"
                "    ...\n"
                "  ]\n"
                "}"
            )
            
            prompt_content = {
                "resume": resume_text or "",
                "jd": jd_text or ""
            }
            
            response = llm.invoke([
                ("system", system_prompt),
                ("human", f"Analyze and compare these profiles:\n\n{json.dumps(prompt_content, indent=2)}")
            ])
            
            content_val = response.content
            if isinstance(content_val, list):
                content_val = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content_val)
            elif not isinstance(content_val, str):
                content_val = str(content_val)
            data = json.loads(content_val.strip())
            extracted_resume = data.get("extracted_resume", extracted_resume)
            extracted_jd = data.get("extracted_jd", extracted_jd)
            gap_analysis = data.get("gap_analysis", gap_analysis)
            interview_objectives = data.get("interview_objectives", interview_objectives)
            
        except Exception as e:
            print(f"[WARNING] Gap analysis Gemini run failed: {e}. Using mock fallback.")
            use_gemini = False
            
    if not use_gemini:
        # Fallback Mock data
        if resume_text and not jd_text:
            extracted_resume = {
                "skills": ["Python", "PyTorch"],
                "projects": [{"title": "Retinal Age Prediction", "description": "Mock description of age prediction"}],
                "strengths": ["Stated experience in PyTorch and computer vision."]
            }
            interview_objectives = [
                "Verify PyTorch knowledge through the Retinal Age Prediction project",
                "Deep-dive into Python programming concepts",
                "Explore computer vision experience"
            ]
        elif jd_text and not resume_text:
            extracted_jd = {
                "required_skills": ["Transformers", "PyTorch", "Qdrant"],
                "responsibilities": ["Design and deploy agentic AI workflows."]
            }
            interview_objectives = [
                "Assess understanding of Transformers and self-attention mechanism",
                "Verify PyTorch coding competence",
                "Evaluate familiarity with vector databases and Qdrant"
            ]
        else:
            extracted_resume = {
                "skills": ["Python", "PyTorch"],
                "projects": [{"title": "Retinal Age Prediction", "description": "Mock description of age prediction"}],
                "strengths": ["Stated experience in PyTorch and computer vision."]
            }
            req_skills = ["Transformers", "PyTorch", "Qdrant"]
            if jd_text and "python" in jd_text.lower():
                req_skills.append("Python")
            extracted_jd = {
                "required_skills": req_skills,
                "responsibilities": ["Design and deploy agentic AI workflows."]
            }
            gap_analysis = {
                "missing_skills": ["Transformers", "Qdrant"],
                "focus_areas": ["Transformers Attention Math", "Qdrant Vector Databases"]
            }
            interview_objectives = [
                "Verify PyTorch knowledge through the Retinal Age Prediction project",
                "Test understanding of Transformers and Self-Attention mechanisms",
                "Evaluate vector search concepts and Qdrant integration"
            ]
            
    # Calculate Job-Specific Readiness Score by integrating Memory System
    from app.agents.memory_agent import is_topic_match
    profile = db.exec(select(UserProfile).where(UserProfile.user_id == user_id)).first()
    mastery = {}
    if profile:
        try:
            mastery = json.loads(profile.topic_mastery_json)
        except:
            pass
            
    required_skills = extracted_jd.get("required_skills", [])
    
    if required_skills:
        scores = []
        tested_count = 0
        claimed_untested_count = 0
        untested_gaps_count = 0
        
        for skill in required_skills:
            matched_stats = None
            for mastered_topic, stats in mastery.items():
                if is_topic_match(skill, mastered_topic):
                    matched_stats = stats
                    break
                    
            if matched_stats:
                scores.append(matched_stats.get("average_score", 50.0))
                tested_count += 1
            else:
                claimed = False
                resume_skills = extracted_resume.get("skills", [])
                for r_skill in resume_skills:
                    if skill.lower() in r_skill.lower() or r_skill.lower() in skill.lower():
                        claimed = True
                        break
                if claimed:
                    scores.append(65.0)
                    claimed_untested_count += 1
                else:
                    scores.append(50.0)
                    untested_gaps_count += 1
                    
        avg_readiness = sum(scores) / len(scores) if scores else 50.0
        
        if len(required_skills) > 0 and tested_count / len(required_skills) < 0.3:
            confidence = "low"
        elif len(required_skills) > 0 and tested_count / len(required_skills) < 0.7:
            confidence = "medium"
        else:
            confidence = "high"
            
        rationale = (
            f"Candidate has an estimated readiness of {avg_readiness:.1f}%. Out of {len(required_skills)} required skills, "
            f"{tested_count} have been tested in mock interviews, and {claimed_untested_count} are claimed on the resume but untested."
        )
        
        job_readiness = {
            "estimated_readiness_score": int(avg_readiness),
            "confidence_level": confidence,
            "match_rationale": rationale
        }
    else:
        job_readiness = {
            "estimated_readiness_score": 70,
            "confidence_level": "medium",
            "match_rationale": "General candidate profile matching."
        }
        
    return {
        "extracted_resume": extracted_resume,
        "extracted_jd": extracted_jd,
        "gap_analysis": gap_analysis,
        "interview_objectives": interview_objectives,
        "job_readiness": job_readiness
    }


# --- Route Endpoints ---
@router.post("/parse-file")
async def parse_uploaded_file(file: UploadFile = File(...)):
    """
    Accepts a PDF or TXT file upload, extracts its raw text, and returns it.
    """
    contents = await file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(contents)
        elif filename.endswith(".txt") or filename.endswith(".md"):
            text = extract_text_from_txt(contents)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a PDF or TXT file.")
            
        return {"filename": file.filename, "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-private-file")
async def parse_private_file(payload: ParsePrivateFilePayload, user_id: str = Depends(auth_service.require_auth)):
    """
    Downloads a private PDF or TXT resume from Supabase Storage using a temporary signed URL,
    extracts its raw text, and returns it.
    """
    signed_url = auth_service.get_resume_signed_url(payload.resume_path)
    if not signed_url:
        raise HTTPException(status_code=400, detail="Could not generate signed URL for resume path")
        
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(signed_url)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to download file from storage: {resp.text}")
            contents = resp.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch file from storage: {str(e)}")
        
    filename = payload.resume_path.lower()
    try:
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(contents)
        elif filename.endswith(".txt") or filename.endswith(".md"):
            text = extract_text_from_txt(contents)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format in storage")
            
        return {"filename": os.path.basename(payload.resume_path), "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from app.subscriptions.middleware import check_subscription

@router.post("/prepare-interview")
async def prepare_interview(payload: PrepareInterviewCreate, db: Session = Depends(get_session), user_id: str = Depends(check_subscription)):
    if not isinstance(user_id, str):
        user_id = "default"
    """
    Consolidated product endpoint that executes:
    CandidateProfile -> JobProfile -> GapAnalysis -> CompanyProfile -> InterviewBlueprint
    and creates the session DB row.
    """
    print("[prepare-interview] request received")
    from app.services.profile_service import build_candidate_profile, build_job_profile, build_gap_analysis, get_company_profile
    from app.agents.interview_planner import build_interview_blueprint
    interview_timeout_seconds = int(os.getenv("INTERVIEW_AGENT_TIMEOUT_SECONDS", "45"))
    
    # 1. Generate profiles in parallel
    print("[prepare-interview] building candidate and job profiles")
    cand_task = build_candidate_profile(payload.resume_text) if payload.resume_text else None
    job_task = build_job_profile(payload.jd_text) if payload.jd_text else None
    
    if cand_task and job_task:
        cand_prof, job_prof = await asyncio.gather(cand_task, job_task)
    else:
        cand_prof = await cand_task if cand_task else CandidateProfile()
        job_prof = await job_task if job_task else JobProfile()
        
    # 2. Run Gap Analysis
    print("[prepare-interview] running gap analysis")
    gap = await build_gap_analysis(cand_prof, job_prof)
    
    # 3. Fetch Company Profile
    print("[prepare-interview] loading company profile")
    company_prof = get_company_profile(payload.company_name or "Target Company")
    
    # 4. Build Blueprint
    print("[prepare-interview] building blueprint")
    blueprint = await asyncio.to_thread(
        build_interview_blueprint,
        payload.mode or "quick",
        payload.role,
        payload.difficulty,
        payload.duration_minutes,
        company_prof,
        cand_prof,
        job_prof,
        gap,
    )
    
    # 5. Save everything in Interview database row
    max_q = get_max_questions(payload.duration_minutes)
    
    # Prepare objectives list merged with gap/blueprint
    from app.routers.interview import merge_gap_objectives
    interview_objectives = merge_gap_objectives(blueprint.interview_objectives, gap.model_dump())
    
    knowledge_model = {
        "proven_skills": cand_prof.skills,
        "weak_skills": gap.weak_areas,
        "claims": [{
            "claim": c["title"],
            "state": "UNVERIFIED",
            "project": c["title"],
            "required_evidence": ["architecture", "implementation"],
            "verified_evidence": [],
            "attempts": 0,
            "evidence_coverage": {
                "architecture": "Missing",
                "implementation": "Missing",
                "tradeoffs": "Missing",
                "debugging": "Missing",
                "scaling": "Missing"
            },
            "supporting_turns": [],
            "confidence": 0
        } for c in cand_prof.projects],
        "unproven_claims": [{"claim": c["title"], "state": "UNVERIFIED", "project": c["title"]} for c in cand_prof.projects],
        "understanding_styles": []
    }
    
    # Initialize project investigation targets with budgets
    project_investigation = {
        "in_mode": False,
        "project_name": None,
        "probed_categories": [],
        "turns_spent": 0,
        "verification_plan": {p: False for p in blueprint.project_targets}
    }

    # Generate first question
    print("[prepare-interview] generating initial interviewer turn")
    initial_state = {
        "messages": [],
        "role": payload.role,
        "difficulty": payload.difficulty,
        "duration_minutes": payload.duration_minutes,
        "question_count": 0,
        "max_question_count": max_q,
        "status": "in_progress",
        "current_question": "",
        "covered_topics": [],
        "missing_topics": list(blueprint.topic_tree.keys()),
        "score_history": [],
        "personalization_context": gap.model_dump(),
        "company_name": company_prof.company_name,
        "topic_tree": blueprint.topic_tree,
        "knowledge_model": knowledge_model,
        "concept_coverage": blueprint.concept_coverage,
        "project_investigation": project_investigation,
        "interview_objectives": interview_objectives,
        "last_question_concepts": []
    }

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(interview_agent.invoke, initial_state),
            timeout=interview_timeout_seconds,
        )
        first_question = result.get("current_question", "Welcome to your mock technical interview. Let's begin.")
        primary_topic = result.get("primary_topic", "Introduction")
        topic_tree = result.get("topic_tree", blueprint.topic_tree)
        knowledge_model = result.get("knowledge_model", knowledge_model)
        concept_coverage = result.get("concept_coverage", blueprint.concept_coverage)
        project_investigation = result.get("project_investigation", project_investigation)
        interview_objectives = result.get("interview_objectives", interview_objectives)
        last_question_concepts = result.get("last_question_concepts", ["Self-introduction", "Project background"])
        interview_phase = result.get("interview_phase", "INTRODUCTION")
        debug_dashboard = result.get("debug_dashboard", {})
    except Exception as e:
        print(f"Agent initial turn failed in prepare_interview: {e}")
        fallback = build_contextual_fallback_question(
            role=payload.role,
            interview_objectives=interview_objectives,
            gap_analysis=gap.model_dump(),
            missing_topics=list(blueprint.topic_tree.keys()),
            knowledge_model=knowledge_model,
            is_opening=True
        )
        first_question = fallback["question"]
        primary_topic = fallback["topic"]
        last_question_concepts = fallback["expected_concepts"]
        interview_phase = "INTRODUCTION"
        debug_dashboard = {}

    interview = Interview(
        user_id=user_id,
        resume_path=payload.resume_path,
        role=payload.role,
        difficulty=payload.difficulty,
        duration_minutes=payload.duration_minutes,
        max_question_count=max_q,
        question_count=1,
        status="in_progress",
        mode=payload.mode or "quick",
        focus_topics_json=None,
        resume_text=payload.resume_text,
        jd_text=payload.jd_text,
        gap_analysis_json=gap.model_dump_json(),
        company_name=company_prof.company_name,
        topic_tree_json=json.dumps(topic_tree),
        knowledge_model_json=json.dumps(knowledge_model),
        concept_coverage_json=json.dumps(concept_coverage),
        project_investigation_json=json.dumps(project_investigation),
        interview_objectives_json=json.dumps(interview_objectives),
        interview_phase=interview_phase,
        current_question=first_question,
        debug_dashboard_json=json.dumps(debug_dashboard),
        candidate_profile_json=cand_prof.model_dump_json(),
        job_profile_json=job_prof.model_dump_json(),
        company_profile_json=company_prof.model_dump_json(),
        blueprint_json=blueprint.model_dump_json()
    )
    
    db.add(interview)
    db.commit()
    db.refresh(interview)
    log_structured_event("Interview Started", {
        "interview_id": interview.id,
        "role": interview.role,
        "difficulty": interview.difficulty,
        "max_question_count": max_q
    })

    # Save interviewer's first question transcript
    transcript = Transcript(
        interview_id=interview.id,
        sender="interviewer",
        text=first_question,
        topic=primary_topic,
        difficulty=interview.difficulty,
        secondary_topics_json=json.dumps(last_question_concepts)
    )
    db.add(transcript)
    db.commit()
    
    return {
        "id": interview.id,
        "ready": True,
        "role": interview.role,
        "difficulty": interview.difficulty,
        "company_name": interview.company_name,
        "max_question_count": interview.max_question_count,
        "blueprint": blueprint.model_dump()
    }


@router.post("", response_model=InterviewRead)
def create_interview(payload: InterviewCreate, db: Session = Depends(get_session), user_id: str = Depends(auth_service.require_auth)):
    if not isinstance(user_id, str):
        user_id = "default"
    max_q = get_max_questions(payload.duration_minutes)
    
    focus_json = None
    if payload.focus_topics:
        focus_json = json.dumps(payload.focus_topics)
        
    # Generate gap analysis if resume or JD is uploaded
    gap_analysis = None
    gap_analysis_json = None
    if payload.resume_text or payload.jd_text:
        try:
            gap_analysis = generate_gap_analysis(payload.resume_text, payload.jd_text, db, user_id)
            gap_analysis_json = json.dumps(gap_analysis)
        except Exception as e:
            print(f"Failed to generate gap analysis: {e}")
            
    from app.agents.interview_planner import generate_interview_plan
    plan = generate_interview_plan(
        mode=payload.mode or "quick",
        company=payload.company_name or "Target Company",
        role=payload.role,
        resume_text=payload.resume_text,
        jd_text=payload.jd_text
    )
    topic_tree = plan["topic_tree"]
    concept_coverage = plan["concept_coverage"]
    interview_objectives = merge_gap_objectives(plan["interview_objectives"], gap_analysis)
    
    knowledge_model = {
        "proven_skills": [],
        "weak_skills": [],
        "claims": [],
        "unproven_claims": [],
        "understanding_styles": []
    }
    
    project_investigation = {
        "in_mode": False,
        "project_name": None,
        "probed_categories": [],
        "turns_spent": 0
    }

    # Create interview session
    interview = Interview(
        user_id=user_id,
        resume_path=payload.resume_path,
        role=payload.role,
        difficulty=payload.difficulty,
        duration_minutes=payload.duration_minutes,
        max_question_count=max_q,
        question_count=0,
        status="in_progress",
        mode=payload.mode or "quick",
        focus_topics_json=focus_json,
        resume_text=payload.resume_text,
        jd_text=payload.jd_text,
        gap_analysis_json=gap_analysis_json,
        company_name=payload.company_name,
        topic_tree_json=json.dumps(topic_tree),
        knowledge_model_json=json.dumps(knowledge_model),
        concept_coverage_json=json.dumps(concept_coverage),
        project_investigation_json=json.dumps(project_investigation),
        interview_objectives_json=json.dumps(interview_objectives)
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    log_structured_event("Interview Started", {
        "interview_id": interview.id,
        "role": interview.role,
        "difficulty": interview.difficulty,
        "max_question_count": max_q
    })
    
    profile = ROLE_PROFILES.get(interview.role, ROLE_PROFILES["AI Engineer"])
    
    if getattr(interview, "mode", "quick") == "re-interview" and getattr(interview, "focus_topics_json", None):
        try:
            all_topics = json.loads(interview.focus_topics_json)
        except Exception:
            all_topics = profile.get("topics", [])
    else:
        # If personalized gap analysis is present, target required/missing skills
        if gap_analysis:
            jd_skills = gap_analysis.get("extracted_jd", {}).get("required_skills", [])
            missing_skills = gap_analysis.get("gap_analysis", {}).get("missing_skills", [])
            personalized_topics = list(set([s for s in jd_skills + missing_skills if s]))
            if personalized_topics:
                all_topics = personalized_topics
            else:
                all_topics = profile.get("topics", [])
        else:
            all_topics = profile.get("topics", [])
        
    # Generate first question
    initial_state = {
        "messages": [],
        "role": interview.role,
        "difficulty": interview.difficulty,
        "duration_minutes": interview.duration_minutes,
        "question_count": 0,
        "max_question_count": interview.max_question_count,
        "status": "in_progress",
        "current_question": "",
        "covered_topics": [],
        "missing_topics": all_topics,
        "score_history": [],
        "personalization_context": gap_analysis,
        "company_name": interview.company_name,
        "topic_tree": topic_tree,
        "knowledge_model": knowledge_model,
        "concept_coverage": concept_coverage,
        "project_investigation": project_investigation,
        "interview_objectives": interview_objectives,
        "last_question_concepts": []
    }

    try:
        result = interview_agent.invoke(initial_state)
        first_question = result.get("current_question", "Hello! Welcome to your interview. Let's begin.")
        primary_topic = result.get("primary_topic", "Introduction")
        topic_tree = result.get("topic_tree", topic_tree)
        knowledge_model = result.get("knowledge_model", knowledge_model)
        concept_coverage = result.get("concept_coverage", concept_coverage)
        project_investigation = result.get("project_investigation", project_investigation)
        interview_objectives = result.get("interview_objectives", interview_objectives)
        last_question_concepts = result.get("last_question_concepts", ["Self-introduction", "Project background"])
        interview_phase = result.get("interview_phase", "INTRODUCTION")
        debug_dashboard = result.get("debug_dashboard", {})
    except Exception as e:
        print(f"Agent initial turn failed: {e}")
        fallback = build_contextual_fallback_question(
            role=interview.role,
            interview_objectives=interview_objectives,
            gap_analysis=gap_analysis,
            missing_topics=all_topics,
            knowledge_model=knowledge_model,
            is_opening=True
        )
        first_question = fallback["question"]
        primary_topic = fallback["topic"]
        last_question_concepts = fallback["expected_concepts"]
        interview_phase = "INTRODUCTION"
        debug_dashboard = {}
    
    # Save interviewer's first question
    transcript = Transcript(
        interview_id=interview.id,
        sender="interviewer",
        text=first_question,
        topic=primary_topic,
        difficulty=interview.difficulty
    )
    db.add(transcript)
    
    # Update interview state
    interview.current_question = first_question
    interview.question_count = 1
    interview.topic_tree_json = json.dumps(topic_tree)
    interview.knowledge_model_json = json.dumps(knowledge_model)
    interview.concept_coverage_json = json.dumps(concept_coverage)
    interview.project_investigation_json = json.dumps(project_investigation)
    interview.interview_objectives_json = json.dumps(interview_objectives)
    interview.interview_phase = interview_phase
    interview.debug_dashboard_json = json.dumps(debug_dashboard)
    
    # Save expected concepts context on the transcript metadata as secondary_topics_json (optional helper)
    transcript.secondary_topics_json = json.dumps(last_question_concepts)
    db.add(transcript)
    
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    return interview

@router.get("", response_model=List[InterviewRead])
def list_interviews(user_id: str = Depends(auth_service.require_auth), db: Session = Depends(get_session)):
    if not isinstance(user_id, str):
        user_id = "default"
    statement = select(Interview).where(Interview.user_id == user_id).order_by(Interview.created_at.desc())
    results = db.exec(statement).all()
    return results

@router.get("/debug/config-status")
def get_debug_config():
    from app.config import SUPABASE_URL, SUPABASE_ANON_KEY
    return {
        "supabase_url": SUPABASE_URL,
        "supabase_key_length": len(SUPABASE_ANON_KEY) if SUPABASE_ANON_KEY else 0,
        "supabase_key_is_placeholder": SUPABASE_ANON_KEY == "your_supabase_anon_key_here",
        "client_initialized": auth_service.client is not None,
        "is_testing": auth_service.IS_TESTING
    }

@router.get("/{id}", response_model=InterviewDetailRead)
def get_interview(id: str, user_id: str = Depends(auth_service.require_auth), db: Session = Depends(get_session)):
    if not isinstance(user_id, str):
        user_id = "default"
    interview = db.get(Interview, id)
    if not interview or interview.user_id != user_id:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    
    # Sort transcripts chronologically
    sorted_transcripts = sorted(interview.transcripts, key=lambda t: t.timestamp)
    
    transcripts_read = []
    for t in sorted_transcripts:
        secondary = []
        if t.secondary_topics_json:
            try:
                secondary = json.loads(t.secondary_topics_json)
            except:
                pass
        transcripts_read.append(
            TranscriptRead(
                sender=t.sender,
                text=t.text,
                timestamp=t.timestamp,
                topic=t.topic,
                score=t.score,
                reasoning_summary=t.reasoning_summary,
                secondary_topics=secondary,
                difficulty=t.difficulty,
                audio_url=t.audio_url
            )
        )
    
    return InterviewDetailRead(
        id=interview.id,
        role=interview.role,
        difficulty=interview.difficulty,
        duration_minutes=interview.duration_minutes,
        max_question_count=interview.max_question_count,
        question_count=interview.question_count,
        status=interview.status,
        mode=interview.mode or "quick",
        focus_topics_json=interview.focus_topics_json,
        resume_text=interview.resume_text,
        jd_text=interview.jd_text,
        gap_analysis_json=interview.gap_analysis_json,
        company_name=interview.company_name,
        topic_tree_json=interview.topic_tree_json,
        knowledge_model_json=interview.knowledge_model_json,
        concept_coverage_json=interview.concept_coverage_json,
        project_investigation_json=interview.project_investigation_json,
        interview_objectives_json=interview.interview_objectives_json,
        interview_phase=interview.interview_phase,
        debug_dashboard_json=interview.debug_dashboard_json,
        created_at=interview.created_at,
        ended_at=interview.ended_at,
        transcripts=transcripts_read
    )

@router.post("/{id}/end", response_model=InterviewRead)
def end_interview(id: str, user_id: str = Depends(auth_service.require_auth), db: Session = Depends(get_session)):
    if not isinstance(user_id, str):
        user_id = "default"
    """
    Manually ends the interview and triggers evaluation report generation.
    """
    interview = db.get(Interview, id)
    if not interview or interview.user_id != user_id:
        raise HTTPException(status_code=404, detail="Interview session not found.")
        
    if interview.status != "completed":
        interview.status = "completed"
        interview.ended_at = datetime.utcnow()
        db.add(interview)
        db.commit()
        db.refresh(interview)
        
        # Increment usage completed
        from app.subscriptions.service import increment_interview_usage
        try:
            increment_interview_usage(interview.user_id, db)
        except Exception as u_err:
            print(f"[ERROR] Failed to increment interview usage: {u_err}")
        
    try:
        # Generate the report immediately
        compute_evaluation_report(id, db)
    except Exception as e:
        print(f"Failed to generate report during manual end: {e}")
        
    return interview

@router.get("/reports/{interview_id}", response_model=EvaluationReportRead)
def get_evaluation_report(interview_id: str, user_id: str = Depends(auth_service.require_auth), db: Session = Depends(get_session)):
    if not isinstance(user_id, str):
        user_id = "default"
    """
    Fetches the evaluation report card for the given session.
    Generates it on-demand if the interview is completed but no report exists.
    """
    interview = db.get(Interview, interview_id)
    if not interview or interview.user_id != user_id:
        raise HTTPException(status_code=404, detail="Interview session not found.")
        
    report = db.exec(
        select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
    ).first()
    
    if not report:
        if interview.status != "completed":
            raise HTTPException(status_code=400, detail="Cannot evaluate an in-progress interview.")
        try:
            report = compute_evaluation_report(interview_id, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate evaluation report: {str(e)}")
            
    # Deserialize JSON fields
    try:
        strengths = json.loads(report.strengths_json)
    except:
        strengths = []
        
    try:
        weaknesses = json.loads(report.categorized_weaknesses_json)
    except:
        weaknesses = {}
        
    try:
        topics = json.loads(report.topic_performance_json)
    except:
        topics = {}
        
    # Extract new fields from raw_json
    raw_data = {}
    if report.raw_json:
        try:
            raw_data = json.loads(report.raw_json)
        except:
            pass
        
    return EvaluationReportRead(
        id=report.id,
        interview_id=report.interview_id,
        overall_score=report.overall_score,
        technical_score=report.technical_score,
        communication_score=report.communication_score,
        explanation_score=report.explanation_score,
        problem_solving_score=report.problem_solving_score,
        behavioral_score=report.behavioral_score,
        summary=report.summary,
        strengths=strengths,
        categorized_weaknesses=weaknesses,
        topic_performance=topics,
        evaluation_version=report.evaluation_version,
        created_at=report.created_at,
        ownership_score=raw_data.get("ownership_score"),
        interview_completion_score=raw_data.get("interview_completion_score"),
        evaluation_evidence=raw_data.get("evaluation_evidence"),
        claim_verification_summary=raw_data.get("claim_verification_summary"),
        learning_plan=raw_data.get("learning_plan"),
        recommendations=raw_data.get("recommendations"),
        hire_recommendation=raw_data.get("hire_recommendation"),
        confidence_level=raw_data.get("confidence_level")
    )


# --- Profile Endpoints ---
@router.get("/profile/card", response_model=UserProfileRead)
def get_user_profile(db: Session = Depends(get_session), user_id: str = Depends(auth_service.require_auth)):
    if not isinstance(user_id, str):
        user_id = "default"
    """
    Fetches the User Knowledge Graph profile for the default candidate.
    Generates an empty default profile if none exists.
    """
    profile = db.exec(select(UserProfile).where(UserProfile.user_id == user_id)).first()
    
    if not profile:
        from app.agents.memory_agent import update_user_profile
        profile = update_user_profile(db, user_id)
        
    try:
        mastery = json.loads(profile.topic_mastery_json)
    except:
        mastery = {}
        
    try:
        readiness = json.loads(profile.readiness_scores_json)
    except:
        readiness = {}
        
    try:
        performance = json.loads(profile.role_performance_json)
    except:
        performance = {}
        
    try:
        trends = json.loads(profile.history_trends_json)
    except:
        trends = []
        
    try:
        recs = json.loads(profile.recommendations_json)
    except:
        recs = []
        
    return UserProfileRead(
        user_id=profile.user_id,
        topic_mastery=mastery,
        readiness_scores=readiness,
        role_performance=performance,
        history_trends=trends,
        recommendations=recs,
        last_updated=profile.last_updated
    )

@router.post("/profile/reset")
def reset_profile(db: Session = Depends(get_session), user_id: str = Depends(auth_service.require_auth)):
    if not isinstance(user_id, str):
        user_id = "default"
    """
    Deletes all previous interview sessions, transcripts, reports, user profiles, and study plans.
    Allows developers to easily verify fresh profile constructions.
    """
    # Delete interviews (which cascades delete transcripts and reports)
    interviews = db.exec(select(Interview).where(Interview.user_id == user_id)).all()
    for i in interviews:
        db.delete(i)
        
    # Delete profiles
    profiles = db.exec(select(UserProfile).where(UserProfile.user_id == user_id)).all()
    for p in profiles:
        db.delete(p)
        
    # Delete study plans
    study_plans = db.exec(select(StudyPlan).where(StudyPlan.user_id == user_id)).all()
    for s in study_plans:
        db.delete(s)
        
    db.commit()
    return {"message": "All mock data, transcripts, scorecards, study plans, and knowledge graphs cleared successfully for this user."}


@router.get("/study-plans/latest", response_model=StudyPlanRead)
def get_latest_study_plan(db: Session = Depends(get_session), user_id: str = Depends(auth_service.require_auth)):
    if not isinstance(user_id, str):
        user_id = "default"
    """
    Fetches the active study plan generated for the candidate.
    """
    plan = db.exec(
        select(StudyPlan).where(
            StudyPlan.user_id == user_id,
            StudyPlan.status == "active"
        ).order_by(StudyPlan.created_at.desc())
    ).first()
    
    if not plan:
        # Generate default profile and study plan on-the-fly if missing
        profile = db.exec(select(UserProfile).where(UserProfile.user_id == user_id)).first()
        if not profile:
            from app.agents.memory_agent import update_user_profile
            profile = update_user_profile(db, user_id)
        from app.agents.planning_agent import generate_study_plan
        plan = generate_study_plan(db, profile)
        
    try:
        roadmap = json.loads(plan.roadmap_json)
    except:
        roadmap = []
        
    try:
        resources = json.loads(plan.recommended_resources_json)
    except:
        resources = []
        
    try:
        questions = json.loads(plan.practice_questions_json)
    except:
        questions = []
        
    return StudyPlanRead(
        id=plan.id,
        user_id=plan.user_id,
        associated_interview_id=plan.associated_interview_id,
        roadmap=roadmap,
        recommended_resources=resources,
        practice_questions=questions,
        status=plan.status,
        created_at=plan.created_at
    )


@router.get("/study-plans/{id}", response_model=StudyPlanRead)
def get_study_plan(id: str, db: Session = Depends(get_session), user_id: str = Depends(auth_service.require_auth)):
    if not isinstance(user_id, str):
        user_id = "default"
    """
    Fetches a specific historical study plan.
    """
    plan = db.get(StudyPlan, id)
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=404, detail="Study plan not found.")
        
    try:
        roadmap = json.loads(plan.roadmap_json)
    except:
        roadmap = []
        
    try:
        resources = json.loads(plan.recommended_resources_json)
    except:
        resources = []
        
    try:
        questions = json.loads(plan.practice_questions_json)
    except:
        questions = []
        
    return StudyPlanRead(
        id=plan.id,
        user_id=plan.user_id,
        associated_interview_id=plan.associated_interview_id,
        roadmap=roadmap,
        recommended_resources=resources,
        practice_questions=questions,
        status=plan.status,
        created_at=plan.created_at
    )


@router.post("/study-plans/{id}/re-interview", response_model=InterviewRead)
def trigger_re_interview(id: str, db: Session = Depends(get_session), user_id: str = Depends(auth_service.require_auth)):
    if not isinstance(user_id, str):
        user_id = "default"
    """
    Creates a new mock interview session focusing on study plan weaknesses,
    dynamically choosing duration (10 min vs 20 min) based on weakness severity.
    """
    plan = db.get(StudyPlan, id)
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=404, detail="Study plan not found.")
        
    profile = db.exec(select(UserProfile).where(UserProfile.user_id == plan.user_id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
        
    try:
        mastery = json.loads(profile.topic_mastery_json)
    except:
        mastery = {}
        
    weak_count = 0
    major_severity = False
    focus_topics = []
    
    # 1. Gather weak concepts from roadmap
    try:
        roadmap = json.loads(plan.roadmap_json)
        for milestone in roadmap:
            concept = milestone.get("concept")
            if concept and concept not in focus_topics:
                focus_topics.append(concept)
    except:
        pass
        
    if not focus_topics:
        # Fallback to UserProfile mastery mapping
        for topic, stats in mastery.items():
            if stats.get("mastery_state") in ["Weak", "Improving"]:
                focus_topics.append(topic)
                
    # 2. Check weakness severity
    for topic in focus_topics:
        stats = mastery.get(topic, {})
        avg_score = stats.get("average_score", 50)
        state = stats.get("mastery_state", "Weak")
        
        if state == "Weak":
            weak_count += 1
            if avg_score < 60:
                major_severity = True
                
    if weak_count >= 3:
        major_severity = True
        
    # 3. Dynamic session configuration
    if major_severity:
        duration = 20
        max_q = 6
    else:
        duration = 10
        max_q = 3
        
    from app.agents.interview_planner import generate_interview_plan
    plan = generate_interview_plan(
        mode="re-interview",
        company="Target Company",
        role="AI Engineer"
    )
    topic_tree = plan["topic_tree"]
    concept_coverage = plan["concept_coverage"]
    interview_objectives = build_reinterview_objectives(focus_topics, plan["interview_objectives"])
    
    knowledge_model = {
        "proven_skills": [],
        "weak_skills": [],
        "claims": [],
        "unproven_claims": [],
        "understanding_styles": []
    }
    
    project_investigation = {
        "in_mode": False,
        "project_name": None,
        "probed_categories": [],
        "turns_spent": 0
    }

    new_interview = Interview(
        user_id=user_id,
        role="AI Engineer",
        difficulty="medium",
        duration_minutes=duration,
        max_question_count=max_q,
        question_count=0,
        status="in_progress",
        mode="re-interview",
        focus_topics_json=json.dumps(focus_topics),
        company_name="Target Company",
        topic_tree_json=json.dumps(topic_tree),
        knowledge_model_json=json.dumps(knowledge_model),
        concept_coverage_json=json.dumps(concept_coverage),
        project_investigation_json=json.dumps(project_investigation),
        interview_objectives_json=json.dumps(interview_objectives)
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)
    
    # 4. Generate first question from focus topics
    initial_state = {
        "messages": [],
        "role": new_interview.role,
        "difficulty": new_interview.difficulty,
        "duration_minutes": new_interview.duration_minutes,
        "question_count": 0,
        "max_question_count": new_interview.max_question_count,
        "status": "in_progress",
        "current_question": "",
        "covered_topics": [],
        "missing_topics": focus_topics if focus_topics else ["Machine Learning"],
        "score_history": [],
        "company_name": "Target Company",
        "topic_tree": topic_tree,
        "knowledge_model": knowledge_model,
        "concept_coverage": concept_coverage,
        "project_investigation": project_investigation,
        "interview_objectives": interview_objectives,
        "last_question_concepts": []
    }
    
    try:
        result = interview_agent.invoke(initial_state)
        first_question = result.get("current_question", "Welcome back! Let's start the follow-up review.")
        primary_topic = result.get("primary_topic", focus_topics[0] if focus_topics else "General")
        topic_tree = result.get("topic_tree", topic_tree)
        knowledge_model = result.get("knowledge_model", knowledge_model)
        concept_coverage = result.get("concept_coverage", concept_coverage)
        project_investigation = result.get("project_investigation", project_investigation)
        interview_objectives = result.get("interview_objectives", interview_objectives)
        last_question_concepts = result.get("last_question_concepts", ["Self-introduction", "Project background"])
        interview_phase = result.get("interview_phase", "INTRODUCTION")
        debug_dashboard = result.get("debug_dashboard", {})
    except Exception as e:
        print(f"Re-interview initial question generation failed: {e}")
        fallback = build_contextual_fallback_question(
            role=new_interview.role,
            interview_objectives=interview_objectives,
            missing_topics=focus_topics,
            knowledge_model=knowledge_model,
            is_opening=True
        )
        first_question = fallback["question"]
        primary_topic = fallback["topic"]
        last_question_concepts = fallback["expected_concepts"]
        interview_phase = "INTRODUCTION"
        debug_dashboard = {}
        
    # Save transcript
    transcript = Transcript(
        interview_id=new_interview.id,
        sender="interviewer",
        text=first_question,
        topic=primary_topic,
        difficulty=new_interview.difficulty,
        secondary_topics_json=json.dumps(last_question_concepts)
    )
    db.add(transcript)
    
    new_interview.current_question = first_question
    new_interview.question_count = 1
    new_interview.topic_tree_json = json.dumps(topic_tree)
    new_interview.knowledge_model_json = json.dumps(knowledge_model)
    new_interview.concept_coverage_json = json.dumps(concept_coverage)
    new_interview.project_investigation_json = json.dumps(project_investigation)
    new_interview.interview_objectives_json = json.dumps(interview_objectives)
    new_interview.interview_phase = interview_phase
    new_interview.debug_dashboard_json = json.dumps(debug_dashboard)
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)
    
    return new_interview


@router.get("/debug/cache-metrics")
def get_cache_metrics():
    """
    Exposes L1 computation cache metrics for performance debugging.
    """
    from app.services.cache import comp_cache
    return comp_cache.collect_metrics()


@router.get("/profile/coaching", response_model=CoachingRecommendationsRead)
def get_coaching_recommendations(db: Session = Depends(get_session), user_id: str = Depends(auth_service.require_auth)):
    if not isinstance(user_id, str):
        user_id = "default"
    """
    Returns unified coaching dashboard recommendations combining Memory and Planning Agent data.
    """
    profile = db.exec(select(UserProfile).where(UserProfile.user_id == user_id)).first()
    if not profile:
        from app.agents.memory_agent import update_user_profile
        profile = update_user_profile(db, user_id)
        
    plan = db.exec(
        select(StudyPlan).where(
            StudyPlan.user_id == user_id,
            StudyPlan.status == "active"
        ).order_by(StudyPlan.created_at.desc())
    ).first()
    
    # 1. Format study_next
    study_next_read = None
    if plan:
        try:
            roadmap = json.loads(plan.roadmap_json)
            resources = json.loads(plan.recommended_resources_json)
            questions = json.loads(plan.practice_questions_json)
            study_next_read = StudyPlanRead(
                id=plan.id,
                user_id=plan.user_id,
                associated_interview_id=plan.associated_interview_id,
                roadmap=roadmap,
                recommended_resources=resources,
                practice_questions=questions,
                status=plan.status,
                created_at=plan.created_at
            )
        except Exception as e:
            print(f"Error parsing latest plan: {e}")
            
    # 2. Format next_interview suggestions
    next_interview = None
    try:
        recs = json.loads(profile.recommendations_json)
        if recs:
            targeted = [r for r in recs if r.get("type") == "targeted_practice"]
            source = targeted[0] if targeted else recs[0]
            next_interview = {
                "role": source.get("role", "AI Engineer"),
                "difficulty": "medium",
                "mode": "re-interview",
                "focus_topics": source.get("focus_topics", []),
                "reason": source.get("reason", "")
            }
    except Exception as e:
        print(f"Error parsing recommendations: {e}")
        
    if not next_interview:
        next_interview = {
            "role": "AI Engineer",
            "difficulty": "medium",
            "mode": "quick",
            "focus_topics": ["Machine Learning"],
            "reason": "Complete a general interview to build your profile."
        }
        
    # 3. Calculate impactful weaknesses
    impactful_weaknesses = []
    try:
        mastery = json.loads(profile.topic_mastery_json)
        target_role = "AI Engineer"
        try:
            performance = json.loads(profile.role_performance_json)
            if performance:
                sorted_roles = sorted(performance.items(), key=lambda x: x[1].get("attempts", 0), reverse=True)
                if sorted_roles:
                    target_role = sorted_roles[0][0]
        except:
            pass
            
        role_profile = ROLE_PROFILES.get(target_role, ROLE_PROFILES["AI Engineer"])
        core_topics = role_profile.get("topics", [])
        
        for topic in core_topics:
            from app.agents.memory_agent import is_topic_match
            matched_stats = None
            for mastered_topic, stats in mastery.items():
                if is_topic_match(topic, mastered_topic):
                    matched_stats = stats
                    break
                    
            if matched_stats:
                avg_score = matched_stats.get("average_score", 50.0)
                state = matched_stats.get("mastery_state", "Weak")
                if state in ["Weak", "Improving"]:
                    impact = round(100.0 - avg_score, 1)
                    impactful_weaknesses.append({
                        "topic": topic,
                        "average_score": avg_score,
                        "mastery_state": state,
                        "readiness_impact": impact
                    })
            else:
                impactful_weaknesses.append({
                    "topic": topic,
                    "average_score": 50.0,
                    "mastery_state": "Weak",
                    "readiness_impact": 50.0
                })
                
        impactful_weaknesses.sort(key=lambda x: x["readiness_impact"], reverse=True)
    except Exception as e:
        print(f"Error computing impactful weaknesses: {e}")
        
    return CoachingRecommendationsRead(
        study_next=study_next_read,
        next_interview=next_interview,
        impactful_weaknesses=impactful_weaknesses
    )



def run_report_in_background(interview_id: str):
    import threading
    import time
    from app.database import engine
    from sqlmodel import Session
    
    def worker():
        # Allow the main WS response turn to complete sending first
        time.sleep(0.5)
        with Session(engine) as db:
            try:
                print(f"[BACKGROUND] Generating evaluation report for session {interview_id}...")
                compute_evaluation_report(interview_id, db)
                print(f"[BACKGROUND] Successfully completed evaluation report for session {interview_id}.")
            except Exception as e:
                print(f"[BACKGROUND ERROR] Failed to generate evaluation report: {e}")
                
    threading.Thread(target=worker, daemon=True).start()


# --- Shared Turn Processor ---
def process_interview_turn(id: str, candidate_text: str, session: Session, audio_url: Optional[str] = None) -> Dict[str, Any]:
    candidate_text = candidate_text.strip()
    if not candidate_text:
        raise ValueError("Candidate response cannot be empty.")
        
    interview = session.get(Interview, id)
    if not interview:
        raise ValueError("Interview session not found.")
        
    if interview.status == "completed":
        try:
            debug_dashboard = json.loads(interview.debug_dashboard_json or "{}")
        except:
            debug_dashboard = {}
        return {
            "sender": "interviewer",
            "text": interview.current_question or "Interview already completed.",
            "question_count": interview.question_count,
            "max_question_count": interview.max_question_count,
            "status": "completed",
            "interview_phase": interview.interview_phase,
            "debug_dashboard": debug_dashboard
        }
        
    current_difficulty = interview.difficulty
    
    # Save candidate response
    cand_transcript = Transcript(
        interview_id=interview.id,
        sender="candidate",
        text=candidate_text,
        difficulty=current_difficulty,
        audio_url=audio_url
    )
    session.add(cand_transcript)
    session.commit()
    session.refresh(cand_transcript)
    
    # Fetch transcripts to reconstruct state
    statement = select(Transcript).where(Transcript.interview_id == id).order_by(Transcript.timestamp.asc())
    transcripts_list = session.exec(statement).all()
    
    # Respect the user's initial selected difficulty and disable adaptive difficulty database updates
    new_difficulty = current_difficulty
    
    if new_difficulty != current_difficulty:
        interview.difficulty = new_difficulty
        session.add(interview)
        session.commit()
        session.refresh(interview)
        
    # Reconstruct covered topics and objectives list
    profile = ROLE_PROFILES.get(interview.role, ROLE_PROFILES["AI Engineer"])
    gap_analysis = None
    if getattr(interview, "mode", "quick") == "re-interview" and getattr(interview, "focus_topics_json", None):
        try:
            all_topics = json.loads(interview.focus_topics_json)
        except Exception:
            all_topics = profile.get("topics", [])
    else:
        # If gap analysis is present, target required/missing skills
        if interview.gap_analysis_json:
            try:
                gap_analysis = json.loads(interview.gap_analysis_json)
            except Exception:
                pass
        if gap_analysis:
            jd_skills = gap_analysis.get("extracted_jd", {}).get("required_skills", [])
            missing_skills = gap_analysis.get("gap_analysis", {}).get("missing_skills", [])
            personalized_topics = list(set([s for s in jd_skills + missing_skills if s]))
            if personalized_topics:
                all_topics = personalized_topics
            else:
                all_topics = profile.get("topics", [])
        elif interview.focus_topics_json:
            try:
                all_topics = json.loads(interview.focus_topics_json)
            except Exception:
                all_topics = profile.get("topics", [])
        else:
            all_topics = profile.get("topics", [])
            
    # Make sure gap_analysis is deserialized for personalization_context
    if not gap_analysis and interview.gap_analysis_json:
        try:
            gap_analysis = json.loads(interview.gap_analysis_json)
        except Exception:
            pass
            
    covered_set = set()
    for t in transcripts_list:
        if t.sender != "candidate":
            continue
        if t.topic:
            covered_set.add(t.topic)
        if t.secondary_topics_json:
            try:
                sec = json.loads(t.secondary_topics_json)
                for s in sec:
                    covered_set.add(s)
            except:
                pass
                
    covered_topics = list(covered_set)
    missing_topics = [t for t in all_topics if t not in covered_set]
    
    # Format message history
    langchain_messages = []
    for t in transcripts_list:
        if t.sender == "interviewer":
            langchain_messages.append(AIMessage(content=t.text))
        else:
            langchain_messages.append(HumanMessage(content=t.text))
            
    try:
        topic_tree = json.loads(interview.topic_tree_json or "{}")
    except:
        topic_tree = {}
    try:
        knowledge_model = json.loads(interview.knowledge_model_json or "{}")
    except:
        knowledge_model = {}
    try:
        concept_coverage = json.loads(interview.concept_coverage_json or "{}")
    except:
        concept_coverage = {}
    try:
        project_investigation = json.loads(interview.project_investigation_json or "{}")
    except:
        project_investigation = {}
    try:
        interview_objectives = json.loads(interview.interview_objectives_json or "{}")
    except:
        interview_objectives = {}
        
    current_phase = interview.interview_phase or "INTRODUCTION"
    try:
        debug_dashboard = json.loads(interview.debug_dashboard_json or "{}")
    except:
        debug_dashboard = {}
        
    # Load last expected concepts from the last interviewer transcript
    last_question_concepts = []
    for t in reversed(transcripts_list):
        if t.sender == "interviewer":
            if t.secondary_topics_json:
                try:
                    last_question_concepts = json.loads(t.secondary_topics_json)
                except:
                    pass
            break
    evaluated_scores = [t.score for t in transcripts_list if t.sender == "candidate" and t.score is not None]
    
    current_state = {
        "messages": langchain_messages,
        "role": interview.role,
        "difficulty": interview.difficulty,
        "duration_minutes": interview.duration_minutes,
        "question_count": interview.question_count,
        "max_question_count": interview.max_question_count,
        "status": interview.status,
        "current_question": interview.current_question,
        "covered_topics": covered_topics,
        "missing_topics": missing_topics,
        "score_history": evaluated_scores,
        "personalization_context": gap_analysis,
        "company_name": interview.company_name,
        "topic_tree": topic_tree,
        "knowledge_model": knowledge_model,
        "concept_coverage": concept_coverage,
        "project_investigation": project_investigation,
        "interview_objectives": interview_objectives,
        "last_question_concepts": last_question_concepts,
        "interview_phase": current_phase,
        "debug_dashboard": debug_dashboard
    }
    
    # Invoke Interview Agent
    import copy
    before_objectives = copy.deepcopy(interview_objectives)
    try:
        result = interview_agent.invoke(current_state)
        next_question = result.get("current_question", "")
        agent_status = result.get("status", "in_progress")
        agent_q_count = result.get("question_count", interview.question_count)
        
        eval_msg = result.get("evaluation", "")
        reasoning = result.get("reasoning_summary", "")
        score_val = result.get("score")
        primary_topic = result.get("primary_topic", "General")
        secondary_topics = result.get("secondary_topics", [])
        action = result.get("action", "transition")
        
        topic_tree = result.get("topic_tree", topic_tree)
        knowledge_model = result.get("knowledge_model", knowledge_model)
        concept_coverage = result.get("concept_coverage", concept_coverage)
        project_investigation = result.get("project_investigation", project_investigation)
        interview_objectives = result.get("interview_objectives", interview_objectives)
        next_expected_concepts = result.get("last_question_concepts", [])
        current_phase = result.get("interview_phase", current_phase)
        debug_dashboard = result.get("debug_dashboard", {})
    except Exception as e:
        print(f"Agent turn run failed: {e}")
        agent_q_count = interview.question_count + 1
        if agent_q_count >= interview.max_question_count:
              fallback = build_contextual_fallback_question(
                  role=interview.role,
                  is_wrap_up=True
              )
              next_question = fallback["question"]
              agent_status = "completed"
              action = "wrap_up"
              primary_topic = fallback["topic"]
              next_expected_concepts = fallback["expected_concepts"]
        else:
              fallback = build_contextual_fallback_question(
                  role=interview.role,
                  interview_objectives=interview_objectives,
                  gap_analysis=gap_analysis,
                  missing_topics=missing_topics,
                  knowledge_model=knowledge_model
              )
              next_question = fallback["question"]
              agent_status = "in_progress"
              action = "transition"
              primary_topic = fallback["topic"]
              next_expected_concepts = fallback["expected_concepts"]
              
        eval_msg = "N/A"
        reasoning = "Gemini Call Failed"
        score_val = 3
        secondary_topics = []
        
    # --- Strict Question Count Limit Check ---
    if interview.question_count >= interview.max_question_count:
        agent_status = "completed"
        next_question = "Thank you for completing the interview. I have gathered enough information to evaluate your performance. I am now generating your final evaluation report."
        agent_q_count = interview.max_question_count
        action = "wrap_up"
        next_expected_concepts = []
        current_phase = "WRAP_UP"

    # Calculate confidence gain for active objective
    confidence_gain = 0
    active_obj = current_state.get("active_objective") or (result.get("active_objective") if "result" in locals() else None)
    if active_obj:
        before_val = 0
        after_val = 0
        for sec in ["must_verify", "nice_to_verify"]:
            if "before_objectives" in locals() and before_objectives and sec in before_objectives and active_obj in before_objectives[sec]:
                val = before_objectives[sec][active_obj]
                before_val = val.get("confidence", 0) if isinstance(val, dict) else 0
            if interview_objectives and sec in interview_objectives and active_obj in interview_objectives[sec]:
                val = interview_objectives[sec][active_obj]
                after_val = val.get("confidence", 0) if isinstance(val, dict) else 0
        confidence_gain = max(0, after_val - before_val)

    # Generic turn metadata payload
    turn_metadata = {
        "objective": active_obj or "None",
        "claim": (result.get("debug_dashboard", {}).get("active_claim") or "None") if "result" in locals() else "None",
        "confidence_gain": confidence_gain,
        "evidence": result.get("evidence_categories_detected", {}) if "result" in locals() else {},
        "strategy": action if "action" in locals() else "transition",
        "phase": current_phase
    }

    # Persist turn metadata back to the candidate's transcript row
    cand_transcript.score = score_val
    cand_transcript.reasoning_summary = reasoning
    cand_transcript.topic = primary_topic
    cand_transcript.secondary_topics_json = json.dumps(secondary_topics)
    cand_transcript.turn_metadata_json = json.dumps(turn_metadata)
    session.add(cand_transcript)
    
    # Save interviewer question to transcripts
    int_transcript = Transcript(
        interview_id=interview.id,
        sender="interviewer",
        text=next_question,
        difficulty=interview.difficulty,
        topic="Wrap-up" if action == "wrap_up" else primary_topic,
        secondary_topics_json=json.dumps(next_expected_concepts)
    )
    session.add(int_transcript)
    
    # Update interview session record
    interview.current_question = next_question
    interview.question_count = agent_q_count
    interview.status = agent_status
    interview.topic_tree_json = json.dumps(topic_tree)
    interview.knowledge_model_json = json.dumps(knowledge_model)
    interview.concept_coverage_json = json.dumps(concept_coverage)
    interview.project_investigation_json = json.dumps(project_investigation)
    interview.interview_objectives_json = json.dumps(interview_objectives)
    interview.interview_phase = current_phase
    interview.debug_dashboard_json = json.dumps(debug_dashboard)
    if agent_status == "completed":
        interview.ended_at = datetime.utcnow()
        
    session.add(interview)
    session.commit()
    
    # Increment usage completed
    if agent_status == "completed":
        from app.subscriptions.service import increment_interview_usage
        try:
            increment_interview_usage(interview.user_id, session)
        except Exception as u_err:
            print(f"[ERROR] Failed to increment interview usage: {u_err}")

    # Log turn lifecycle events by comparing before and after states
    try:
        # Phase Transition Event
        prev_phase = current_state.get("interview_phase", "INTRODUCTION")
        if current_phase != prev_phase:
            log_structured_event("Phase Transition", {
                "interview_id": interview.id,
                "from_phase": prev_phase,
                "to_phase": current_phase
            })
            
        # Objective Selected Event
        prev_obj = current_state.get("active_objective")
        if active_obj != prev_obj:
            log_structured_event("Objective Selected", {
                "interview_id": interview.id,
                "objective": active_obj
            })
            
        # Claims Verification Status Changes
        prev_km = current_state.get("knowledge_model") or {}
        prev_claims = prev_km.get("claims") or prev_km.get("unproven_claims") or []
        prev_states = {c.get("claim"): c.get("state") for c in prev_claims if c.get("claim")}
        
        curr_claims = knowledge_model.get("claims") or []
        for c in curr_claims:
            c_text = c.get("claim")
            if c_text:
                prev_s = prev_states.get(c_text)
                curr_s = c.get("state")
                if curr_s != prev_s:
                    if curr_s == "VERIFIED":
                        log_structured_event("Claim Verified", {
                            "interview_id": interview.id,
                            "claim": c_text,
                            "project": c.get("project")
                        })
                    elif curr_s == "FAILED_VERIFICATION":
                        log_structured_event("Claim Failed Verification", {
                            "interview_id": interview.id,
                            "claim": c_text,
                            "project": c.get("project")
                        })
                        
        # Objective Verification Status Changes
        for sec in ["must_verify", "nice_to_verify"]:
            prev_objs = before_objectives.get(sec, {}) if before_objectives else {}
            curr_objs = interview_objectives.get(sec, {})
            for name, o_data in curr_objs.items():
                if isinstance(o_data, dict):
                    prev_status = prev_objs.get(name, {}).get("status") if isinstance(prev_objs.get(name), dict) else None
                    curr_status = o_data.get("status")
                    if curr_status != prev_status and curr_status == "verified":
                        log_structured_event("Objective Verified", {
                            "interview_id": interview.id,
                            "objective": name,
                            "section": sec
                        })
                        
        # Interview Completed Event
        if agent_status == "completed" and current_state.get("status") != "completed":
            log_structured_event("Interview Completed", {
                "interview_id": interview.id,
                "turns_count": interview.question_count
            })
    except Exception as le:
        print(f"Failed to log structured lifecycle event: {le}")
    
    # --- Auto-generate Report on completion ---
    if agent_status == "completed":
        run_report_in_background(id)
            
    return {
        "sender": "interviewer",
        "text": next_question,
        "question_count": interview.question_count,
        "max_question_count": interview.max_question_count,
        "status": interview.status,
        "interview_phase": interview.interview_phase,
        "debug_dashboard": debug_dashboard
    }


# --- WebSocket stream ---
@router.websocket("/{id}/stream")
async def interview_stream(websocket: WebSocket, id: str, token: Optional[str] = None):
    # Verify token
    try:
        user_id = auth_service.get_user_id(token) if token else None
        if not auth_service.IS_TESTING and not user_id:
            await websocket.accept()
            await websocket.send_json({"error": "Unauthorized WebSocket connection"})
            await websocket.close(code=4001)
            return
    except Exception as e:
        try:
            await websocket.accept()
            await websocket.send_json({"error": f"Authentication failed: {str(e)}"})
            await websocket.close(code=4001)
        except:
            pass
        return
        
    await websocket.accept()
    
    try:
        while True:
            # Receive candidate response JSON
            data = await websocket.receive_json()
            candidate_text = data.get("text", "").strip()
            
            if not candidate_text:
                continue
            
            with Session(engine) as session:
                try:
                    # Verify session ownership
                    interview = session.get(Interview, id)
                    if not interview or (not auth_service.IS_TESTING and interview.user_id != user_id):
                        await websocket.send_json({"error": "Interview session not found or forbidden"})
                        await websocket.close()
                        break
                        
                    response_payload = process_interview_turn(id, candidate_text, session)
                    await websocket.send_json(response_payload)
                    
                    if response_payload["status"] == "completed":
                        await websocket.close()
                        break
                except ValueError as ve:
                    await websocket.send_json({"error": str(ve)})
                    await websocket.close()
                    break
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
            await websocket.close()
        except:
            pass
