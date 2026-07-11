import os
import json
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.profiles import ROLE_PROFILES

def normalize_interview_objectives(objectives, fallback=None) -> dict:
    """
    Converts planner/gap-analysis objective formats into the dict shape used by
    the interview agent. Each objective starts with confidence = 0 and tracks
    5 sub-evidence categories.
    """
    default_obj_structure = {
        "confidence": 0,
        "status": "unverified",
        "attempts": 0,
        "evidence_categories": {
            "architecture": False,
            "debugging": False,
            "tradeoffs": False,
            "implementation": False,
            "scaling": False
        }
    }

    fallback = fallback or {
        "must_verify": {
            "Project Ownership": dict(default_obj_structure),
            "System Understanding": dict(default_obj_structure),
            "Problem Solving & Debugging": dict(default_obj_structure)
        },
        "nice_to_verify": {
            "Decision & Tradeoff Thinking": dict(default_obj_structure),
            "Scaling & Production Thinking": dict(default_obj_structure),
            "Behavioral & Communication": dict(default_obj_structure)
        }
    }

    def create_nested_objective(obj_name, existing_data=None):
        import copy
        nested = copy.deepcopy(default_obj_structure)
        if isinstance(existing_data, dict):
            nested["confidence"] = existing_data.get("confidence", 0)
            nested["attempts"] = existing_data.get("attempts", 0)
            nested["status"] = existing_data.get("status", "unverified")
            if "evidence_categories" in existing_data:
                for k in nested["evidence_categories"].keys():
                    if k in existing_data["evidence_categories"]:
                        nested["evidence_categories"][k] = bool(existing_data["evidence_categories"][k])
        elif isinstance(existing_data, str):
            nested["status"] = existing_data
            if existing_data == "verified":
                nested["confidence"] = 100
                for k in nested["evidence_categories"].keys():
                    nested["evidence_categories"][k] = True
        return nested

    if not objectives:
        import copy
        return copy.deepcopy(fallback)

    res = {
        "must_verify": {},
        "nice_to_verify": {}
    }

    if isinstance(objectives, list):
        for item in objectives:
            text = str(item).strip()
            if text:
                res["must_verify"][text] = create_nested_objective(text)
        for key in ["must_verify", "nice_to_verify"]:
            for name, fallback_val in fallback.get(key, {}).items():
                if name not in res["must_verify"] and name not in res["nice_to_verify"]:
                    import copy
                    res[key][name] = copy.deepcopy(fallback_val)
        return res

    if isinstance(objectives, dict):
        for key in ["must_verify", "nice_to_verify"]:
            raw_group = objectives.get(key, {})
            if isinstance(raw_group, list):
                raw_group = {str(item): "unverified" for item in raw_group if str(item).strip()}
            
            if isinstance(raw_group, dict):
                for name, value in raw_group.items():
                    name_str = str(name).strip()
                    if name_str:
                        res[key][name_str] = create_nested_objective(name_str, value)

        if not res["must_verify"] and not res["nice_to_verify"]:
            import copy
            return copy.deepcopy(fallback)
            
        for key in ["must_verify", "nice_to_verify"]:
            if not res[key]:
                import copy
                res[key] = copy.deepcopy(fallback.get(key, {}))
        return res

    import copy
    return copy.deepcopy(fallback)

from app.models.profile import CandidateProfile, JobProfile, GapAnalysis, CompanyProfile, InterviewBlueprint

def build_interview_blueprint(
    mode: str,
    role: str,
    difficulty: str,
    duration_minutes: int,
    company_profile: CompanyProfile,
    candidate_profile: Optional[CandidateProfile] = None,
    job_profile: Optional[JobProfile] = None,
    gap_analysis: Optional[GapAnalysis] = None
) -> InterviewBlueprint:
    """
    Connects to Gemini to generate the structured InterviewBlueprint.
    Consumes candidate/job profiles and gap analysis instead of raw text.
    """
    from app.services.cache import comp_cache, hash_text
    import time
    
    cand_hash = hash_text(candidate_profile.model_dump_json()) if candidate_profile else "none"
    job_hash = hash_text(job_profile.model_dump_json()) if job_profile else "none"
    company_name = company_profile.company_name.lower().strip() if company_profile else "standard"
    
    key_identifier = f"{role}:{mode}:{difficulty}:{duration_minutes}:{company_name}:{cand_hash}:{job_hash}"
    key = comp_cache.generate_cache_key("blueprint", "v1", key_identifier)
    
    cached = comp_cache.get(key)
    if cached:
        return cached
        
    start_time = time.perf_counter()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    use_live_api = api_key and api_key != "placeholder_api_key" and api_key != "your_gemini_api_key_here"
    
    # 1. Fallback Topic Tree & Objectives based on role profile
    profile = ROLE_PROFILES.get(role, ROLE_PROFILES["AI Engineer"])
    fallback_topics = profile.get("topics", ["Machine Learning", "Python", "System Design"])
    
    fallback_tree = {}
    fallback_concepts = {}
    for idx, t in enumerate(fallback_topics):
        if t == "Machine Learning":
            sub_map = {
                "Supervised Learning": ["Loss Functions", "Gradient Descent"],
                "Deep Neural Networks": ["Backpropagation", "Activations"]
            }
        elif t == "Python":
            sub_map = {
                "OOP Programming": ["Inheritance & Polymorphism", "Decorators"],
                "Memory Management": ["Garbage Collection", "Reference Counting"]
            }
        elif t == "System Design":
            sub_map = {
                "Distributed Systems": ["Load Balancers", "Sharding & Replication"],
                "Database Design": ["SQL vs NoSQL", "ACID Transactions"]
            }
        else:
            sub_map = {
                f"Core {t}": ["Foundational Theory", "Syntax & Rules"],
                f"Applied {t}": ["Architecture", "Production Scaling"]
            }
            
        fallback_concepts[t] = {c: "uncovered" for c in sub_map.keys()}
        fallback_tree[t] = sub_map
        
    fallback_objectives = {
        "must_verify": {},
        "nice_to_verify": {}
    }
    
    default_obj_structure = {
        "confidence": 0,
        "status": "unverified",
        "attempts": 0,
        "evidence_categories": {
            "architecture": False,
            "debugging": False,
            "tradeoffs": False,
            "implementation": False,
            "scaling": False
        }
    }
    
    for idx, t in enumerate(fallback_topics):
        obj_name = f"{t} Mastery"
        if idx < 2:
            fallback_objectives["must_verify"][obj_name] = dict(default_obj_structure)
        else:
            fallback_objectives["nice_to_verify"][obj_name] = dict(default_obj_structure)
            
    if "Project Ownership" not in fallback_objectives["must_verify"] and "Project Ownership" not in fallback_objectives["nice_to_verify"]:
        fallback_objectives["must_verify"]["Project Ownership"] = dict(default_obj_structure)
        
    project_targets = []
    if candidate_profile and candidate_profile.projects:
        project_targets = [p.title for p in candidate_profile.projects if p.title]
    proj_weight = company_profile.project_depth if company_profile else 0.3
    code_weight = company_profile.coding_weight if company_profile else 0.4
    sys_weight = company_profile.system_design_weight if company_profile else 0.3
    
    coverage_budget = {
        "project_investigation": proj_weight,
        "technical_coding": code_weight,
        "system_design": sys_weight
    }
    
    evaluation_weights = {
        "technical": code_weight + sys_weight,
        "communication": 0.2,
        "problem_solving": 0.3,
        "behavioral": 0.1
    }
    
    if use_live_api:
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.0,
                google_api_key=api_key,
                response_mime_type="application/json",
                max_retries=1
            )
            
            prompt_context = ""
            if candidate_profile:
                prompt_context += f"Candidate Tech Background:\n{candidate_profile.model_dump_json(indent=2)}\n\n"
            if job_profile:
                prompt_context += f"Job Description Profile:\n{job_profile.model_dump_json(indent=2)}\n\n"
            if gap_analysis:
                prompt_context += f"Gap Analysis Priorities:\n{gap_analysis.model_dump_json(indent=2)}\n\n"
                
            planner_prompt = (
                "You are an expert technical interviewer and blueprint planner. Generate a structured interview blueprint "
                "for a candidate based on their profile, the target job requirements, and the gap analysis.\n\n"
                f"{prompt_context}"
                f"Role Name: {role}\n"
                f"Company Focus & Culture: {company_profile.question_philosophy}\n"
                f"Target Level: {difficulty}\n"
                f"Interview Duration: {duration_minutes} minutes\n\n"
                "Construct the JSON blueprint containing:\n"
                "1. topic_tree: 3 specific technical topics to cover. For each topic, map exactly 2 subconcepts. For each subconcept, list exactly 2 key discussion points.\n"
                "2. interview_objectives: Group objectives into 'must_verify' (2-3 items) and 'nice_to_verify' (2-3 items). Ensure 'Project Ownership' is one of the must_verify objectives if candidate has projects.\n"
                "3. concept_coverage: Initialize a dictionary where each of the 3 topics contains its 2 subconcepts initialized to 'uncovered'.\n"
                "4. project_targets: Projects from the candidate profile to probe during the interview.\n"
                "5. interview_strategy: A short strategic description of how the interviewer should guide the conversation.\n"
                "6. interview_order: Order in which the 3 topics should be introduced.\n\n"
                "Return JSON matching this schema:\n"
                "{\n"
                "  \"topic_tree\": {\n"
                "     \"Topic Name\": {\n"
                "        \"Subconcept Name\": [\"Key Point 1\", \"Key Point 2\"]\n"
                "     }\n"
                "  },\n"
                "  \"interview_objectives\": {\n"
                "     \"must_verify\": [\"Project Ownership\", \"Topic Name 1 Mastery\"],\n"
                "     \"nice_to_verify\": [\"Topic Name 2 Mastery\"]\n"
                "  },\n"
                "  \"concept_coverage\": {\n"
                "     \"Topic Name\": {\n"
                "        \"Subconcept Name\": \"uncovered\"\n"
                "     }\n"
                "  },\n"
                "  \"project_targets\": [\"Project Title to Verify\"],\n"
                "  \"interview_strategy\": \"Strategy explanation.\",\n"
                "  \"interview_order\": [\"Topic1\", \"Topic2\"]\n"
                "}"
            )
            
            response = llm.invoke([
                SystemMessage(content=planner_prompt),
                HumanMessage(content="Generate the interview blueprint.")
            ])
            
            content_val = response.content
            if isinstance(content_val, list):
                content_val = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content_val)
            elif not isinstance(content_val, str):
                content_val = str(content_val)
                
            data = json.loads(content_val.strip())
            
            blueprint = InterviewBlueprint(
                topic_tree=data.get("topic_tree", fallback_tree),
                interview_objectives=normalize_interview_objectives(data.get("interview_objectives"), fallback_objectives),
                concept_coverage=data.get("concept_coverage", fallback_concepts),
                project_targets=data.get("project_targets", project_targets),
                coverage_budget=coverage_budget,
                interview_strategy=data.get("interview_strategy", "Standard assessment."),
                evaluation_weights=evaluation_weights,
                interview_order=data.get("interview_order", fallback_topics)
            )
            comp_cache.record_generation_time(time.perf_counter() - start_time)
            comp_cache.set(key, blueprint)
            return blueprint
        except Exception as e:
            print(f"[WARNING] build_interview_blueprint LLM failed: {e}. Utilizing fallback blueprint.")
            
    blueprint = InterviewBlueprint(
        topic_tree=fallback_tree,
        interview_objectives=normalize_interview_objectives(fallback_objectives, fallback_objectives),
        concept_coverage=fallback_concepts,
        project_targets=project_targets,
        coverage_budget=coverage_budget,
        interview_strategy="Fallback standard assessment.",
        evaluation_weights=evaluation_weights,
        interview_order=fallback_topics
    )
    comp_cache.record_generation_time(time.perf_counter() - start_time)
    comp_cache.set(key, blueprint)
    return blueprint


def generate_interview_plan(mode: str, company: str, role: str, resume_text: str = None, jd_text: str = None) -> dict:
    from app.services.profile_service import get_company_profile, build_candidate_profile, build_job_profile, build_gap_analysis
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    cand_prof = loop.run_until_complete(build_candidate_profile(resume_text)) if resume_text else None
    job_prof = loop.run_until_complete(build_job_profile(jd_text)) if jd_text else None
    gap = loop.run_until_complete(build_gap_analysis(cand_prof, job_prof)) if (cand_prof and job_prof) else None
    comp_prof = get_company_profile(company)
    
    blueprint = build_interview_blueprint(
        mode=mode,
        role=role,
        difficulty="medium",
        duration_minutes=15,
        company_profile=comp_prof,
        candidate_profile=cand_prof,
        job_profile=job_prof,
        gap_analysis=gap
    )
    return {
        "topic_tree": blueprint.topic_tree,
        "interview_objectives": blueprint.interview_objectives,
        "concept_coverage": blueprint.concept_coverage
    }


def build_contextual_fallback_question(
    *,
    role: str,
    interview_objectives: Optional[Dict[str, Any]] = None,
    gap_analysis: Optional[Dict[str, Any]] = None,
    missing_topics: Optional[List[str]] = None,
    knowledge_model: Optional[Dict[str, Any]] = None,
    project_investigation: Optional[Dict[str, Any]] = None,
    is_opening: bool = False,
    is_wrap_up: bool = False
) -> Dict[str, Any]:
    if is_wrap_up:
        return {
            "question": "Thank you for your time. This concludes the mock interview, and your transcript is ready for review.",
            "topic": "Wrap-up",
            "expected_concepts": []
        }

    objectives = normalize_interview_objectives(interview_objectives)
    active_objective = None
    for bucket in ["must_verify", "nice_to_verify"]:
        for name, status in objectives.get(bucket, {}).items():
            if status != "verified":
                active_objective = name
                break
        if active_objective:
            break

    target = None
    unproven = (knowledge_model or {}).get("unproven_claims", [])
    for claim in unproven:
        if claim.get("state") in ["UNVERIFIED", "PROBED"] and claim.get("claim"):
            target = claim.get("claim")
            break

    gap_analysis = gap_analysis or {}
    resume = gap_analysis.get("extracted_resume", {}) or {}
    jd = gap_analysis.get("extracted_jd", {}) or {}
    gap = gap_analysis.get("gap_analysis", {}) or {}
    projects = resume.get("projects", []) if isinstance(resume.get("projects", []), list) else []
    skills = resume.get("skills", []) if isinstance(resume.get("skills", []), list) else []
    required = jd.get("required_skills", []) if isinstance(jd.get("required_skills", []), list) else []
    missing = gap.get("missing_skills", []) if isinstance(gap.get("missing_skills", []), list) else []

    project_investigation = project_investigation or {}
    project_name = project_investigation.get("project_name")
    
    claim_project = None
    for claim in unproven:
        if claim.get("state") in ["UNVERIFIED", "PROBED"] and claim.get("project") and claim.get("project") != "General":
            claim_project = claim.get("project")
            break
            
    actual_project = project_name or claim_project

    project_title = None
    if projects:
        first_project = projects[0]
        if isinstance(first_project, dict):
            project_title = first_project.get("title") or first_project.get("name")
        else:
            project_title = str(first_project)

    known_project = actual_project or project_title

    # Ask for discovery if we need project ownership but have no project
    if active_objective and "ownership" in active_objective.lower() and not known_project:
        return {
            "question": "Could you walk me through one of the most challenging technical projects you've worked on, its system design, and your exact contribution?",
            "topic": "Project Discovery",
            "expected_concepts": []
        }

    if not target:
        target = known_project or (missing[0] if missing else None) or (required[0] if required else None) or (skills[0] if skills else None)
    if not target and missing_topics:
        target = missing_topics[0]
    if not target:
        target = active_objective or role

    if is_opening:
        question = (
            f"Welcome. I want to start with something concrete from your background: walk me through {target}, "
            "especially your exact contribution, one key design decision, and one difficulty you had to solve."
        )
    elif active_objective and "ownership" in active_objective.lower():
        if target == known_project:
            question = (
                f"Let's verify ownership around {target}. What part did you personally build, what tradeoff did you choose, "
                "and how would I see that decision reflected in the implementation?"
            )
        else:
            question = (
                f"Let's discuss {target}. What is its core mechanism, and how have you used it or evaluated its performance?"
            )
    elif active_objective:
        question = (
            f"Let's focus on {active_objective}. Using {target} as the example, can you explain the mechanism, "
            "the main tradeoff, and a concrete failure case or limitation?"
        )
    else:
        question = (
            f"Let's go deeper on {target}. Can you explain how it works in practice and describe a specific implementation "
            "or debugging decision you made around it?"
        )

    expected = []
    if target and str(target) not in [active_objective, role, "Project Discovery", "Project Ownership", "System Understanding", "Problem Solving & Debugging"]:
        expected.append(str(target))

    return {
        "question": question,
        "topic": str(target),
        "expected_concepts": expected
    }

