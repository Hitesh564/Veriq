from datetime import datetime
from typing import List, Optional
import uuid
from sqlmodel import Field, Relationship, SQLModel

class InterviewBase(SQLModel):
    role: str
    difficulty: str
    duration_minutes: int
    max_question_count: int
    question_count: int = 0
    status: str = "in_progress"  # "in_progress", "completed"
    current_question: Optional[str] = Field(default=None)
    mode: str = Field(default="quick")  # "quick", "re-interview"
    focus_topics_json: Optional[str] = Field(default=None)
    resume_text: Optional[str] = Field(default=None)
    jd_text: Optional[str] = Field(default=None)
    gap_analysis_json: Optional[str] = Field(default=None)
    company_name: Optional[str] = Field(default=None)
    topic_tree_json: Optional[str] = Field(default="{}")
    knowledge_model_json: Optional[str] = Field(default="{}")
    concept_coverage_json: Optional[str] = Field(default="{}")
    project_investigation_json: Optional[str] = Field(default="{}")
    interview_objectives_json: Optional[str] = Field(default="{}")
    interview_phase: Optional[str] = Field(default="INTRODUCTION")
    debug_dashboard_json: Optional[str] = Field(default="{}")
    candidate_profile_json: Optional[str] = Field(default=None)
    job_profile_json: Optional[str] = Field(default=None)
    company_profile_json: Optional[str] = Field(default=None)
    blueprint_json: Optional[str] = Field(default=None)
    user_id: str = Field(index=True, nullable=False)
    resume_path: Optional[str] = Field(default=None)


class Interview(InterviewBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    
    # Relationship back to transcripts
    transcripts: List["Transcript"] = Relationship(
        back_populates="interview",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    # Relationship to evaluation report (one-to-one)
    evaluation_report: Optional["EvaluationReport"] = Relationship(
        back_populates="interview",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )

class TranscriptBase(SQLModel):
    sender: str  # "interviewer" or "candidate"
    text: str
    topic: Optional[str] = None
    score: Optional[int] = Field(default=None)
    reasoning_summary: Optional[str] = Field(default=None)
    secondary_topics_json: Optional[str] = Field(default=None)
    difficulty: Optional[str] = Field(default=None)
    audio_url: Optional[str] = Field(default=None)
    turn_metadata_json: Optional[str] = Field(default=None, nullable=True)


class Transcript(TranscriptBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: str = Field(foreign_key="interview.id", index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship back to interview
    interview: Optional[Interview] = Relationship(back_populates="transcripts")


class EvaluationReport(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    interview_id: str = Field(foreign_key="interview.id", unique=True, index=True)
    overall_score: int
    technical_score: int
    communication_score: int
    explanation_score: int
    problem_solving_score: int
    behavioral_score: int
    summary: str
    strengths_json: str
    categorized_weaknesses_json: str
    topic_performance_json: str
    evaluation_version: str
    raw_json: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship back to interview
    interview: Optional[Interview] = Relationship(back_populates="evaluation_report")


class UserProfile(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(unique=True, index=True, nullable=False)
    topic_mastery_json: str = Field(default="{}")
    readiness_scores_json: str = Field(default="{}")
    role_performance_json: str = Field(default="{}")
    history_trends_json: str = Field(default="[]")
    recommendations_json: str = Field(default="[]")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class StudyPlan(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    associated_interview_id: Optional[str] = Field(default=None, foreign_key="interview.id", nullable=True)
    roadmap_json: str = Field(default="[]")
    recommended_resources_json: str = Field(default="[]")
    practice_questions_json: str = Field(default="[]")
    status: str = Field(default="active")  # "active", "superseded", "completed"
    created_at: datetime = Field(default_factory=datetime.utcnow)



