from typing import TypedDict, List, Optional, Dict, Any, NotRequired
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
    evaluation: NotRequired[Optional[str]]
    reasoning_summary: NotRequired[Optional[str]]
    score: NotRequired[Optional[int]]
    primary_topic: NotRequired[Optional[str]]
    secondary_topics: NotRequired[Optional[List[str]]]
    action: NotRequired[Optional[str]]
    personalization_context: NotRequired[Optional[Dict[str, Any]]]
    company_name: NotRequired[Optional[str]]
    topic_tree: NotRequired[Optional[Dict[str, Any]]]
    knowledge_model: NotRequired[Optional[Dict[str, Any]]]
    concept_coverage: NotRequired[Optional[Dict[str, Any]]]
    project_investigation: NotRequired[Optional[Dict[str, Any]]]
    interview_objectives: NotRequired[Optional[Dict[str, Any]]]
    last_question_concepts: NotRequired[Optional[List[str]]]
    active_question_intent: NotRequired[Optional[Dict[str, Any]]]
    interview_phase: NotRequired[Optional[str]]
    debug_dashboard: NotRequired[Optional[Dict[str, Any]]]
    original_max_question_count: NotRequired[Optional[int]]
    question_style_history: NotRequired[Optional[List[str]]]
    objective_turns_spent: NotRequired[Optional[Dict[str, int]]]
    project_turns_spent: NotRequired[Optional[Dict[str, int]]]
    failed_attempts_per_concept: NotRequired[Optional[Dict[str, int]]]
    category_counts: NotRequired[Optional[Dict[str, int]]]
    question_bucket_history: NotRequired[Optional[List[str]]]




