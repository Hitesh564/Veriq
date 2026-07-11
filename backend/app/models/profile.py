from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CandidateProfile(BaseModel):
    skills: List[str] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    primary_tech_stack: List[str] = Field(default_factory=list)
    years_of_experience: Optional[float] = None
    project_complexity: Optional[str] = None # "low", "medium", "high"
    leadership_experience: Optional[str] = None
    research_experience: Optional[str] = None
    open_source: Optional[str] = None

class JobProfile(BaseModel):
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    role_level: str = "Mid-level"
    technology_stack: List[str] = Field(default_factory=list)
    experience_years: Optional[float] = None

class GapAnalysis(BaseModel):
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    strong_areas: List[str] = Field(default_factory=list)
    weak_areas: List[str] = Field(default_factory=list)
    difficulty_adjustments: str = "none"
    interview_priorities: Dict[str, Any] = Field(default_factory=lambda: {
        "priority_1": "",
        "priority_2": "",
        "priority_3": "",
        "topics_to_skip": [],
        "topics_to_probe_deeply": []
    })

class CompanyProfile(BaseModel):
    company_name: str
    interview_style: str = "standard"
    question_philosophy: str = ""
    behavioral_framework: str = ""
    technical_focus: str = ""
    difficulty_curve: str = "medium"
    evaluation_bias: str = "balanced"
    preferred_followups: str = ""
    project_depth: float = 0.3
    coding_weight: float = 0.4
    system_design_weight: float = 0.3

class InterviewBlueprint(BaseModel):
    topic_tree: Dict[str, Any] = Field(default_factory=dict)
    interview_objectives: Dict[str, Any] = Field(default_factory=dict)
    concept_coverage: Dict[str, Any] = Field(default_factory=dict)
    project_targets: List[str] = Field(default_factory=list)
    coverage_budget: Dict[str, float] = Field(default_factory=dict)
    interview_strategy: str = ""
    evaluation_weights: Dict[str, float] = Field(default_factory=dict)
    interview_order: List[str] = Field(default_factory=list)

class InterviewContext(BaseModel):
    candidate_profile: Optional[CandidateProfile] = None
    job_profile: Optional[JobProfile] = None
    gap_analysis: Optional[GapAnalysis] = None
    company_profile: Optional[CompanyProfile] = None
    blueprint: InterviewBlueprint
    knowledge_model: Dict[str, Any]
    conversation_history: List[Any]
    interview_state: Dict[str, Any]
