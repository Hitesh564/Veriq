from typing import TypedDict, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage

class InterviewState(TypedDict):
    """
    State definition for the Veriq AI LangGraph agent.
    """
    messages: List[BaseMessage]
    role: str
    difficulty: str
    duration_minutes: int
    question_count: int
    max_question_count: int
    status: str
    current_question: str
    covered_topics: List[str]
    missing_topics: List[str]
    score_history: List[int]
    evaluation: Optional[str] = None
    reasoning_summary: Optional[str] = None
    score: Optional[int] = None
    primary_topic: Optional[str] = None
    secondary_topics: Optional[List[str]] = None
    action: Optional[str] = None
    personalization_context: Optional[Dict[str, Any]] = None
    company_name: Optional[str] = None
    topic_tree: Optional[Dict[str, Any]] = None
    knowledge_model: Optional[Dict[str, Any]] = None
    concept_coverage: Optional[Dict[str, Any]] = None
    project_investigation: Optional[Dict[str, Any]] = None
    interview_objectives: Optional[Dict[str, Any]] = None
    last_question_concepts: Optional[List[str]] = None
    active_question_intent: Optional[Dict[str, Any]] = None
    interview_phase: Optional[str] = "INTRODUCTION"
    debug_dashboard: Optional[Dict[str, Any]] = None
    original_max_question_count: Optional[int] = None
    question_style_history: Optional[List[str]] = None
    objective_turns_spent: Optional[Dict[str, int]] = None
    project_turns_spent: Optional[Dict[str, int]] = None
    failed_attempts_per_concept: Optional[Dict[str, int]] = None
    category_counts: Optional[Dict[str, int]] = None
    question_bucket_history: Optional[List[str]] = None





