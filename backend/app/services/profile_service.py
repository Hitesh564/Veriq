import os
import json
import time
import asyncio
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import GEMINI_API_KEY
from app.models.profile import CandidateProfile, JobProfile, GapAnalysis, CompanyProfile
from app.services.cache import comp_cache, hash_text

LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "25"))


async def build_candidate_profile(resume_text: str) -> CandidateProfile:
    if not resume_text or not resume_text.strip():
        return CandidateProfile()
        
    resume_hash = hash_text(resume_text)
    key = comp_cache.generate_cache_key("resume", "v1", resume_hash)
    cached = comp_cache.get(key)
    if cached:
        return cached
        
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        return CandidateProfile(skills=["Software Engineering"], technologies=["Python"])
        
    start_time = time.perf_counter()
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=api_key,
            response_mime_type="application/json",
            max_retries=1
        )
        
        prompt = (
            "You are an expert resume parser. Parse the provided resume text into a structured JSON object. "
            "Extract skills, projects (with title, description, and technologies used), experience (with role, company, and duration), "
            "education, certifications, technologies, achievements, primary tech stack, years of experience (estimate as float), "
            "project complexity (estimate as 'low', 'medium', or 'high'), leadership experience (description of any lead/manager/mentor roles), "
            "research experience, and open source contributions.\n\n"
            "Resume text:\n"
            f"{resume_text[:4000]}\n\n"
            "Return JSON matching this schema:\n"
            "{\n"
            "  \"skills\": [\"skill1\", \"skill2\"],\n"
            "  \"projects\": [{\"title\": \"project1\", \"description\": \"desc\", \"technologies\": [\"tech1\"]}],\n"
            "  \"experience\": [{\"role\": \"Engineer\", \"company\": \"Google\", \"duration\": \"2 years\"}],\n"
            "  \"education\": [{\"degree\": \"BS CS\", \"school\": \"MIT\", \"year\": \"2020\"}],\n"
            "  \"certifications\": [\"AWS Certified Solutions Architect\"],\n"
            "  \"technologies\": [\"Python\", \"Docker\"],\n"
            "  \"achievements\": [\"First place in Hackathon\"],\n"
            "  \"primary_tech_stack\": [\"Python\", \"React\"],\n"
            "  \"years_of_experience\": 3.5,\n"
            "  \"project_complexity\": \"medium\",\n"
            "  \"leadership_experience\": \"Mentored 2 junior engineers\",\n"
            "  \"research_experience\": \"None\",\n"
            "  \"open_source\": \"Contributor to LangChain\"\n"
            "}"
        )
        
        response = await asyncio.wait_for(
            llm.ainvoke([SystemMessage(content=prompt)]),
            timeout=LLM_TIMEOUT_SECONDS,
        )
        data = json.loads(response.content.strip())
        profile = CandidateProfile(**data)
        
        comp_cache.record_generation_time(time.perf_counter() - start_time)
        comp_cache.set(key, profile)
        return profile
    except Exception as e:
        print(f"[ERROR] Failed to build candidate profile: {e}")
        return CandidateProfile(skills=["Software Engineering"], technologies=["Python"])

async def build_job_profile(jd_text: str) -> JobProfile:
    if not jd_text or not jd_text.strip():
        return JobProfile()
        
    jd_hash = hash_text(jd_text)
    key = comp_cache.generate_cache_key("jd", "v1", jd_hash)
    cached = comp_cache.get(key)
    if cached:
        return cached
        
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        return JobProfile(required_skills=["Software Engineering"])
        
    start_time = time.perf_counter()
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=api_key,
            response_mime_type="application/json",
            max_retries=1
        )
        
        prompt = (
            "You are an expert job description parser. Parse the provided JD text into a structured JSON object. "
            "Extract required skills, preferred skills, responsibilities, role level (estimate as 'Junior', 'Mid-level', 'Senior', or 'Lead'), "
            "technology stack, and required years of experience (estimate as float).\n\n"
            "JD text:\n"
            f"{jd_text[:4000]}\n\n"
            "Return JSON matching this schema:\n"
            "{\n"
            "  \"required_skills\": [\"skill1\", \"skill2\"],\n"
            "  \"preferred_skills\": [\"skill3\"],\n"
            "  \"responsibilities\": [\"resp1\", \"resp2\"],\n"
            "  \"role_level\": \"Senior\",\n"
            "  \"technology_stack\": [\"Python\", \"AWS\"],\n"
            "  \"experience_years\": 5.0\n"
            "}"
        )
        
        response = await asyncio.wait_for(
            llm.ainvoke([SystemMessage(content=prompt)]),
            timeout=LLM_TIMEOUT_SECONDS,
        )
        data = json.loads(response.content.strip())
        profile = JobProfile(**data)
        
        comp_cache.record_generation_time(time.perf_counter() - start_time)
        comp_cache.set(key, profile)
        return profile
    except Exception as e:
        print(f"[ERROR] Failed to build job profile: {e}")
        return JobProfile(required_skills=["Software Engineering"])

async def build_gap_analysis(cand: CandidateProfile, job: JobProfile) -> GapAnalysis:
    if not cand.skills and not job.required_skills:
        return GapAnalysis()
        
    cand_hash = hash_text(cand.model_dump_json())
    job_hash = hash_text(job.model_dump_json())
    key = comp_cache.generate_cache_key("gap", "v1", f"{cand_hash}:{job_hash}")
    cached = comp_cache.get(key)
    if cached:
        return cached
        
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        return GapAnalysis()
        
    start_time = time.perf_counter()
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=api_key,
            response_mime_type="application/json",
            max_retries=1
        )
        
        prompt = (
            "You are an expert technical recruiter. Compare the Candidate Profile and Job Profile to produce a detailed Gap Analysis and Interview Priorities. "
            "Compare the candidate's skills, technologies, and projects with the JD's requirements and responsibilities.\n\n"
            f"Candidate Profile:\n{cand.model_dump_json(indent=2)}\n\n"
            f"Job Profile:\n{job.model_dump_json(indent=2)}\n\n"
            "Determine:\n"
            "1. matching_skills: Skills claimed by candidate that match JD requirements.\n"
            "2. missing_skills: Skills required by JD but missing/unproven in candidate profile.\n"
            "3. strong_areas: Areas of high experience or technical depth matching the job.\n"
            "4. weak_areas: Gaps in candidate profile compared to JD expectations.\n"
            "5. difficulty_adjustments: Decide if difficulty should be adjusted (estimate as 'easy', 'none', or 'hard').\n"
            "6. interview_priorities: Construct a prioritized strategy:\n"
            "   - priority_1: Primary skill/gap to verify first.\n"
            "   - priority_2: Secondary skill/gap to verify.\n"
            "   - priority_3: Third skill/gap to verify.\n"
            "   - topics_to_skip: Known candidate strengths or unrelated topics to skip.\n"
            "   - topics_to_probe_deeply: High-priority topics/projects to probe deeply.\n\n"
            "Return JSON matching this schema:\n"
            "{\n"
            "  \"matching_skills\": [\"skill1\"],\n"
            "  \"missing_skills\": [\"skill2\"],\n"
            "  \"strong_areas\": [\"area1\"],\n"
            "  \"weak_areas\": [\"area2\"],\n"
            "  \"difficulty_adjustments\": \"none\",\n"
            "  \"interview_priorities\": {\n"
            "     \"priority_1\": \"Verify skill2 which is a key JD requirement\",\n"
            "     \"priority_2\": \"Explore project1 to check system design understanding\",\n"
            "     \"priority_3\": \"Verify coding comfort in tech stack\",\n"
            "     \"topics_to_skip\": [\"skill1\"],\n"
            "     \"topics_to_probe_deeply\": [\"project1\"]\n"
            "  }\n"
            "}"
        )
        
        response = await asyncio.wait_for(
            llm.ainvoke([SystemMessage(content=prompt)]),
            timeout=LLM_TIMEOUT_SECONDS,
        )
        data = json.loads(response.content.strip())
        gap = GapAnalysis(**data)
        
        comp_cache.record_generation_time(time.perf_counter() - start_time)
        comp_cache.set(key, gap)
        return gap
    except Exception as e:
        print(f"[ERROR] Failed to build gap analysis: {e}")
        return GapAnalysis()

def get_company_profile(company_name: str) -> CompanyProfile:
    name_lower = company_name.lower().strip() if company_name else ""
    key = comp_cache.generate_cache_key("company_profile", "v1", name_lower)
    cached = comp_cache.get(key)
    if cached:
        return cached
        
    def _build():
        if "google" in name_lower:
            return CompanyProfile(
                company_name="Google",
                interview_style="Google Style",
                question_philosophy="Focus heavily on computer science fundamentals, algorithmic efficiency (Big O), scalability, and clean system design paradigms.",
                behavioral_framework="Googleyness and leadership (navigating ambiguity, helping others, ownership).",
                technical_focus="Algorithms, Data Structures (DSA), System Design, Scalability, and technical depth.",
                difficulty_curve="Steep, high bar for optimal runtime and space tradeoffs.",
                evaluation_bias="Highly technical, penalizes brute-force algorithms and vague architecture descriptions.",
                preferred_followups="Ask for optimization, scale limitations, and boundary conditions.",
                project_depth=0.4,
                coding_weight=0.5,
                system_design_weight=0.3
            )
        elif "amazon" in name_lower:
            return CompanyProfile(
                company_name="Amazon",
                interview_style="Amazon Style",
                question_philosophy="Focus on customer obsession, scale, operational excellence, and behavioral alignment with leadership principles.",
                behavioral_framework="Amazon Leadership Principles (Customer Obsession, Ownership, Bias for Action, Earn Trust, Dive Deep).",
                technical_focus="System Design, OOP design, scale bottlenecks, and Leadership Principles.",
                difficulty_curve="Moderate, shifts from basic logic to deep behavioral and ownership questioning.",
                evaluation_bias="Highly behavioral and leadership-aligned; a candidate with weaker coding but excellent leadership principles alignment can pass.",
                preferred_followups="Ask 'why' decisions were made, how they measured success metrics, and instances of leadership conflicts.",
                project_depth=0.5,
                coding_weight=0.3,
                system_design_weight=0.3
            )
        elif "nvidia" in name_lower:
            return CompanyProfile(
                company_name="NVIDIA",
                interview_style="NVIDIA Style",
                question_philosophy="Focus on low-level performance, GPU architecture, parallel programming, CUDA, deep learning systems, and hardware-software co-design.",
                behavioral_framework="Collaboration, technical excellence, passion for solving hard computing problems.",
                technical_focus="CUDA, GPU architecture, deep learning model architectures, distributed training, optimization, memory layouts, hardware constraints.",
                difficulty_curve="Very steep technical probing of hardware-level details and deep learning math.",
                evaluation_bias="Highly technical, penalizes shallow understanding of neural network libraries and framework abstractions without knowing bottom-up mechanics.",
                preferred_followups="Ask about memory bandwidth, kernel optimization, custom layer math, and hardware bottlenecks.",
                project_depth=0.4,
                coding_weight=0.4,
                system_design_weight=0.4
            )
        else:
            return CompanyProfile(
                company_name=company_name or "Target Company",
                interview_style="Standard",
                question_philosophy="Balanced technical and behavioral assessment targeting candidate skills.",
                behavioral_framework="Communication, team collaboration, and basic problem solving.",
                technical_focus="Standard software engineering concepts, API design, testing, and debugging.",
                difficulty_curve="Standard medium.",
                evaluation_bias="Balanced.",
                preferred_followups="Ask about implementation choices, tradeoffs, and testing.",
                project_depth=0.3,
                coding_weight=0.4,
                system_design_weight=0.3
            )
            
    profile = _build()
    comp_cache.set(key, profile, ttl=30*24*3600)
    return profile
