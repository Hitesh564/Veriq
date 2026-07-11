import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict, Any, Optional

from app.agents.profiles import ROLE_PROFILES

def run_evaluation(role: str, difficulty: str, transcripts: List[Dict[str, Any]], topic_tree: Optional[Dict[str, Any]] = None, knowledge_model: Optional[Dict[str, Any]] = None, concept_coverage: Optional[Dict[str, Any]] = None, interview_objectives: Optional[Dict[str, Any]] = None, project_investigation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Evaluates the complete interview transcripts using Gemini and outputs a structured JSON report.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        api_key = "placeholder_api_key"
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0.3, # Lower temperature for more factual, stable analysis
        google_api_key=api_key,
        response_mime_type="application/json",
        max_retries=1
    )
    
    profile = ROLE_PROFILES.get(role, ROLE_PROFILES["AI Engineer"])
    
    # 1. Format the transcript log with per-turn evaluations for the LLM
    formatted_log = []
    for idx, t in enumerate(transcripts):
        sender_label = "Interviewer" if t["sender"] == "interviewer" else "Candidate"
        entry = f"[{sender_label}] (Difficulty: {t.get('difficulty', difficulty)})"
        entry += f"\nText: {t['text']}"
        
        # If it's a candidate answer, add the per-turn assessment metadata
        if t["sender"] == "candidate":
            entry += f"\n- Assigned Topic: {t.get('topic')}"
            entry += f"\n- Turn score (1-5): {t.get('score')}"
            entry += f"\n- Critique reasoning: {t.get('reasoning_summary')}"
            if t.get("secondary_topics"):
                entry += f"\n- Secondary Topics: {', '.join(t['secondary_topics'])}"
                
        formatted_log.append(entry)
        
    transcript_text = "\n\n".join(formatted_log)
    
    # 2. Extract and format structured evidence from the inputs in Python
    km = knowledge_model or {}
    objectives = interview_objectives or {}
    proj = project_investigation or {}

    # Extract verified/failed claims
    verified_claims = []
    unproven_claims_list = km.get("claims") or km.get("unproven_claims") or []
    for claim in unproven_claims_list:
        c_text = claim.get("claim", "")
        if c_text:
            if claim.get("state") == "VERIFIED" or c_text in km.get("proven_skills", []):
                if c_text not in verified_claims:
                    verified_claims.append(c_text)
    for skill in km.get("proven_skills", []):
        if skill not in verified_claims:
            verified_claims.append(skill)
            
    failed_claims = []
    for claim in unproven_claims_list:
        c_text = claim.get("claim", "")
        if c_text:
            if claim.get("state") == "FAILED_VERIFICATION" or c_text in km.get("weak_skills", []):
                if c_text not in failed_claims:
                    failed_claims.append(c_text)
    for skill in km.get("weak_skills", []):
        if skill not in failed_claims:
            failed_claims.append(skill)

    weak_skills = km.get("weak_skills", [])
    strong_skills = km.get("proven_skills", [])

    # Format objective summary
    objective_summary = []
    for section_name in ["must_verify", "nice_to_verify"]:
        section = objectives.get(section_name, {})
        for obj_name, obj_data in section.items():
            if isinstance(obj_data, dict):
                obj_sum = {
                    "objective": obj_name,
                    "type": section_name,
                    "confidence": obj_data.get("confidence", 0),
                    "status": obj_data.get("status", "unverified"),
                    "attempts": obj_data.get("attempts", 0)
                }
                objective_summary.append(obj_sum)

    # Format project verification summary
    project_verification_summary = {
        "project_name": proj.get("project_name", "N/A"),
        "turns_spent": proj.get("turns_spent", 0),
        "verified_categories": proj.get("verified_categories", []),
        "verification_plan": proj.get("verification_plan", {})
    }

    # Python computation of metrics to avoid LLM hallucinations/inconsistencies
    # Modification 1: Compute Fallback Ownership Score in Python
    verified_claims_count = len(verified_claims)
    failed_claims_count = len(failed_claims)
    
    # Calculate a sensible fallback/starting ownership score in case LLM parsing fails
    proj_plan = project_verification_summary.get("verification_plan") or {}
    arch_pts = 80 if proj_plan.get("architecture") else 50
    impl_pts = 80 if proj_plan.get("implementation") else 40
    tradeoff_pts = 80 if proj_plan.get("tradeoffs") else 40
    debug_pts = 80 if proj_plan.get("debugging") else 40
    fail_pts = 80 if proj_plan.get("failure_cases") else 40
    
    fallback_ownership_calc = int(
        0.40 * arch_pts +
        0.30 * impl_pts +
        0.15 * tradeoff_pts +
        0.10 * debug_pts +
        0.05 * fail_pts
    )
    fallback_ownership_score = max(0, min(100, fallback_ownership_calc - (failed_claims_count * 3)))

    # Modification 2: Compute Interview Completion Score in Python
    must_list = objectives.get("must_verify", {})
    nice_list = objectives.get("nice_to_verify", {})
    
    total_confidence = 0
    objectives_verified = 0
    for obj_name, obj_data in must_list.items():
        if isinstance(obj_data, dict):
            total_confidence += obj_data.get("confidence", 0)
            if obj_data.get("status") == "verified" or obj_data.get("confidence", 0) >= 60:
                objectives_verified += 1
                
    for obj_name, obj_data in nice_list.items():
        if isinstance(obj_data, dict):
            total_confidence += obj_data.get("confidence", 0) * 0.5
            if obj_data.get("status") == "verified" or obj_data.get("confidence", 0) >= 60:
                objectives_verified += 1
                
    possible_objectives_weight = len(must_list) + len(nice_list) * 0.5
    objective_ratio = (total_confidence / (possible_objectives_weight * 100)) if possible_objectives_weight > 0 else 1.0
    
    concepts = concept_coverage or {}
    covered_count = sum(1 for c, status in concepts.items() if status != "uncovered")
    total_concepts_count = len(concepts)
    coverage_ratio = (covered_count / total_concepts_count) if total_concepts_count > 0 else 1.0
    
    completion_score = int((0.7 * objective_ratio + 0.3 * coverage_ratio) * 100)
    interview_completion_score = max(0, min(100, completion_score))

    # Modification 3: Construct evaluation_evidence block in Python
    evaluation_evidence = {
        "verified_claims_count": verified_claims_count,
        "failed_claims_count": failed_claims_count,
        "weak_skills_count": len(weak_skills),
        "strong_skills_count": len(strong_skills),
        "objectives_verified": objectives_verified
    }
    
    topic_tree_str = json.dumps(topic_tree, indent=2) if topic_tree else "N/A"
    concept_coverage_str = json.dumps(concept_coverage, indent=2) if concept_coverage else "N/A"
    
    # 3. Build the system instruction detailing the metrics and output structure
    system_instruction = (
        f"You are an expert executive recruiter and technical interviewer conducting a post-interview evaluation.\n"
        f"The candidate was interviewed for a {role} position under {difficulty} difficulty guidelines.\n\n"
        f"You are provided with structured evidence gathered during the interview:\n"
        f"- Verified Claims: {json.dumps(verified_claims, indent=2)}\n"
        f"- Failed Claims: {json.dumps(failed_claims, indent=2)}\n"
        f"- Weak Skills: {json.dumps(weak_skills, indent=2)}\n"
        f"- Strong Skills: {json.dumps(strong_skills, indent=2)}\n"
        f"- Objective Summary: {json.dumps(objective_summary, indent=2)}\n"
        f"- Project Verification Summary: {json.dumps(project_verification_summary, indent=2)}\n"
        f"- Concept Coverage: {concept_coverage_str}\n"
        f"- Topic Tree: {topic_tree_str}\n\n"
        f"And pre-calculated metrics (You MUST output these exact values in the JSON fields):\n"
        f"- Pre-calculated Interview Completion Score: {interview_completion_score}\n"
        f"- Pre-calculated Evaluation Evidence: {json.dumps(evaluation_evidence, indent=2)}\n\n"
        f"Instructions:\n"
        f"1. SCORING PHILOSOPHY & CALIBRATION (CRITICAL):\n"
        f"   - Calibrate scoring to realistic internship interview expectations. Remain technically rigorous while avoiding unnecessarily punitive scoring for isolated implementation gaps.\n"
        f"   - Evaluate all dimensions entirely independently. Do NOT collapse multiple scores because of a single weak answer or missing code detail.\n"
        f"   - Explicitly apply this HIERARCHY OF KNOWLEDGE:\n"
        f"     * Conceptual understanding -> Architecture understanding -> Implementation understanding -> Code-level mastery\n"
        f"     * If a candidate demonstrates strong conceptual and architectural understanding but lacks implementation details or code-level mastery, they should score satisfactory/medium (45-65 range) on Technical Knowledge/Project Explanation. Do NOT collapse all scores to low/failed.\n"
        f"   - Evaluate Communication Quality entirely independently from technical ability. Candidates who communicate clearly, structure answers well, and articulate concepts nicely must receive a high communication score (e.g. 75-90) even if they have technical gaps.\n"
        f"   - Give architecture understanding full independent credit under Technical Knowledge and Project Explanation, even if code-level implementation details are weak.\n\n"
        f"2. EVALUATING DIMENSIONS:\n"
        f"   - Rate the candidate on 5 dimensions (on a scale from 0 to 100):\n"
        f"     * Technical Knowledge: Depth of understanding of role-specific concepts.\n"
        f"     * Communication Quality: Clarity, structure, articulation, and assertiveness.\n"
        f"     * Project Explanation: Competence describing architecture, design patterns, and decisions.\n"
        f"     * Problem Solving: Analytical capability, structure, handling edge cases.\n"
        f"     * Behavioral Performance: Soft skills, attitude, role alignment.\n"
        f"   - Rate 5 independent Project Ownership sub-scores (0-100):\n"
        f"     * architecture_understanding: Candidate's grasp of their project's high-level components and flow.\n"
        f"     * implementation_understanding: Candidate's grasp of lower-level verbal code details.\n"
        f"     * design_decisions: Candidate's grasp of alternative solutions and justifications.\n"
        f"     * trade_offs: Candidate's grasp of constraints (latency, cost, complexity).\n"
        f"     * limitations_future_work: Candidate's grasp of failures, edge cases, and improvements.\n"
        f"     * NOTE: If the candidate had no project targets, score these sub-scores based on their system design and architecture answers generally. If untested, default to 80.\n\n"
        f"3. RECRUITER SUMMARY & OUTCOMES:\n"
        f"   - In your recruiter summary (the 'summary' field), explicitly state the candidate's demonstrated understanding style (Genuine, Memorized, or Bluffing) as captured in the knowledge model.\n"
        f"   - Identify 3-5 key Strengths of the candidate.\n"
        f"   - Identify and categorize Weaknesses into: conceptual_gaps, communication_issues, explanation_issues, and behavioral_weaknesses.\n"
        f"   - Provide 3-5 specific, actionable recommendations for improvement, mapped directly to Weak Skills, Failed Claims, and low-confidence objectives.\n"
        f"   - Assess the candidate's mastery of each individual topic from this list: {', '.join(profile['topics'])}. Assign a score (0 to 100) for each topic discussed. Do not include topics not discussed.\n"
        f"   - Categorize claim verification into a 'claim_verification_summary' object listing 'verified_claims', 'partially_verified_claims', and 'failed_claims'.\n"
        f"   - Create a detailed 'learning_plan' object split into: 'high_priority', 'medium_priority', and 'low_priority'.\n"
        f"   - Determine a 'hire_recommendation' (values: 'Strong Hire', 'Hire', 'Borderline', 'No Hire') and 'confidence_level' (values: 'High', 'Medium', 'Low').\n\n"
        f"You MUST return a raw JSON object matching the following schema:\n"
        f"{{\n"
        f"  \"summary\": \"Recruiter-style summary text...\",\n"
        f"  \"technical_score\": <Integer 0-100>,\n"
        f"  \"communication_score\": <Integer 0-100>,\n"
        f"  \"explanation_score\": <Integer 0-100>,\n"
        f"  \"problem_solving_score\": <Integer 0-100>,\n"
        f"  \"behavioral_score\": <Integer 0-100>,\n"
        f"  \"ownership_sub_scores\": {{\n"
        f"     \"architecture_understanding\": <Integer 0-100>,\n"
        f"     \"implementation_understanding\": <Integer 0-100>,\n"
        f"     \"design_decisions\": <Integer 0-100>,\n"
        f"     \"trade_offs\": <Integer 0-100>,\n"
        f"     \"limitations_future_work\": <Integer 0-100>\n"
        f"  }},\n"
        f"  \"ownership_score\": 0,\n"
        f"  \"interview_completion_score\": {interview_completion_score},\n"
        f"  \"evaluation_evidence\": {json.dumps(evaluation_evidence)},\n"
        f"  \"strengths\": [<list of strength strings>],\n"
        f"  \"categorized_weaknesses\": {{\n"
        f"     \"conceptual_gaps\": [<list of strings>],\n"
        f"     \"communication_issues\": [<list of strings>],\n"
        f"     \"explanation_issues\": [<list of strings>],\n"
        f"     \"behavioral_weaknesses\": [<list of strings>]\n"
        f"  }},\n"
        f"  \"topic_performance\": {{\n"
        f"     \"TopicName\": <Integer score 0-100>,\n"
        f"     ...\n"
        f"  }},\n"
        f"  \"claim_verification_summary\": {{\n"
        f"     \"verified_claims\": [<list of strings>],\n"
        f"     \"partially_verified_claims\": [<list of strings>],\n"
        f"     \"failed_claims\": [<list of strings>]\n"
        f"  }},\n"
        f"  \"learning_plan\": {{\n"
        f"     \"high_priority\": [<list of strings>],\n"
        f"     \"medium_priority\": [<list of strings>],\n"
        f"     \"low_priority\": [<list of strings>]\n"
        f"  }},\n"
        f"  \"recommendations\": [<list of specific recommendation strings>],\n"
        f"  \"hire_recommendation\": \"<Strong Hire | Hire | Borderline | No Hire>\",\n"
        f"  \"confidence_level\": \"<High | Medium | Low>\"\n"
        f"}}"
    )
    
    # 4. Call LLM
    try:
        response = llm.invoke([
            SystemMessage(content=system_instruction),
            HumanMessage(content=f"Here is the complete interview transcript:\n\n{transcript_text}")
        ])
        
        # Parse returned JSON
        data = parse_json_content(response.content)
        
        # Calculate dynamic ownership_score in Python using sub-scores and -3 penalty
        sub_scores = data.get("ownership_sub_scores", {})
        if not isinstance(sub_scores, dict):
            sub_scores = {}
        arch_val = sub_scores.get("architecture_understanding", 80)
        impl_val = sub_scores.get("implementation_understanding", 80)
        decisions_val = sub_scores.get("design_decisions", 80)
        tradeoffs_val = sub_scores.get("trade_offs", 80)
        limitations_val = sub_scores.get("limitations_future_work", 80)
        
        calculated_ownership = int(
            0.40 * arch_val +
            0.30 * impl_val +
            0.15 * decisions_val +
            0.10 * tradeoffs_val +
            0.05 * limitations_val
        )
        ownership_score = max(0, min(100, calculated_ownership - (failed_claims_count * 3)))
        data["ownership_score"] = ownership_score
        
        # Ensure raw response is attached as a serialized JSON string representing the dict
        data["raw_json"] = json.dumps(data)
        return data
    except Exception as e:
        print(f"Evaluation Agent LLM Call Failed: {e}")
        # Fallback evaluation object
        return {
            "summary": "Evaluation failed due to LLM error. Please regenerate later.",
            "technical_score": 50,
            "communication_score": 50,
            "explanation_score": 50,
            "problem_solving_score": 50,
            "behavioral_score": 50,
            "ownership_score": fallback_ownership_score,
            "interview_completion_score": interview_completion_score,
            "evaluation_evidence": evaluation_evidence,
            "strengths": ["Evaluation runner executed"],
            "categorized_weaknesses": {
                "conceptual_gaps": ["Evaluation service encountered a runtime issue"],
                "communication_issues": [],
                "explanation_issues": [],
                "behavioral_weaknesses": []
            },
            "topic_performance": {},
            "claim_verification_summary": {
                "verified_claims": verified_claims,
                "partially_verified_claims": [],
                "failed_claims": failed_claims
            },
            "learning_plan": {
                "high_priority": failed_claims + list(weak_skills),
                "medium_priority": [],
                "low_priority": []
            },
            "recommendations": ["Re-run the evaluation once API connectivity is restored."],
            "hire_recommendation": "Borderline",
            "confidence_level": "Low",
            "raw_json": json.dumps({"error": str(e)})
        }

def parse_json_content(content) -> dict:
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict):
                if "text" in part:
                    text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        content = "".join(text_parts)
    elif not isinstance(content, str):
        content = str(content)
        
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except:
        return {}
