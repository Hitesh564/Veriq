"""
Interview Agent Module for AI Mock Technical Interviews.

This module implements a dynamic, adaptive, state-driven mock interviewer agent using LangGraph.
Key Responsibilities:
  1. Managing interview progression through 4 distinct phases: INTRODUCTION -> PROJECT_DISCOVERY -> TECHNICAL_EVALUATION -> WRAP_UP.
  2. Dynamically selecting active objectives (Project, Technical, Behavioral) based on duration budgets and target distributions.
  3. Probing and verifying technical claims made in candidate resumes or responses.
  4. Evaluating candidate answers for depth, specificity, evidence strength, and technical concept coverage.
  5. Dynamically adjusting interview difficulty (Easy/Medium/Hard) based on candidate performance.
  6. Employing sliding-window token management to optimize LLM context usage while retaining full interview state.
  7. Providing structured fallback questions if LLM invocation fails.
"""

import os
import json
from typing import Optional, Any
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.agents.state import InterviewState
from app.agents.profiles import ROLE_PROFILES
from app.agents.interview_planner import generate_interview_plan, build_contextual_fallback_question

# ============================================================================
# --- Extraction Helpers ---
# Helper functions for processing concept coverage, resumes, and question intent
# ============================================================================

def _first_uncovered_concept(concept_coverage: dict, weak_skills: list = None) -> str:
    """
    Finds and returns the first technical concept that has not been fully evaluated yet.
    
    Args:
        concept_coverage (dict): Map of concept names to coverage statuses ("covered", "partially_covered", "uncovered", "missed").
        weak_skills (list, optional): List of concept names already flagged as candidate weak skills (skipped first).
        
    Returns:
        str: The name of the first uncovered concept found, or empty string if all are covered.
    """
    weak_skills = weak_skills or []
    weak_skills_lower = [ws.lower() for ws in weak_skills]
    
    # First pass: Look for unverified/partially covered concepts that are NOT already in weak_skills
    for concept, status in (concept_coverage or {}).items():
        if concept.lower() in weak_skills_lower:
            continue
        if status in ["uncovered", "missed", "partially_covered"]:
            return concept
            
    # Second pass: Fall back to any concept needing coverage even if in weak_skills
    for concept, status in (concept_coverage or {}).items():
        if status in ["uncovered", "missed", "partially_covered"]:
            return concept
            
    return ""

def _flatten_projects(personalization_context: dict) -> list:
    """
    Extracts and flattens project entries from the candidate's resume context into a clean list of string summaries.
    
    Args:
        personalization_context (dict): Candidate context containing parsed resume, job description, and gap analysis.
        
    Returns:
        list: List of project summary strings (e.g., ["Project Alpha: Built a scalable backend API", ...]).
    """
    resume = (personalization_context or {}).get("extracted_resume", {})
    projects = resume.get("projects", [])
    if not isinstance(projects, list):
        return []
    flattened = []
    for project in projects:
        if isinstance(project, dict):
            title = project.get("title") or project.get("name") or "Unnamed project"
            description = project.get("description") or project.get("summary") or ""
            flattened.append(f"{title}: {description}".strip(": "))
        elif project:
            flattened.append(str(project))
    return flattened

def _pick_source_context(personalization_context: dict, active_objective: str, target_concept: str) -> dict:
    """
    Selects the most relevant context source (Resume Project, Resume Skill, JD Required Skill, Gap Skill, etc.)
    that aligns with the current active interview objective and target concept.
    
    Args:
        personalization_context (dict): Parsed resume, JD, and gap analysis details.
        active_objective (str): Current active objective being probed (e.g. "Project Ownership").
        target_concept (str): Specific concept or claim targeted for evaluation.
        
    Returns:
        dict: A dictionary containing 'type' and 'value' describing the selected source context.
    """
    personalization_context = personalization_context or {}
    resume = personalization_context.get("extracted_resume", {}) or {}
    jd = personalization_context.get("extracted_jd", {}) or {}
    gap = personalization_context.get("gap_analysis", {}) or {}
    objective_lower = active_objective.lower()
    target_lower = (target_concept or "").lower()

    # Extract available context lists from resume and job description
    projects = _flatten_projects(personalization_context)
    skills = resume.get("skills", []) if isinstance(resume.get("skills", []), list) else []
    required_skills = jd.get("required_skills", []) if isinstance(jd.get("required_skills", []), list) else []
    missing_skills = gap.get("missing_skills", []) if isinstance(gap.get("missing_skills", []), list) else []
    focus_areas = gap.get("focus_areas", []) if isinstance(gap.get("focus_areas", []), list) else []

    # Priority 1: Direct match against resume projects
    for project in projects:
        if "project" in objective_lower or any(token and token in project.lower() for token in [target_lower]):
            return {"type": "resume_project", "value": project}
            
    # Priority 2: Direct match against resume skills
    for skill in skills:
        if str(skill).lower() in objective_lower or str(skill).lower() == target_lower:
            return {"type": "resume_skill", "value": str(skill)}
            
    # Priority 3: Direct match against job description required skills
    for skill in required_skills:
        if str(skill).lower() in objective_lower or str(skill).lower() == target_lower:
            return {"type": "jd_required_skill", "value": str(skill)}
            
    # Priority 4: Direct match against skill gap missing items
    for skill in missing_skills:
        if str(skill).lower() in objective_lower or str(skill).lower() == target_lower:
            return {"type": "gap_missing_skill", "value": str(skill)}
            
    # Priority 5: Direct match against gap focus areas
    for area in focus_areas:
        if str(area).lower() in objective_lower or str(area).lower() == target_lower:
            return {"type": "gap_focus_area", "value": str(area)}

    # Priority 6: Fall back to first available context item in order of preference
    if projects:
        return {"type": "resume_project", "value": projects[0]}
    if required_skills:
        return {"type": "jd_required_skill", "value": str(required_skills[0])}
    if skills:
        return {"type": "resume_skill", "value": str(skills[0])}
    if focus_areas:
        return {"type": "gap_focus_area", "value": str(focus_areas[0])}
        
    # Default fallback to target concept or objective
    return {"type": "role_profile", "value": target_concept or active_objective}

def _build_evidence_requirements(strategy_action: str, difficulty: str, target_concept: str) -> list:
    """
    Generates a checklist of required evidence types based on strategy action, difficulty level, and target concept.
    
    Args:
        strategy_action (str): The interviewer action (e.g. 'CHALLENGE_CLAIM', 'PROBE_DEEPER', 'MOVE_TO_NEW_TOPIC').
        difficulty (str): Interview difficulty ("easy", "medium", "hard").
        target_concept (str): The specific technical concept being probed.
        
    Returns:
        list: List of concise evidence requirement statements (max 4 items).
    """
    base = {
        "CHALLENGE_CLAIM": [
            "specific implementation detail",
            "reasoning behind a technical decision",
            "tradeoff or failure mode they personally handled"
        ],
        "PROBE_DEEPER": [
            "step-by-step mechanism",
            "why the chosen approach works",
            "edge case or limitation"
        ],
        "ASK_CLARIFICATION": [
            "clear definition",
            "small concrete example",
            "correction of the missing or vague part"
        ],
        "REQUEST_EXAMPLE": [
            "real project example",
            "candidate's exact contribution",
            "result, metric, or debugging outcome"
        ],
        "MOVE_TO_NEW_TOPIC": [
            "core concept explanation",
            "practical application",
            "tradeoff or production consideration"
        ]
    }
    requirements = list(base.get(strategy_action, base["MOVE_TO_NEW_TOPIC"]))
    
    # Adjust depth based on difficulty settings
    if difficulty == "hard":
        requirements.append("deep technical detail beyond surface definitions")
    elif difficulty == "easy":
        requirements = requirements[:2]
        
    if target_concept:
        requirements.append(f"evidence related to {target_concept}")
        
    return requirements[:4]

def _build_question_intent(
    *,
    active_objective: str,
    strategy_action: str,
    difficulty: str,
    missing_topics: list,
    concept_coverage: dict,
    knowledge_model: dict,
    project_investigation: dict,
    personalization_context: dict,
    score_val,
    understanding_style: str
) -> dict:
    """
    Constructs a comprehensive Intent Object detailing why the next question is being asked,
    what target concept/claim is being targeted, and what evidence is required from the candidate.
    
    Returns:
        dict: Question intent payload used by the prompt builder and context metrics.
    """
    weak_skills = knowledge_model.get("weak_skills", []) if knowledge_model else []
    weak_skills_lower = [ws.lower() for ws in weak_skills]

    # Find the next unverified claim to target (skipping weak skills)
    target_claim = None
    claims_list = knowledge_model.get("claims") or knowledge_model.get("unproven_claims") or []
    for claim in claims_list:
        if claim.get("state") in ["PROBED", "UNVERIFIED"]:
            if claim.get("claim", "").lower() in weak_skills_lower:
                continue
            target_claim = claim
            break

    # Determine target concept priority: missing topic -> uncovered concept -> claim -> active project
    target_concept = ""
    filtered_missing = [t for t in missing_topics if t.lower() not in weak_skills_lower]
    if filtered_missing:
        target_concept = filtered_missing[0]
    if not target_concept:
        target_concept = _first_uncovered_concept(concept_coverage, weak_skills)
    if target_claim and target_claim.get("claim"):
        target_concept = target_claim.get("claim")
    if project_investigation.get("in_mode") and project_investigation.get("project_name"):
        target_concept = project_investigation["project_name"]

    source_context = _pick_source_context(personalization_context, active_objective, target_concept)

    # Determine transitional reasoning for interviewer continuity
    if score_val is None:
        transition = "Open the interview by anchoring on the candidate's strongest resume/JD signal."
    elif score_val <= 2:
        transition = "The previous answer was weak or vague; ask a focused clarification before moving on."
    elif understanding_style in ["BLUFFING", "MEMORIZED_KNOWLEDGE"]:
        transition = "The previous answer sounded memorized or unsupported; ask for concrete evidence."
    elif strategy_action == "CHALLENGE_CLAIM":
        transition = "The candidate made a claim that needs verification; ask a natural challenge."
    elif strategy_action == "PROBE_DEEPER":
        transition = "The previous answer was promising; drill one level deeper."
    else:
        transition = "Move to the next highest-priority uncovered objective without feeling abrupt."

    return {
        "objective": active_objective,
        "strategy_action": strategy_action,
        "target_concept_or_claim": target_concept or active_objective,
        "target_claim": target_claim,
        "source_context": source_context,
        "evidence_required": _build_evidence_requirements(strategy_action, difficulty, target_concept),
        "transition_reason": transition,
        "question_quality_rules": [
            "Ask exactly one main question, with at most one short follow-up clause.",
            "Tie the question to resume, JD, prior answer, or active objective.",
            "Avoid generic prompts like 'tell me about another skill'.",
            "Prefer ownership, decisions, tradeoffs, debugging, metrics, and failure modes over definitions.",
            "Do not reveal the rubric or expected concepts to the candidate."
        ]
    }


# ============================================================================
# --- Modular Pure-Refactored Helper Components (Behavior Preservation) ---
# Helper classes structuring prompt generation, phase transitions, objective
# selection, claim resolution, and response parsing.
# ============================================================================

class PromptBuilder:
    """
    Constructs system prompts and instructions for the LLM interviewer.
    
    Ensures consistent enforcement of verbal-only constraints, adaptive interviewer
    fluidity, scoring schema guidelines, and strategy/question style selection.
    """
    @staticmethod
    def build_system_prompt(role: str, company_name: str, difficulty: str, role_instructions: str, active_objective: str, active_cat: str) -> str:
        """
        Builds the complete system prompt instructions string formatted for Gemini.
        
        Args:
            role (str): Role title (e.g., 'AI Engineer', 'Backend Developer').
            company_name (str): Target company name.
            difficulty (str): Interview target difficulty level ('easy', 'medium', 'hard').
            role_instructions (str): Guidelines tailored to the specific role profile.
            active_objective (str): Current active objective name.
            active_cat (str): Current active category ('project', 'technical', 'behavioral').
            
        Returns:
            str: System prompt text containing verbal rules, answer evaluation rubric, strategy routing rules, and JSON response schema.
        """
        return (
            f"You are an expert technical interviewer conducting a mock interview for a {role} position at {company_name or 'General'}.\n"
            f"Target difficulty: {difficulty}.\n"
            f"Role guidelines:\n{role_instructions}\n\n"
            "VERBAL-ONLY INTERVIEW RULES (CRITICAL):\n"
            "- This platform is ENTIRELY VERBAL. There is no code editor, drawing board, or live coding interface.\n"
            "- You MUST NEVER ask the candidate to write, output, show, or implement code, functions, queries, JSON schemas, Pydantic models, class definitions, or programming syntax.\n"
            "- Instead, you must probe implementation depth VERBALLY. Ask the candidate to explain, describe, walk through, outline, or detail their implementation verbally.\n"
            "- Examples of acceptable VERBAL probes:\n"
            "  * 'Can you describe the main fields and properties you defined in your Pydantic model?' (instead of 'Write the Pydantic model.')\n"
            "  * 'How is the routing logic implemented? Walk me through the algorithm verbally.' (instead of 'Implement this routing logic.')\n"
            "  * 'Explain how the function behaves internally and what design decisions you made.' (instead of 'Write the Python function.')\n"
            "  * 'Describe the database schema and table relationships verbally.' (instead of 'Show me the database schema.')\n\n"
            "INTERVIEWER ADAPTATION & FLUIDITY (CRITICAL):\n"
            "- Real interviewers adapt instead of escalating or repeating the same question style forever. The interview should feel technically rigorous but not punitive.\n"
            "- When the candidate states they do not know, do not remember, or are unsure of a detail (e.g. 'I don't remember the exact implementation details', 'I forgot', 'I copied it'):\n"
            "  * You MUST NOT continue demanding lower-level details or repeating coding questions of that concept.\n"
            "  * Pivot first to asking about it at a higher conceptual or architectural level verbally.\n"
            "  * If they still don't know or show gaps, accept it gracefully and move to another aspect of the project or transition to a new topic entirely.\n\n"
            "Your task is to analyze the candidate's last answer and generate the next question. You must perform the following tasks:\n\n"
            "1. Answer Analysis:\n"
            "   - Rate the candidate's last answer overall (1 to 5) as 'score'.\n"
            "   - Rate the answer's depth (1-5) as 'depth_score'.\n"
            "   - Rate the answer's specificity (1-5) as 'specificity_score'.\n"
            "   - Assess the evidence strength as one of: 'strong', 'moderate', 'weak', or 'none'.\n"
            "   - Provide a one-sentence 'evaluation' and a short 'reasoning_summary'.\n"
            "   - Identify which technical concepts were covered/partially covered/missed in the response under 'concept_coverage_updates'.\n"
            "   - Extract any new technical claims, decisions, or projects mentioned under 'extracted_claims'.\n"
            "   - Map which evidence categories ('architecture', 'debugging', 'tradeoffs', 'implementation', 'scaling') were demonstrated for the objectives in 'evidence_categories_detected' as a dictionary of categories and their strengths ('strong', 'moderate', 'weak', 'none').\n"
            "   - If discussing a project, identify which project categories ('architecture', 'implementation', 'tradeoffs', 'debugging') were demonstrated in 'project_categories_demonstrated' as a dictionary of categories and their strengths ('strong', 'moderate', 'weak', 'none').\n"
            "   - If any new projects are mentioned, return them in 'new_projects'.\n\n"
            "2. Strategy Decision:\n"
            "   - Choose the next strategy action ('PROBE_DEEPER', 'CHALLENGE_CLAIM', 'ASK_CLARIFICATION', 'REQUEST_EXAMPLE', 'MOVE_TO_NEW_TOPIC') under 'strategy_action'.\n"
            "   - Choose the next 'question_style'. It MUST be one of:\n"
            "     - 'architecture': System components, cyclic graph layout, routing nodes.\n"
            "     - 'implementation': State structures, prompts, schemas, functions, database fields, node logic.\n"
            "     - 'tradeoff': Latency, cost, accuracy, or other quantified constraints.\n"
            "     - 'debugging': Failure logs, testing workflows, validation methods.\n"
            "     - 'scaling': Rate limits, high throughput, load distribution.\n"
            "     - 'failure_analysis': Counterfactual questions such as 'What happens if component X fails?', 'What limitations did you observe?', or 'What failure cases did you handle?'.\n"
            "     - 'design_choice': Decision alternatives like 'Why choose framework/pattern X instead of alternative Y?'.\n"
            "   - Choose the next 'question_bucket'. It MUST be one of: 'Project', 'Technical Skill', 'System Design', 'Behavioral'.\n"
            "     * BUCKET SELECTION RULE:\n"
            f"       - The active_objective is '{active_objective}' which has category '{active_cat}'.\n"
            f"       - If the category is 'project', you MUST select 'Project'.\n"
            f"       - If the category is 'behavioral', you MUST select 'Behavioral'.\n"
            f"       - If the category is 'technical', you MUST select either 'Technical Skill' or 'System Design'. Select the one that matches the technical depth/focus of the question, and review 'last_3_buckets' to avoid repeating the same bucket consecutively if possible.\n"
            "     * BUCKET DIVERSITY PENALTY: Review the 'last_3_buckets' array. You must avoid repeating the same bucket consecutively if possible. Prioritize rotating to a different bucket to make the interview realistic and diverse.\n"
            "   - Apply these Routing & Selection Rules:\n"
            "     * STRICT STYLE ROUTING: If both 'architecture' and 'implementation' are listed in the project_investigation's 'verified_categories', you MUST select one of: 'tradeoff', 'failure_analysis', or 'design_choice'. Do NOT ask architecture or implementation questions.\n"
            "     * STYLE DIVERSITY PENALTY: Review the 'last_3_styles' array. You must avoid repeating the same style consecutively. Penalize any style listed in 'last_3_styles' and actively choose a different style.\n"
            "     * IMPLEMENTATION-DETAIL CHALLENGE (Buzzword Mode): Check if the candidate's last answer contains high-level buzzwords (e.g., 'evaluation agent', 'confidence score', 'workflow', 'objective', 'pipeline') but lacks concrete details (e.g., prompts, state fields, node logic, schemas, functions). If so:\n"
            "       - Rate 'specificity_score' as 1 or 2, and 'evidence_strength' as 'weak' or 'none'.\n"
            "       - Choose strategy_action = 'CHALLENGE_CLAIM' or 'PROBE_DEEPER'.\n"
            "       - Choose question_style = 'implementation' or 'design_choice'.\n"
            "       - Ask a question specifically demanding concrete details (e.g., schema fields, database tables, prompts, or exact node execution logic).\n"
            "   - Explain the transition reason in 'reason_for_next_question'.\n\n"
            "3. Question Generation:\n"
            "   - Generate the 'next_question' based on the phase, active objective, active claim, strategy_action, and selected question_style.\n"
            "   - Guidelines based on Phase:\n"
            "     - INTRODUCTION: Welcoming candidate and wrapping up introduction.\n"
            "     - PROJECT_DISCOVERY: Prompt the candidate to walk through their most relevant technical project, its architecture, and their contribution.\n"
            "     - TECHNICAL_EVALUATION: Deep-dive technical evaluation probing concepts, tradeoffs, debugging, implementation, and scaling.\n"
            "     - WRAP_UP: Polite closing message thanking the candidate.\n"
            "   - Follow these rules:\n"
            "     - Ask exactly one main question, with at most one short follow-up clause.\n"
            "     - Formulate it to be concise (max 3 sentences) and suitable for a spoken conversation.\n"
            "     - Tie it to the resume/JD context, active claim, or active objective.\n"
            "     - Do not reveal the rubric, phase, or expected concepts to the candidate.\n"
            "   - List 2-3 specific 'expected_concepts' (technical terms like 'Transformers', 'PyTorch', etc.) required to answer it successfully. Do NOT include high-level objectives (e.g. 'Project Ownership'), general evaluation rubrics, or generic categories (e.g. 'tradeoffs', 'implementation details').\n\n"
            "You MUST respond with a raw JSON object matching this schema:\n"
            "{\n"
            "  \"score\": <Integer 1-5>,\n"
            "  \"depth_score\": <Integer 1-5>,\n"
            "  \"specificity_score\": <Integer 1-5>,\n"
            "  \"evidence_strength\": \"strong | moderate | weak | none\",\n"
            "  \"evaluation\": \"One-sentence analysis.\",\n"
            "  \"reasoning_summary\": \"Short critique.\",\n"
            "  \"concept_coverage_updates\": {\n"
            "     \"ConceptName\": \"covered | partially_covered | missed\"\n"
            "  },\n"
            "  \"extracted_claims\": [\n"
            "     {\n"
            "        \"claim\": \"...\",\n"
            "        \"decision\": \"...\",\n"
            "        \"project\": \"...\"\n"
            "     }\n"
            "  ],\n"
            "  \"evidence_categories_detected\": {\n"
            "     \"ObjectiveName\": {\n"
            "        \"architecture\": \"strong | moderate | weak | none\",\n"
            "        \"debugging\": \"strong | moderate | weak | none\",\n"
            "        \"tradeoffs\": \"strong | moderate | weak | none\",\n"
            "        \"implementation\": \"strong | moderate | weak | none\",\n"
            "        \"scaling\": \"strong | moderate | weak | none\"\n"
            "     }\n"
            "  },\n"
            "  \"project_categories_demonstrated\": {\n"
            "     \"architecture\": \"strong | moderate | weak | none\",\n"
            "     \"implementation\": \"strong | moderate | weak | none\",\n"
            "     \"tradeoffs\": \"strong | moderate | weak | none\",\n"
            "     \"debugging\": \"strong | moderate | weak | none\"\n"
            "  },\n"
            "  \"new_projects\": [\"...\"],\n"
            "  \"strategy_action\": \"PROBE_DEEPER | CHALLENGE_CLAIM | ASK_CLARIFICATION | REQUEST_EXAMPLE | MOVE_TO_NEW_TOPIC\",\n"
            "  \"question_style\": \"architecture | implementation | tradeoff | debugging | scaling | failure_analysis | design_choice\",\n"
            "  \"question_bucket\": \"Project | Technical Skill | System Design | Behavioral\",\n"
            "  \"reason_for_next_question\": \"Why this question is next.\",\n"
            "  \"next_question\": \"...\",\n"
            "  \"expected_concepts\": [\"concept1\", \"concept2\", ...]\n"
            "}"
        )


class PhaseManager:
    """
    Manages interview phase progression (INTRODUCTION -> PROJECT_DISCOVERY -> TECHNICAL_EVALUATION -> WRAP_UP).
    
    Phases guide the global focus of the interview:
      - INTRODUCTION: Initial greeting and self-introduction.
      - PROJECT_DISCOVERY: High-level walkthrough of candidate projects.
      - TECHNICAL_EVALUATION: Deep technical probing of skills, tradeoffs, implementation, and scaling.
      - WRAP_UP: Concluding questions and interview completion.
    """

    @staticmethod
    def _base_transition(
        current_phase: str,
        candidate_answers_count: int,
        project_investigation: dict,
        project_turns_spent: dict,
        objective_turns_spent: dict,
        max_project_turns: int,
        max_turns: int,
    ) -> str:
        """
        Internal transition logic shared across pre-assessment and post-assessment checks.
        Advances phase based on turn limits and architecture verification status.
        """
        phase = current_phase

        # Transition 1: INTRODUCTION -> PROJECT_DISCOVERY after candidate's initial answer
        if phase == "INTRODUCTION" and candidate_answers_count >= 1:
            phase = "PROJECT_DISCOVERY"

        # Transition 2: PROJECT_DISCOVERY -> TECHNICAL_EVALUATION once project architecture is verified or turn limit reached
        if phase == "PROJECT_DISCOVERY":
            proj_name = project_investigation.get("project_name")
            arch_verified = (
                project_investigation.get("verification_plan", {}).get("architecture", False)
            )
            proj_turns = (
                project_turns_spent.get(proj_name, 0) if proj_name else 0
            )
            po_turns = objective_turns_spent.get("Project Ownership", 0)

            if (proj_name and arch_verified) or proj_turns >= max_project_turns or po_turns >= max_turns:
                phase = "TECHNICAL_EVALUATION"

        return phase

    @staticmethod
    def transition_before_assessment(
        current_phase: str,
        candidate_answers_count: int,
        project_investigation: dict,
        project_turns_spent: dict,
        objective_turns_spent: dict,
        max_project_turns: int,
        max_turns: int,
        all_objectives_verified: bool,
        q_count: int,
        max_q: int,
    ) -> str:
        """
        Determines the interview phase PRIOR to sending the candidate's latest answer to Gemini.
        Triggers WRAP_UP early if all objectives are verified or max question limit is reached.
        """
        phase = PhaseManager._base_transition(
            current_phase=current_phase,
            candidate_answers_count=candidate_answers_count,
            project_investigation=project_investigation,
            project_turns_spent=project_turns_spent,
            objective_turns_spent=objective_turns_spent,
            max_project_turns=max_project_turns,
            max_turns=max_turns,
        )

        # Stop if interview limit reached or objectives complete
        if all_objectives_verified or q_count >= max_q:
            phase = "WRAP_UP"

        return phase

    @staticmethod
    def transition_after_assessment(
        current_phase: str,
        candidate_answers_count: int,
        project_investigation: dict,
        project_turns_spent: dict,
        objective_turns_spent: dict,
        max_project_turns: int,
        max_turns: int,
        all_objectives_verified_now: bool,
    ) -> str:
        """
        Determines the interview phase AFTER Gemini evaluates the candidate's latest answer.
        Checks if the latest answer successfully verified all remaining objectives.
        """
        phase = PhaseManager._base_transition(
            current_phase=current_phase,
            candidate_answers_count=candidate_answers_count,
            project_investigation=project_investigation,
            project_turns_spent=project_turns_spent,
            objective_turns_spent=objective_turns_spent,
            max_project_turns=max_project_turns,
            max_turns=max_turns,
        )

        # Gemini may have completed objective verification on this turn
        if all_objectives_verified_now:
            phase = "WRAP_UP"

        return phase


class ObjectiveSelector:
    """
    Selects the next active objective to target based on interview targets, category balance, and turns spent.
    """
    @staticmethod
    def get_objective_category(obj_name: str) -> str:
        """
        Categorizes an objective name into one of three primary categories: 'project', 'behavioral', or 'technical'.
        """
        name_lower = obj_name.lower()
        if "ownership" in name_lower or "project" in name_lower:
            return "project"
        elif "behavioral" in name_lower or "communication" in name_lower or "leadership" in name_lower:
            return "behavioral"
        else:
            return "technical"

    @staticmethod
    def select_active_objective(
        current_phase: str,
        interview_objectives: dict,
        objective_turns_spent: dict,
        knowledge_model: dict,
        max_turns: int,
        q_count: int,
        max_q: int,
        category_counts: dict,
        targets: dict,
        differences: dict
    ) -> str:
        """
        Calculates ranking scores for unverified objectives and picks the best objective based on category deficit.
        
        Args:
            current_phase (str): Active interview phase.
            interview_objectives (dict): Must-verify and nice-to-verify objective maps.
            objective_turns_spent (dict): Count of turns spent per objective.
            knowledge_model (dict): Model containing candidate proven/weak skills and claims.
            max_turns (int): Max turns allowed per objective.
            q_count (int): Current question count.
            max_q (int): Maximum questions allowed for the session.
            category_counts (dict): Number of questions asked in each category ('project', 'technical', 'behavioral').
            targets (dict): Target percentage allocations for categories (e.g. {'project': 0.4, ...}).
            differences (dict): Deficit differences between target allocations and actual counts.
            
        Returns:
            str: Name of the selected active objective.
        """
        # Phase-based hardcoded overrides
        if current_phase == "INTRODUCTION":
            return "Project Ownership"
        elif current_phase == "PROJECT_DISCOVERY":
            return "Project Ownership"
        elif current_phase == "WRAP_UP":
            return "Behavioral & Communication"
            
        must_list = interview_objectives.get("must_verify", {})
        nice_list = interview_objectives.get("nice_to_verify", {})
        weak_skills = knowledge_model.get("weak_skills", [])
        
        unverified_objs = []
        # Rank objectives by status, turn limits, and candidate weak skills
        for group_name, group in [("must_verify", must_list), ("nice_to_verify", nice_list)]:
            for obj_name, obj_data in group.items():
                status = obj_data.get("status", "unverified") if isinstance(obj_data, dict) else obj_data
                if status != "verified":
                    cat = ObjectiveSelector.get_objective_category(obj_name)
                    turns = objective_turns_spent.get(obj_name, 0)
                    conf = obj_data.get("confidence", 0) if isinstance(obj_data, dict) else 0
                    
                    limit = max_turns + 1 if conf < 20 else max_turns
                    exceeded = (turns >= limit)
                    is_weak = any(ws.lower() in obj_name.lower() or obj_name.lower() in ws.lower() for ws in weak_skills)
                    
                    # Compute priority rank (1 = highest priority, 4 = lowest)
                    if not exceeded and not is_weak:
                        rank = 1
                    elif not exceeded and is_weak:
                        rank = 2
                    elif exceeded and not is_weak:
                        rank = 3
                    else:
                        rank = 4
                        
                    unverified_objs.append({
                        "name": obj_name,
                        "category": cat,
                        "rank": rank,
                        "group": group_name,
                        "turns": turns
                    })
                    
        # Filter candidate objectives to non-exceeded items (ranks 1 & 2)
        non_exceeded_objs = [o for o in unverified_objs if o["rank"] in [1, 2]]
        candidate_objs = non_exceeded_objs if non_exceeded_objs else unverified_objs
        
        selected_obj = None
        
        # Rule: If last question is approaching and behavioral target budget hasn't been touched, force behavioral
        if q_count == max_q - 1 and targets.get("behavioral", 0.0) > 0.0 and category_counts.get("behavioral", 0) == 0:
            behavioral_objs = [o for o in candidate_objs if o["category"] == "behavioral"]
            if behavioral_objs:
                selected_obj = behavioral_objs[0]["name"]
                
        # Pick objective from category with highest target deficit (biggest difference)
        if not selected_obj:
            available_categories = set(o["category"] for o in candidate_objs)
            best_category = None
            if available_categories:
                sorted_diffs = sorted(
                    [(cat, differences[cat]) for cat in available_categories],
                    key=lambda x: x[1],
                    reverse=True
                )
                best_category = sorted_diffs[0][0]
                
            if best_category:
                cat_objs = [o for o in candidate_objs if o["category"] == best_category]
                cat_objs.sort(key=lambda x: (x["rank"], 0 if x["group"] == "must_verify" else 1))
                if cat_objs:
                    selected_obj = cat_objs[0]["name"]
                    
        # Fallback selection sorted by rank and group
        if not selected_obj:
            candidate_objs.sort(key=lambda x: (x["rank"], 0 if x["group"] == "must_verify" else 1))
            if candidate_objs:
                selected_obj = candidate_objs[0]["name"]
                
        return selected_obj or "Project Ownership"


class ClaimSelector:
    """
    Selects candidate technical claims from the Knowledge Model for verification or deep probing.
    """
    @staticmethod
    def select_active_claim(knowledge_model: dict, weak_skills: list) -> Optional[str]:
        """
        Finds the first candidate claim in PROBED or UNVERIFIED state, excluding known weak skills.
        
        Returns:
            Optional[str]: Selected claim text, or None if no valid claim is available.
        """
        active_claim = None
        claims_list = knowledge_model.get("claims") or knowledge_model.get("unproven_claims") or []
        weak_skills_lower = [ws.lower() for ws in weak_skills]
        for claim in claims_list:
            if claim.get("state") in ["PROBED", "UNVERIFIED"]:
                if claim.get("claim", "").lower() in weak_skills_lower:
                    continue
                active_claim = claim.get("claim")
                break
        return active_claim


class ResponseProcessor:
    """
    Parses and sanitizes LLM JSON output responses.
    """
    @staticmethod
    def parse_gemini_response(content: str) -> dict:
        """
        Delegates parsing of raw LLM text to `parse_json_content`.
        """
        return parse_json_content(content)



class StateUpdater:
    """
    Updates graph state objects including candidate weak skills, concept coverage,
    objective confidence scores, claim knowledge base, project investigation progress,
    and adaptive difficulty scaling.
    """
    @staticmethod
    def accumulate_failed_attempts(
        score_val: Optional[int],
        evidence_strength: str,
        last_question_concepts: list,
        failed_attempts_per_concept: dict,
        knowledge_model: dict,
        concept_coverage: dict
    ):
        """
        Tracks consecutive low scores or weak evidence for probed concepts.
        If a concept receives 2 or more failed attempts, it is added to weak_skills.
        
        Args:
            score_val (Optional[int]): Overall answer score (1-5).
            evidence_strength (str): Evaluated strength ('strong', 'moderate', 'weak', 'none').
            last_question_concepts (list): Technical concepts evaluated in the latest question.
            failed_attempts_per_concept (dict): Counter dictionary tracking failed attempts per concept.
            knowledge_model (dict): Model containing candidate proven/weak skills and claims.
            concept_coverage (dict): Status map for technical concepts.
        """
        if score_val is not None and (score_val <= 2 or evidence_strength in ["none", "weak"]):
            # Filter out high-level meta objective labels
            filtered_concepts = [
                c for c in last_question_concepts 
                if c.lower() not in [
                    "tradeoffs", "implementation details", "project ownership", 
                    "system understanding", "decision & tradeoff thinking", 
                    "scaling & production thinking", "behavioral & communication", 
                    "problem solving & debugging"
                ]
            ]
            for concept in filtered_concepts:
                failed_attempts_per_concept[concept] = failed_attempts_per_concept.get(concept, 0) + 1
                # Threshold: 2 failed attempts -> mark as candidate weak skill
                if failed_attempts_per_concept[concept] >= 2:
                    if concept not in knowledge_model.setdefault("weak_skills", []):
                        knowledge_model["weak_skills"].append(concept)
                    if concept in concept_coverage:
                        concept_coverage[concept] = "partially_covered"
        else:
            # Reset failure count for successfully answered concepts
            for concept in last_question_concepts:
                if concept in failed_attempts_per_concept:
                    failed_attempts_per_concept[concept] = 0

    @staticmethod
    def update_concept_coverage(concept_coverage: dict, concept_updates: dict):
        """
        Updates concept coverage dictionary based on Gemini evaluation ('covered', 'partially_covered', 'missed').
        """
        for c, status in concept_updates.items():
            if c in concept_coverage:
                concept_coverage[c] = status

    @staticmethod
    def update_objectives_confidence(
        interview_objectives: dict,
        active_objective: str,
        evidence_categories_detected: dict,
        STRENGTH_VALUES: dict,
        WEIGHTS: dict
    ):
        """
        Recalculates objective confidence percentage (0-100%) based on detected evidence categories.
        
        Evaluates 5 evidence dimensions for each objective:
          - architecture (weight 20)
          - debugging (weight 20)
          - tradeoffs (weight 20)
          - implementation (weight 20)
          - scaling (weight 20)
          
        Marks objective as 'verified' when confidence reaches 80% with at least 2 probing attempts.
        """
        for obj_key in ["must_verify", "nice_to_verify"]:
            if obj_key in interview_objectives:
                for obj_name, obj_data in interview_objectives[obj_key].items():
                    # Initialize default objective data structure if missing
                    if not isinstance(obj_data, dict):
                        obj_data = {
                            "confidence": 0,
                            "status": "unverified",
                            "attempts": 0,
                            "evidence_categories": {
                                "architecture": "none",
                                "debugging": "none",
                                "tradeoffs": "none",
                                "implementation": "none",
                                "scaling": "none"
                            }
                        }
                        interview_objectives[obj_key][obj_name] = obj_data
                        
                    # Sanitize legacy boolean values in evidence categories
                    old_ec = obj_data.setdefault("evidence_categories", {})
                    cleaned_ec = {}
                    for cat in ["architecture", "debugging", "tradeoffs", "implementation", "scaling"]:
                        val = old_ec.get(cat, "none")
                        if val is True:
                            cleaned_ec[cat] = "strong"
                        elif val is False or val is None:
                            cleaned_ec[cat] = "none"
                        else:
                            cleaned_ec[cat] = val
                    obj_data["evidence_categories"] = cleaned_ec
                    
                    # Update category strength if higher strength detected
                    detected_cats = evidence_categories_detected.get(obj_name, {})
                    if isinstance(detected_cats, dict):
                        for cat, strength in detected_cats.items():
                            if cat in obj_data["evidence_categories"] and strength in STRENGTH_VALUES:
                                old_strength = obj_data["evidence_categories"][cat]
                                if STRENGTH_VALUES[strength] > STRENGTH_VALUES.get(old_strength, 0):
                                    obj_data["evidence_categories"][cat] = strength
                    elif isinstance(detected_cats, list):
                        for cat in detected_cats:
                            if cat in obj_data["evidence_categories"]:
                                obj_data["evidence_categories"][cat] = "strong"
                                
                    # Calculate aggregate confidence score (max 100%)
                    confidence_val = sum(WEIGHTS.get(strength, 0) for strength in obj_data["evidence_categories"].values())
                    obj_data["confidence"] = min(100, confidence_val)
                    
                    # Check verification threshold
                    attempts_count = obj_data.get("attempts", 0)
                    if confidence_val >= 80 and attempts_count >= 2:
                        obj_data["status"] = "verified"
                    else:
                        obj_data["status"] = "unverified"

    @staticmethod
    def update_claims_knowledge_base(
        knowledge_model: dict,
        extracted_claims: list,
        active_claim: Optional[str],
        project_categories_demonstrated: Any,
        evidence_categories_detected: dict,
        evidence_strength: str,
        score_val: Optional[int],
        q_count: int = 1
    ):
        """
        Registers newly extracted technical claims into the knowledge model and tracks their verification state.
        
        Claims transition from UNVERIFIED -> VERIFIED (if required evidence criteria are met)
        or -> FAILED_VERIFICATION (if candidate fails verification twice).
        """
        def _get_required_evidence_for_claim(claim_text: str) -> list:
            """Determines required evidence types (debugging, scaling, tradeoffs, architecture, implementation) for a claim."""
            claim_lower = claim_text.lower()
            if any(kw in claim_lower for kw in ["debug", "test", "error", "log"]):
                return ["debugging"]
            elif any(kw in claim_lower for kw in ["scale", "performance", "load", "rate limit"]):
                return ["scaling"]
            elif any(kw in claim_lower for kw in ["tradeoff", "cost", "latency"]):
                return ["tradeoffs"]
            elif any(kw in claim_lower for kw in ["built", "designed", "architecture"]):
                return ["architecture", "implementation"]
            else:
                return ["implementation"]

        claims_list = knowledge_model.get("claims") or knowledge_model.get("unproven_claims") or []
        
        # 1. Append newly extracted claims from Gemini response
        for ec in extracted_claims:
            claim_text = ec.get("claim", "")
            if claim_text:
                exists = False
                for existing in claims_list:
                    if existing.get("claim", "").lower() == claim_text.lower():
                        exists = True
                        break
                if not exists:
                    claims_list.append({
                        "claim": claim_text,
                        "decision": ec.get("decision", ""),
                        "project": ec.get("project", "General"),
                        "state": "UNVERIFIED",
                        "required_evidence": _get_required_evidence_for_claim(claim_text),
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
                    })
                    
        # 2. Update status and evidence coverage for existing claims
        for claim_item in claims_list:
            if "required_evidence" not in claim_item:
                claim_item["required_evidence"] = _get_required_evidence_for_claim(claim_item.get("claim", ""))
            if "verified_evidence" not in claim_item:
                claim_item["verified_evidence"] = []
            if "attempts" not in claim_item:
                claim_item["attempts"] = 0
            if "evidence_coverage" not in claim_item:
                claim_item["evidence_coverage"] = {
                    "architecture": "Missing",
                    "implementation": "Missing",
                    "tradeoffs": "Missing",
                    "debugging": "Missing",
                    "scaling": "Missing"
                }
            if "supporting_turns" not in claim_item:
                claim_item["supporting_turns"] = []
            if "confidence" not in claim_item:
                claim_item["confidence"] = 0
                
            # Focus on active claim targeted in this turn
            if claim_item.get("claim") == active_claim:
                claim_item["attempts"] += 1
                
                current_cats = []
                project_categories = {}
                if isinstance(project_categories_demonstrated, dict):
                    project_categories = project_categories_demonstrated
                elif isinstance(project_categories_demonstrated, list):
                    for cat in project_categories_demonstrated:
                        project_categories[cat] = "strong"
                        
                for cat, strength in project_categories.items():
                    if strength in ["moderate", "strong"]:
                        current_cats.append(cat)
                        claim_item["evidence_coverage"][cat] = "Strong" if strength == "strong" else "Moderate"
                        
                for obj_name, detected_cats in evidence_categories_detected.items():
                    if isinstance(detected_cats, dict):
                        for cat, strength in detected_cats.items():
                            if strength in ["moderate", "strong"]:
                                if cat not in current_cats:
                                    current_cats.append(cat)
                                current_strength = claim_item["evidence_coverage"].get(cat, "Missing")
                                if strength == "strong" or current_strength == "Missing":
                                    claim_item["evidence_coverage"][cat] = "Strong" if strength == "strong" else "Moderate"
                    elif isinstance(detected_cats, list):
                        for cat in detected_cats:
                            if cat not in current_cats:
                                current_cats.append(cat)
                            if claim_item["evidence_coverage"].get(cat) == "Missing":
                                claim_item["evidence_coverage"][cat] = "Strong"
                                
                new_evidence_found = False
                for cat in current_cats:
                    if cat in claim_item["required_evidence"] and cat not in claim_item["verified_evidence"]:
                        claim_item["verified_evidence"].append(cat)
                        new_evidence_found = True
                        
                if new_evidence_found or current_cats:
                    # Add question turn if new evidence found or current categories
                    q_label = f"Question {q_count}"
                    if q_label not in claim_item["supporting_turns"]:
                        claim_item["supporting_turns"].append(q_label)
                        
                req_len = len(claim_item["required_evidence"])
                ver_len = len(claim_item["verified_evidence"])
                if req_len > 0:
                    claim_item["confidence"] = int((ver_len / req_len) * 100)
                else:
                    claim_item["confidence"] = 100
                    
                all_req_verified = all(c in claim_item["verified_evidence"] for c in claim_item["required_evidence"])
                if all_req_verified:
                    claim_item["state"] = "VERIFIED"
                    if claim_item["claim"] not in knowledge_model.setdefault("proven_skills", []):
                        knowledge_model["proven_skills"].append(claim_item["claim"])
                elif claim_item["attempts"] >= 2:
                    if evidence_strength in ["none", "weak"] or (score_val is not None and score_val <= 2):
                        claim_item["state"] = "FAILED_VERIFICATION"
                        if claim_item["claim"] not in knowledge_model.setdefault("weak_skills", []):
                            knowledge_model["weak_skills"].append(claim_item["claim"])
                else:
                    claim_item["state"] = "UNVERIFIED"
                    
        knowledge_model["claims"] = claims_list
        knowledge_model["unproven_claims"] = claims_list

    @staticmethod
    def update_project_investigation(
        project_investigation: dict,
        new_projects: list,
        active_cat: str,
        max_project_turns: int,
        project_turns_spent: dict,
        project_categories_demonstrated: Any,
        question_style: str,
        evidence_strength: str
    ):
        """
        Manages state tracking when performing a deep dive on a specific candidate project.
        Tracks verification across 5 project dimensions: architecture, implementation, tradeoffs, debugging, failure_cases.
        """
        # Initiate project mode if new project introduced under 'project' category
        if new_projects and not project_investigation.get("in_mode") and active_cat == "project":
            proj_name = new_projects[0]
            if project_turns_spent.get(proj_name, 0) < max_project_turns:
                project_investigation["in_mode"] = True
                project_investigation["project_name"] = proj_name
                project_investigation["verified_categories"] = []
                project_investigation["turns_spent"] = 0
                project_investigation["verification_plan"] = {
                    "architecture": False,
                    "implementation": False,
                    "debugging": False,
                    "tradeoffs": False,
                    "failure_cases": False
                }
        elif project_investigation.get("in_mode"):
            proj_name = project_investigation.get("project_name")
            project_turns_spent[proj_name] = project_turns_spent.get(proj_name, 0) + 1
            project_investigation["turns_spent"] += 1
            
            project_categories = {}
            if isinstance(project_categories_demonstrated, dict):
                project_categories = project_categories_demonstrated
            elif isinstance(project_categories_demonstrated, list):
                for cat in project_categories_demonstrated:
                    project_categories[cat] = "strong"
                    
            # Mark categories as verified when candidate demonstrates moderate/strong evidence
            for cat, strength in project_categories.items():
                if cat in ["architecture", "implementation", "tradeoffs", "debugging"]:
                    if strength in ["moderate", "strong"]:
                        project_investigation.setdefault("verification_plan", {})[cat] = True
                        if cat not in project_investigation.setdefault("verified_categories", []):
                            project_investigation["verified_categories"].append(cat)
                            
            if (project_categories.get("failure_cases") in ["moderate", "strong"] or 
                project_categories.get("failure_analysis") in ["moderate", "strong"] or
                (question_style == "failure_analysis" and evidence_strength in ["moderate", "strong"])):
                project_investigation.setdefault("verification_plan", {})["failure_cases"] = True

            # Exit project mode when all required categories are verified or project turn limit reached
            req_cats = ["architecture", "implementation", "tradeoffs", "debugging"]
            all_verified = all(project_investigation.setdefault("verification_plan", {}).get(c, False) for c in req_cats)
            if all_verified or project_turns_spent.get(proj_name, 0) >= max_project_turns:
                project_investigation["in_mode"] = False
                project_investigation["project_name"] = None

    @staticmethod
    def adjust_adaptive_difficulty(state: InterviewState, score_val: Optional[int], current_difficulty: str) -> str:
        """
        Dynamically adjusts interview difficulty level ('easy', 'medium', 'hard')
        based on the rolling average of the candidate's last 3 answer scores.
        
        Rules:
          - Rolling avg >= 4.0: Level up (easy -> medium, medium -> hard)
          - Rolling avg <= 2.5: Level down (hard -> medium, medium -> easy)
        """
        hist = state.get("score_history", [])
        difficulty = current_difficulty
        if score_val is not None:
            hist = hist + [score_val]
        if len(hist) >= 3:
            last_3 = hist[-3:]
            avg_score = sum(last_3) / 3
            if avg_score >= 4.0:
                if difficulty == "easy":
                    difficulty = "medium"
                elif difficulty == "medium":
                    difficulty = "hard"
            elif avg_score <= 2.5:
                if difficulty == "hard":
                    difficulty = "medium"
                elif difficulty == "medium":
                    difficulty = "easy"
        return difficulty


class ContextBuilder:
    """
    Constructs the token-optimized context window payload sent to Gemini for each interview turn.
    """
    @staticmethod
    def build_active_context(
        role: str,
        company_name: str,
        difficulty: str,
        current_phase: str,
        active_objective: str,
        active_claim: Optional[str],
        project_investigation: dict,
        project_name: Optional[str],
        resume_projects: list,
        jd_skills: list,
        messages: list,
        last_3_styles: list,
        last_3_buckets: list,
        knowledge_model: dict,
        concept_coverage: dict,
        blueprint_json: Optional[dict],
        personalization_context: Optional[dict]
    ) -> dict:
        """
        Builds a dynamic sliding-window context dictionary targeting ~1500 tokens (6000 chars).
        
        Includes recent conversation messages, active objective state, verified/weak skills,
        and context reduction performance metrics.
        """
        # Dynamic sliding window setup (min 4 messages/2 turns, max 8 messages/4 turns)
        min_messages = 4
        max_messages = 8
        target_char_budget = 6000
        
        selected_messages = messages[-min_messages:] if len(messages) >= min_messages else messages[:]
        
        # Expand window if character budget permits
        current_len = sum(len(m.content) for m in selected_messages)
        if current_len < target_char_budget and len(messages) > min_messages:
            for num_msgs in range(min_messages + 2, max_messages + 1, 2):
                if num_msgs <= len(messages):
                    candidate_subset = messages[-num_msgs:]
                    subset_len = sum(len(m.content) for m in candidate_subset)
                    if subset_len <= target_char_budget:
                        selected_messages = candidate_subset
                    else:
                        break
                        
        recent_history = []
        for msg in selected_messages:
            sender = "Interviewer" if isinstance(msg, AIMessage) else "Candidate"
            recent_history.append({"sender": sender, "text": msg.content})
            
        # Current candidate answer is the last message in history
        current_answer = messages[-1].content if messages else ""
        
        # Token Savings Estimation
        turns_included = len(recent_history) // 2
        total_turns = len(messages) // 2
        
        full_history_str = "\n".join([m.content for m in messages])
        recent_history_str = "\n".join([h["text"] for h in recent_history])
        
        approx_full_tokens = len(full_history_str) // 4
        approx_recent_tokens = len(recent_history_str) // 4
        token_savings = max(0, approx_full_tokens - approx_recent_tokens)
        reduction_percentage = 0.0
        if approx_full_tokens > 0:
            reduction_percentage = round((token_savings / approx_full_tokens) * 100, 1)
            
        context = {
            "role": role,
            "company_name": company_name,
            "difficulty": difficulty,
            "phase": current_phase,
            "active_objective": active_objective,
            "active_claim": active_claim,
            "project_investigation": {
                "in_mode": project_investigation.get("in_mode", False),
                "project_name": project_name,
                "verified_categories": project_investigation.get("verified_categories", []),
                "verification_plan": project_investigation.get("verification_plan", {})
            },
            "resume_projects": resume_projects,
            "jd_skills": jd_skills,
            "recent_turns": recent_history,
            "last_question": messages[-2].content if len(messages) >= 2 else "",
            "last_answer": current_answer,
            "last_3_styles": last_3_styles,
            "last_3_buckets": last_3_buckets,
            "knowledge_model": {
                "proven_skills": knowledge_model.get("proven_skills", []),
                "weak_skills": knowledge_model.get("weak_skills", []),
                "claims": knowledge_model.get("claims") or knowledge_model.get("unproven_claims") or []
            },
            "concept_coverage": concept_coverage,
            "blueprint": blueprint_json,
            "personalization_context": personalization_context,
            "context_metrics": {
                "context_tokens": approx_recent_tokens,
                "context_reduction_percent": reduction_percentage,
                "turns_included": turns_included,
                "estimated_saved_tokens": token_savings
            }
        }
        return context



# ============================================================================
# --- LangGraph Graph Builder & Core Interviewer Node ---
# Defines the state machine graph execution workflow for the interview agent.
# ============================================================================

def build_interview_graph():
    """
    Constructs and compiles the LangGraph StateGraph workflow for the mock technical interviewer.
    
    The graph consists of a single primary execution node ('interviewer') that loops
    continuously until the interview transitions to the 'WRAP_UP' phase or question budget ends.
    
    Returns:
        CompiledStateGraph: The executable LangGraph instance.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        api_key = "placeholder_api_key"
        
    # Instantiate ChatGoogleGenerativeAI using Gemini Flash Lite model configured for JSON output
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0.7,
        google_api_key=api_key,
        response_mime_type="application/json",
        max_retries=1
    )
    
    workflow = StateGraph(InterviewState)
    
    def interviewer_node(state: InterviewState):
        """
        Core node function executed on every interview turn.
        
        Execution Pipeline:
          Step 1: Extract state parameters and interview history.
          Step 2: Calculate duration budget & target category allocations (project, technical, behavioral).
          Step 3: Lazily generate interview plan (topic tree & objectives) if not already initialized.
          Step 4: Handle Turn 0 welcome greeting if conversation is starting.
          Step 5: Execute pre-assessment phase transition logic.
          Step 6: Select active objective and claim candidates.
          Step 7: Build sliding-window prompt context & system instructions.
          Step 8: Invoke Gemini LLM and parse JSON response (or execute fallback on error).
          Step 9: Run StateUpdater pipeline (accumulate failures, update coverage, re-evaluate confidence & claims).
          Step 10: Adjust adaptive difficulty based on performance history.
          Step 11: Execute post-assessment phase transition & evaluate dynamic bonus turns.
          Step 12: Assemble debug dashboard payload and return updated state.
        """
        # --- Step 1: Extract State & Configuration ---
        messages = state.get("messages", [])
        role = state.get("role", "AI Engineer")
        difficulty = state.get("difficulty", "medium")
        q_count = state.get("question_count", 0)
        max_q = state.get("max_question_count", 5)
        company_name = state.get("company_name", "Target Company")
        
        covered_topics = state.get("covered_topics", [])
        missing_topics = state.get("missing_topics", [])
        current_phase = state.get("interview_phase", "INTRODUCTION")
        
        topic_tree = state.get("topic_tree")
        concept_coverage = state.get("concept_coverage")
        interview_objectives = state.get("interview_objectives")
        
        original_max_q = state.get("original_max_question_count")
        if original_max_q is None:
            original_max_q = max_q

        question_style_history = state.get("question_style_history") or []
        last_3_styles = list(question_style_history[-3:])
        
        objective_turns_spent = state.get("objective_turns_spent") or {}
        project_turns_spent = state.get("project_turns_spent") or {}
        failed_attempts_per_concept = state.get("failed_attempts_per_concept") or {}
        question_bucket_history = state.get("question_bucket_history") or []
        last_3_buckets = list(question_bucket_history[-3:])
        category_counts = state.get("category_counts") or {
            "project": 0,
            "technical": 0,
            "behavioral": 0
        }
        
        # --- Step 2: Duration Budget Targets & Allocation Limits ---
        INTERVIEW_BUDGETS = {
           "5_min": {
              "project": 0.50,
              "technical": 0.40,
              "behavioral": 0.10
           },
           "10_min": {
              "project": 0.40,
              "technical": 0.40,
              "behavioral": 0.20
           },
           "15_min": {
              "project": 0.30,
              "technical": 0.50,
              "behavioral": 0.20
           },
           "20_min": {
              "project": 0.30,
              "technical": 0.50,
              "behavioral": 0.20
           },
           "30_min": {
              "project": 0.20,
              "technical": 0.60,
              "behavioral": 0.20
           }
        }
        
        # Map max question count to duration key and turn limits
        max_turns = 3
        max_project_turns = 3
        budget_key = "15_min"
        
        if max_q <= 5:
            max_turns = 2
            max_project_turns = 2
            budget_key = "5_min"
        elif max_q <= 10:
            max_turns = 3
            max_project_turns = 3
            budget_key = "10_min"
        elif max_q <= 15:
            max_turns = 3
            max_project_turns = 3
            budget_key = "15_min"
        else:
            max_turns = 5
            max_project_turns = 5
            budget_key = "15_min"
            
        targets = INTERVIEW_BUDGETS[budget_key]
        
        # --- Step 3: Lazy Interview Plan & Topic Tree Initialization ---
        if not topic_tree or not concept_coverage or not interview_objectives:
            personalization = state.get("personalization_context") or {}
            resume_text = personalization.get("extracted_resume", {}).get("skills", [])
            jd_text = personalization.get("extracted_jd", {}).get("required_skills", [])
            
            plan = generate_interview_plan(
                mode=state.get("mode", "role"),
                company=company_name,
                role=role,
                resume_text=str(resume_text),
                jd_text=str(jd_text)
            )
            topic_tree = plan["topic_tree"]
            concept_coverage = plan["concept_coverage"]
            interview_objectives = plan["interview_objectives"]
            
        # Ensure knowledge model and project investigation data structures exist
        knowledge_model = state.get("knowledge_model")
        if not knowledge_model:
            knowledge_model = {
                "proven_skills": [],
                "weak_skills": [],
                "claims": [],
                "unproven_claims": [],
                "understanding_styles": [],
                "evaluation_history": []
            }
        if "evaluation_history" not in knowledge_model:
            knowledge_model["evaluation_history"] = []
            
        project_investigation = state.get("project_investigation")
        if not project_investigation:
            project_investigation = {
                "in_mode": False,
                "project_name": None,
                "verified_categories": [],
                "turns_spent": 0,
                "verification_plan": {
                    "architecture": False,
                    "implementation": False,
                    "debugging": False,
                    "tradeoffs": False,
                    "failure_cases": False
                }
            }
        if "verified_categories" not in project_investigation:
            project_investigation["verified_categories"] = []
        if "verification_plan" not in project_investigation:
            project_investigation["verification_plan"] = {
                "architecture": False,
                "implementation": False,
                "debugging": False,
                "tradeoffs": False,
                "failure_cases": False
            }
            
        last_question_concepts = state.get("last_question_concepts") or []
        profile = ROLE_PROFILES.get(role, ROLE_PROFILES["AI Engineer"])
        personalization_context = state.get("personalization_context")
        
        # --- Step 4: Turn 0 Initial Greeting & Self-Introduction ---
        if not messages:
            next_question = (
                f"Welcome to your mock technical interview for the {role} role at {company_name}. "
                "To start off, could you please introduce yourself and walk me through your professional background?"
            )
            return {
                "current_question": next_question,
                "question_count": 1,
                "covered_topics": [],
                "missing_topics": missing_topics,
                "score_history": [],
                "messages": [AIMessage(content=next_question)],
                "evaluation": "N/A",
                "reasoning_summary": "Interview start",
                "score": None,
                "primary_topic": "Introduction",
                "secondary_topics": [],
                "action": "INTRODUCTION",
                "status": "in_progress",
                "company_name": company_name,
                "topic_tree": topic_tree,
                "knowledge_model": knowledge_model,
                "concept_coverage": concept_coverage,
                "project_investigation": project_investigation,
                "interview_objectives": interview_objectives,
                "last_question_concepts": ["Self-introduction", "Project background"],
                "interview_phase": "INTRODUCTION",
                "debug_dashboard": {
                    "objective": "Project Ownership",
                    "confidence": 0,
                    "claims": [],
                    "strategy": "INTRODUCTION",
                    "reason_for_next_question": "Greeting and request for self-introduction."
                },
                "objective_turns_spent": objective_turns_spent,
                "project_turns_spent": project_turns_spent,
                "failed_attempts_per_concept": failed_attempts_per_concept,
                "category_counts": category_counts,
                "question_bucket_history": question_bucket_history
            }
            
        candidate_answers_count = sum(1 for m in messages if m.type == "human")
        
        # --- Step 5: Check Pre-Assessment Objective Verification & Phase Transition ---
        all_objectives_verified = True
        for group in ["must_verify", "nice_to_verify"]:
            for obj_name, obj_data in interview_objectives.get(group, {}).items():
                status = obj_data.get("status", "unverified") if isinstance(obj_data, dict) else obj_data
                if status != "verified":
                    all_objectives_verified = False
                    break
                    
        current_phase = PhaseManager.transition_before_assessment(
            current_phase=current_phase,
            candidate_answers_count=candidate_answers_count,
            project_investigation=project_investigation,
            project_turns_spent=project_turns_spent,
            objective_turns_spent=objective_turns_spent,
            max_project_turns=max_project_turns,
            max_turns=max_turns,
            all_objectives_verified=all_objectives_verified,
            q_count=q_count,
            max_q=max_q
        )
        
        # --- Step 6: Select Active Objective & Category Balancing ---
        total_questions = sum(category_counts.values())
        ratios = {}
        for cat in ["project", "technical", "behavioral"]:
            ratios[cat] = category_counts.get(cat, 0) / total_questions if total_questions > 0 else 0.0
        differences = {cat: targets[cat] - ratios[cat] for cat in ["project", "technical", "behavioral"]}
        
        active_objective = ObjectiveSelector.select_active_objective(
            current_phase=current_phase,
            interview_objectives=interview_objectives,
            objective_turns_spent=objective_turns_spent,
            knowledge_model=knowledge_model,
            max_turns=max_turns,
            q_count=q_count,
            max_q=max_q,
            category_counts=category_counts,
            targets=targets,
            differences=differences
        )
        active_cat = ObjectiveSelector.get_objective_category(active_objective)
        
        # Toggle project mode based on active category selection
        if active_cat != "project":
            project_investigation["in_mode"] = False
        else:
            proj_name = project_investigation.get("project_name")
            if proj_name and project_turns_spent.get(proj_name, 0) < max_project_turns:
                project_investigation["in_mode"] = True
                
        # Resolve confidence for the active objective
        current_confidence = 0
        for group in ["must_verify", "nice_to_verify"]:
            if active_objective in interview_objectives.get(group, {}):
                obj_data = interview_objectives[group][active_objective]
                if isinstance(obj_data, dict):
                    current_confidence = obj_data.get("confidence", 0)
                elif obj_data == "verified":
                    current_confidence = 100
                    
        # Update turn counts per objective and category
        if current_phase not in ["INTRODUCTION", "WRAP_UP"] and messages:
            objective_turns_spent[active_objective] = objective_turns_spent.get(active_objective, 0) + 1
            category_counts[active_cat] = category_counts.get(active_cat, 0) + 1
            
        # Select active claim to probe
        weak_skills = knowledge_model.get("weak_skills", [])
        active_claim = ClaimSelector.select_active_claim(knowledge_model, weak_skills)
        
        project_name = None
        if project_investigation.get("in_mode"):
            project_name = project_investigation.get("project_name")
            
        resume_projects = []
        jd_skills = []
        if personalization_context:
            resume = personalization_context.get("extracted_resume", {}) or {}
            jd = personalization_context.get("extracted_jd", {}) or {}
            
            for p in resume.get("projects", []):
                if isinstance(p, dict):
                    title = p.get("title") or p.get("name")
                    if title:
                        resume_projects.append(title)
                elif p:
                    resume_projects.append(str(p))
                    
            for s in jd.get("required_skills", []):
                if s:
                    jd_skills.append(str(s))
                    
        # --- Step 7: Construct Prompt & Active Context Payload ---
        active_context = ContextBuilder.build_active_context(
            role=role,
            company_name=company_name,
            difficulty=difficulty,
            current_phase=current_phase,
            active_objective=active_objective,
            active_claim=active_claim,
            project_investigation=project_investigation,
            project_name=project_name,
            resume_projects=resume_projects,
            jd_skills=jd_skills,
            messages=messages,
            last_3_styles=last_3_styles,
            last_3_buckets=last_3_buckets,
            knowledge_model=knowledge_model,
            concept_coverage=concept_coverage,
            blueprint_json={"topic_tree": topic_tree, "objectives": interview_objectives},
            personalization_context=personalization_context
        )
        
        system_prompt = PromptBuilder.build_system_prompt(
            role=role,
            company_name=company_name,
            difficulty=difficulty,
            role_instructions=profile.get("role_instructions", ""),
            active_objective=active_objective,
            active_cat=active_cat
        )
        
        langsmith_metadata = {
            "interview_phase": current_phase,
            "active_objective": active_objective,
            "objective_confidence": int(current_confidence),
            "active_claim": str(active_claim) if active_claim else "None",
            "strategy_action": "pending",
            "reason_for_next_question": "pending"
        }
        
        # --- Step 8: Invoke Gemini LLM & Process Response ---
        try:
            response = llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=json.dumps(active_context))
                ],
                config={"metadata": langsmith_metadata}
            )
            
            # Parse raw JSON response string
            data = ResponseProcessor.parse_gemini_response(response.content)
            
            score_val = data.get("score", 3)
            depth_score = data.get("depth_score", score_val)
            specificity_score = data.get("specificity_score", score_val)
            evidence_strength = data.get("evidence_strength", "none")
            eval_msg = data.get("evaluation", "N/A")
            reasoning = data.get("reasoning_summary", "Critique failed")
            
            concept_updates = data.get("concept_coverage_updates", {})
            extracted_claims = data.get("extracted_claims", [])
            evidence_categories_detected = data.get("evidence_categories_detected", {})
            project_categories_demonstrated = data.get("project_categories_demonstrated", [])
            new_projects = data.get("new_projects", [])
            
            strategy_action = data.get("strategy_action", "MOVE_TO_NEW_TOPIC")
            question_style = data.get("question_style", "implementation")
            question_bucket = data.get("question_bucket", "Technical Skill")
            
            # Enforce question bucket rules based on active category
            if active_cat == "project":
                question_bucket = "Project"
            elif active_cat == "behavioral":
                question_bucket = "Behavioral"
            else:
                if question_bucket not in ["Technical Skill", "System Design"]:
                    question_bucket = "Technical Skill"
                    
            reason_for_next_question = data.get("reason_for_next_question", "Reason not provided")
            next_question = data.get("next_question", "Let's proceed.")
            next_expected_concepts = data.get("expected_concepts", [])
            
            langsmith_metadata["strategy_action"] = strategy_action
            langsmith_metadata["reason_for_next_question"] = reason_for_next_question
            langsmith_metadata["question_style"] = question_style
            
            # Optional LangSmith trace metadata tracking
            try:
                from langsmith.run_helpers import get_current_run_tree
                run_tree = get_current_run_tree()
                if run_tree:
                    run_tree.add_metadata({
                        "interview_phase": current_phase,
                        "active_objective": active_objective,
                        "objective_confidence": int(current_confidence),
                        "active_claim": str(active_claim) if active_claim else "None",
                        "strategy_action": strategy_action,
                        "reason_for_next_question": reason_for_next_question,
                        "question_style": question_style
                    })
            except Exception:
                pass
                
        except Exception as e:
            # Fallback handling on LLM invocation error
            print(f"Agent LLM invocation failed: {e}")
            fallback = build_contextual_fallback_question(
                role=role,
                interview_objectives=interview_objectives,
                gap_analysis=personalization_context,
                missing_topics=missing_topics,
                knowledge_model=knowledge_model,
                project_investigation=project_investigation,
                is_wrap_up=(current_phase == "WRAP_UP" or q_count >= max_q)
            )
            next_question = fallback["question"]
            strategy_action = "wrap_up" if (current_phase == "WRAP_UP" or q_count >= max_q) else "MOVE_TO_NEW_TOPIC"
            question_style = "failure_analysis" if (current_phase == "WRAP_UP" or q_count >= max_q) else "implementation"
            if current_phase == "WRAP_UP" or q_count >= max_q:
                question_bucket = "Behavioral"
            else:
                if active_cat == "project":
                    question_bucket = "Project"
                elif active_cat == "behavioral":
                    question_bucket = "Behavioral"
                else:
                    question_bucket = "Technical Skill"
            reason_for_next_question = "Fallback question generated due to LLM error."
            next_expected_concepts = fallback["expected_concepts"]
            
            score_val = 3
            depth_score = 3
            specificity_score = 3
            evidence_strength = "none"
            eval_msg = "N/A"
            reasoning = f"Gemini call failed: {e}"
            concept_updates = {}
            extracted_claims = []
            evidence_categories_detected = {}
            project_categories_demonstrated = []
            new_projects = []
            data = {}
            
        question_style_history.append(question_style)
        question_bucket_history.append(question_bucket)
        
        # --- Step 9: StateUpdater Pipeline Executions ---
        # 9a. Accumulate failed probing attempts per concept
        StateUpdater.accumulate_failed_attempts(
            score_val=score_val,
            evidence_strength=evidence_strength,
            last_question_concepts=last_question_concepts,
            failed_attempts_per_concept=failed_attempts_per_concept,
            knowledge_model=knowledge_model,
            concept_coverage=concept_coverage
        )
        
        # 9b. Update concept coverage states
        StateUpdater.update_concept_coverage(
            concept_coverage=concept_coverage,
            concept_updates=concept_updates
        )
        
        STRENGTH_VALUES = {"none": 0, "weak": 1, "moderate": 2, "strong": 3}
        WEIGHTS = {"none": 0, "weak": 5, "moderate": 15, "strong": 20}
        
        # 9c. Re-calculate objective verification confidence scores
        StateUpdater.update_objectives_confidence(
            interview_objectives=interview_objectives,
            active_objective=active_objective,
            evidence_categories_detected=evidence_categories_detected,
            STRENGTH_VALUES=STRENGTH_VALUES,
            WEIGHTS=WEIGHTS
        )
        
        # 9d. Register and track technical claims in Knowledge Model
        StateUpdater.update_claims_knowledge_base(
            knowledge_model=knowledge_model,
            extracted_claims=extracted_claims,
            active_claim=active_claim,
            project_categories_demonstrated=project_categories_demonstrated,
            evidence_categories_detected=evidence_categories_detected,
            evidence_strength=evidence_strength,
            score_val=score_val,
            q_count=q_count
        )
        
        # 9e. Update deep-dive project investigation tracking
        StateUpdater.update_project_investigation(
            project_investigation=project_investigation,
            new_projects=new_projects,
            active_cat=active_cat,
            max_project_turns=max_project_turns,
            project_turns_spent=project_turns_spent,
            project_categories_demonstrated=project_categories_demonstrated,
            question_style=question_style,
            evidence_strength=evidence_strength
        )
        
        # --- Step 10: Adjust Adaptive Difficulty Level ---
        difficulty = StateUpdater.adjust_adaptive_difficulty(
            state=state,
            score_val=score_val,
            current_difficulty=difficulty
        )
        
        # Chronological score history recording
        hist = state.get("score_history", [])
        if score_val is not None:
            hist = hist + [score_val]
            
        # --- Step 11: Post-Assessment Phase Transition & Bonus Turn Logic ---
        all_objectives_verified_now = True
        for group in ["must_verify", "nice_to_verify"]:
            for obj_name, obj_data in interview_objectives.get(group, {}).items():
                status = obj_data.get("status", "unverified") if isinstance(obj_data, dict) else obj_data
                if status != "verified":
                    all_objectives_verified_now = False
                    break
                    
        next_phase = PhaseManager.transition_after_assessment(
            current_phase=current_phase,
            candidate_answers_count=candidate_answers_count,
            project_investigation=project_investigation,
            project_turns_spent=project_turns_spent,
            objective_turns_spent=objective_turns_spent,
            max_project_turns=max_project_turns,
            max_turns=max_turns,
            all_objectives_verified_now=all_objectives_verified_now
        )
        
        # Evaluate dynamic bonus turn: Grant +1 question turn if candidate is close to verifying a must-verify objective
        has_unverified_must = False
        must_list = interview_objectives.get("must_verify", {})
        nice_list = interview_objectives.get("nice_to_verify", {})
        for obj_name, obj_data in must_list.items():
            status = obj_data.get("status", "unverified") if isinstance(obj_data, dict) else obj_data
            if status != "verified":
                has_unverified_must = True
                break
                
        active_obj_data = must_list.get(active_objective, {}) or nice_list.get(active_objective, {})
        active_obj_conf = 0
        if isinstance(active_obj_data, dict):
            active_obj_conf = active_obj_data.get("confidence", 0)
        elif active_obj_data == "verified":
            active_obj_conf = 100
            
        if (q_count + 1) >= max_q and has_unverified_must and max_q < original_max_q + 3:
            if active_obj_conf < 80 and strategy_action in ["CHALLENGE_CLAIM", "PROBE_DEEPER"]:
                max_q += 1
                print(f"[BONUS TURN] Granting bonus turn {max_q - original_max_q}. New limit: {max_q}")
                
        if all_objectives_verified_now or (q_count + 1) >= max_q:
            next_phase = "WRAP_UP"
            
        agent_status = "in_progress"
        if next_phase == "WRAP_UP":
            agent_status = "completed"
            
        # Update covered and missing topic lists
        newly_covered = []
        if primary_topic := data.get("primary_topic"):
            if primary_topic in missing_topics:
                newly_covered.append(primary_topic)
        for sec in data.get("secondary_topics", []):
            if sec in missing_topics and sec not in newly_covered:
                newly_covered.append(sec)
                
        updated_covered = covered_topics + newly_covered
        updated_missing = [t for t in missing_topics if t not in updated_covered]
        
        # --- Step 12: Assemble Debug Dashboard Payload & Final State Return ---
        prev_dashboard = state.get("debug_dashboard") or {}
        trace = list(prev_dashboard.get("execution_trace") or [])
        before_confidence = prev_dashboard.get("confidence", 0)
        
        trace_event = {
            "turn": q_count + 1,
            "phase": current_phase,
            "objective": active_objective or "None",
            "claim": active_claim or "None",
            "confidence_before": int(before_confidence),
            "confidence_after": int(current_confidence)
        }
        trace.append(trace_event)
        
        claims_data = knowledge_model.get("claims") or knowledge_model.get("unproven_claims") or []
        claims_list = [c.get("claim", "") for c in claims_data]
        
        debug_dashboard = {
            "objective": active_objective,
            "confidence": current_confidence,
            "claims": claims_list,
            "strategy": strategy_action,
            "reason_for_next_question": reason_for_next_question,
            "question_style": question_style,
            "question_bucket": question_bucket,
            "context_metrics": active_context.get("context_metrics"),
            "execution_trace": trace
        }
        
        print({
            "phase": next_phase,
            "strategy": strategy_action,
            "confidence": current_confidence,
            "claims": claims_list,
            "question_bucket": question_bucket
        })
        
        return {
            "current_question": next_question,
            "question_count": q_count + 1,
            "covered_topics": updated_covered,
            "missing_topics": updated_missing,
            "score_history": hist,
            "messages": messages + [AIMessage(content=next_question)],
            "evaluation": eval_msg,
            "reasoning_summary": reasoning,
            "score": score_val,
            "primary_topic": data.get("primary_topic", "General"),
            "secondary_topics": data.get("secondary_topics", []),
            "action": strategy_action,
            "status": agent_status,
            "company_name": company_name,
            "topic_tree": topic_tree,
            "knowledge_model": knowledge_model,
            "concept_coverage": concept_coverage,
            "project_investigation": project_investigation,
            "interview_objectives": interview_objectives,
            "last_question_concepts": next_expected_concepts,
            "interview_phase": next_phase,
            "debug_dashboard": debug_dashboard,
            "max_question_count": max_q,
            "original_max_question_count": original_max_q,
            "question_style_history": question_style_history,
            "objective_turns_spent": objective_turns_spent,
            "project_turns_spent": project_turns_spent,
            "failed_attempts_per_concept": failed_attempts_per_concept,
            "category_counts": category_counts,
            "question_bucket_history": question_bucket_history
        }

    # Bind node to StateGraph workflow and set entry point
    workflow.add_node("interviewer", interviewer_node)
    workflow.set_entry_point("interviewer")
    workflow.add_edge("interviewer", END)
    
    return workflow.compile()


def parse_json_content(content) -> dict:
    """
    Parses and deserializes JSON content strings returned from Gemini LLM calls.
    
    Features:
      - Extracts plain text if input is a list of dictionary blocks.
      - Strips markdown triple-backtick code fence blocks (```json ... ```).
      - Catches JSONDecodeError exceptions gracefully and returns a safe fallback structured dictionary.
      
    Args:
        content (str | list | Any): Content payload to parse.
        
    Returns:
        dict: Parsed dictionary payload, or safe fallback dictionary if parsing fails.
    """
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
    
    # Strip markdown code fence syntax (```json ... ```)
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        
    try:
        return json.loads(cleaned)
    except Exception as e:
        print(f"JSON Parsing Error: {e} | Content: {content}")
        # Safe fallback response dictionary when JSON decoding fails
        return {
            "evaluation": "N/A",
            "reasoning_summary": "Failed to parse critique",
            "score": 3,
            "primary_topic": "General",
            "secondary_topics": [],
            "action": "MOVE_TO_NEW_TOPIC",
            "next_question": "Let's stay concrete. Can you walk me through one implementation decision you personally made, the tradeoff behind it, and how you validated that it worked?",
            "expected_concepts": ["implementation decision", "tradeoff", "validation"]
        }

# Instantiate the default compiled interview agent state graph
interview_agent = build_interview_graph()

