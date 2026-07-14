import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select

from app.models.interview import UserProfile, StudyPlan
from app.agents.seed_knowledge_base import KNOWLEDGE_DATA
from app.agents.profiles import ROLE_PROFILES
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from qdrant_client import QdrantClient
except ImportError:
    QdrantClient = None


def get_matching_resources(weak_topics: List[Dict[str, Any]], api_key: str = None) -> List[Dict[str, Any]]:
    """
    Retrieves matching resource cards for the weak topics.
    Uses Qdrant vector search if API key is present and database is seeded.
    Otherwise, falls back to direct python keyword lookup and ranking.
    """
    matched_resources = []
    
    # Check if we can use Qdrant
    use_qdrant = False
    client = None
    collection_name = "global_knowledge_base"
    
    if QdrantClient and api_key and api_key != "placeholder_api_key" and api_key != "your_gemini_api_key_here":
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "qdrant_db")
            client = QdrantClient(path=db_path)
            # Check if collection exists and has points
            info = client.get_collection(collection_name)
            if info and info.points_count > 0:
                use_qdrant = True
        except Exception as e:
            print(f"[WARNING] Could not connect to Qdrant collection: {e}. Falling back to keyword search.")
            
    for topic_info in weak_topics:
        topic_name = topic_info["topic"]
        avg_score = topic_info["average_score"]
        
        resources_for_topic = []
        
        if use_qdrant:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                embeddings_model = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004",
                    google_api_key=api_key
                )
                query_vector = embeddings_model.embed_query(topic_name)
                
                # Perform search
                search_results = client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=5
                )
                
                # Convert hits to dicts
                for hit in search_results:
                    resources_for_topic.append(hit.payload)
            except Exception as e:
                print(f"[WARNING] Qdrant search failed for topic {topic_name}: {e}. Using keyword fallback.")
                use_qdrant = False  # Switch to fallback
                
        # Keyword lookup fallback (or if Qdrant search yielded nothing)
        if not use_qdrant or not resources_for_topic:
            # Substring match on topic or concept
            for item in KNOWLEDGE_DATA:
                item_topic = item["topic"].lower()
                item_concept = item["concept"].lower()
                q = topic_name.lower()
                
                if q in item_topic or item_topic in q or q in item_concept or item_concept in q:
                    resources_for_topic.append(item)
                    
        # Apply difficulty ranking and selection heuristics
        # If user score < 60, prefer beginner/intermediate.
        # If user score >= 60, prefer intermediate/advanced.
        ranked_resources = []
        for res in resources_for_topic:
            # Base score = source quality
            rel_score = res.get("source_quality", 4.0)
            
            diff = res.get("difficulty_level", "intermediate").lower()
            if avg_score < 60:
                if diff == "beginner":
                    rel_score += 3.0
                elif diff == "intermediate":
                    rel_score += 1.0
            else:
                if diff == "intermediate":
                    rel_score += 3.0
                elif diff == "advanced":
                    rel_score += 2.0
                    
            ranked_resources.append((rel_score, res))
            
        # Sort by relevance score descending and take top 2
        ranked_resources.sort(key=lambda x: x[0], reverse=True)
        for _, res in ranked_resources[:2]:
            matched_resources.append(res)
            
    return matched_resources

def generate_study_plan(db: Session, user_profile: UserProfile, associated_interview_id: Optional[str] = None) -> StudyPlan:
    """
    Generates a personalized study plan for the candidate.
    Identifies weak areas, queries matching resources with rich metadata,
    calls Gemini to build a strategic learning roadmap, and saves a versioned StudyPlan record.
    """
    # 1. Archive previous active plans by marking them superseded
    stmt = select(StudyPlan).where(
        StudyPlan.user_id == user_profile.user_id,
        StudyPlan.status == "active"
    )
    active_plans = db.exec(stmt).all()
    for plan in active_plans:
        plan.status = "superseded"
        db.add(plan)
    db.commit()
    
    # 2. Extract weak or improving topics from UserProfile
    try:
        mastery_map = json.loads(user_profile.topic_mastery_json)
    except Exception as e:
        print(f"Error parsing topic mastery for planning: {e}")
        mastery_map = {}
        
    weak_topics = []
    for topic, stats in mastery_map.items():
        state = stats.get("mastery_state", "Weak")
        if state in ["Weak", "Improving"] or stats.get("average_score", 100) < 70:
            weak_topics.append({
                "topic": topic,
                "average_score": stats.get("average_score", 50),
                "latest_score": stats.get("latest_score", 50),
                "trend_direction": stats.get("trend_direction", "insufficient_data"),
                "mastery_state": state
            })
            
    # Default fallback if no weak topics found
    if not weak_topics:
        weak_topics.append({
            "topic": "Machine Learning",
            "average_score": 70.0,
            "latest_score": 70,
            "trend_direction": "insufficient_data",
            "mastery_state": "Improving"
        })
        
    # 3. Retrieve relevant resource cards matching the weak concepts
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    resources = get_matching_resources(weak_topics, api_key)
    
    # 4. Prompt Gemini to construct the strategic learning roadmap
    if not api_key or api_key == "placeholder_api_key" or api_key == "your_gemini_api_key_here":
        # No API Key Fallback
        roadmap = [
            {
                "milestone_title": f"Review {topic_info['topic']} Basics",
                "concept": topic_info["topic"],
                "description": f"Focus on core concepts and theory regarding {topic_info['topic']}.",
                "duration": "3 days",
                "learning_sequence": {
                    "intuition": f"Understand the fundamentals of {topic_info['topic']}.",
                    "mechanism": f"Deep dive into the structural operations of {topic_info['topic']}.",
                    "practice": f"Work on implementing mock models or pipelines for {topic_info['topic']}."
                },
                "validation_criteria": f"Be able to explain {topic_info['topic']} and successfully complete a focused re-interview."
            }
            for topic_info in weak_topics
        ]
        
        practice_questions = []
        for res in resources:
            practice_questions.extend(res.get("practice_questions", []))
            
        recommended_resources = []
        for res in resources:
            for r in res.get("resources", []):
                recommended_resources.append({
                    "title": r["title"],
                    "url": r["url"],
                    "estimated_time": res.get("estimated_completion_time", "30 minutes"),
                    "type": res.get("resource_type", "article"),
                    "difficulty": res.get("difficulty_level", "intermediate"),
                    "why_recommended": f"Matches your weakness in {res.get('concept')}."
                })
                
        plan = StudyPlan(
            user_id=user_profile.user_id,
            associated_interview_id=associated_interview_id,
            roadmap_json=json.dumps(roadmap),
            recommended_resources_json=json.dumps(recommended_resources),
            practice_questions_json=json.dumps(practice_questions),
            status="active"
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan
        
    # Active Gemini invocation
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.4,
        google_api_key=api_key,
        response_mime_type="application/json",
        max_retries=1
    )
    
    system_prompt = (
        "You are an expert technical AI coach. Your goal is to convert candidate weaknesses into a highly strategic learning plan.\n"
        "You will be given the candidate's weak topics, their scores, and a list of matching resources retrieved from our knowledge base.\n\n"
        "Instructions:\n"
        "- Generate a professional study plan in JSON format.\n"
        "- Explain exactly WHY the user is struggling (e.g., matching their low score/declining trend to the concepts).\n"
        "- Break the plan into sequential milestones. For each milestone, specify a structured learning_sequence:\n"
        "  1. intuition: The fundamental high-level idea to grasp.\n"
        "  2. mechanism: The detailed math, code structure, or pipeline to study.\n"
        "  3. practice: Specific coding, architectural exercises, or math questions to write out.\n"
        "- Map recommendations to the retrieved resources, explaining why each is recommended.\n"
        "- Provide 3-5 concrete practice questions for validation.\n\n"
        "You MUST return a JSON object matching this schema:\n"
        "{\n"
        "  \"strategic_rationale\": \"Detailed narrative explaining the gap assessment and sequence strategy...\",\n"
        "  \"roadmap\": [\n"
        "    {\n"
        "      \"milestone_title\": \"Milestone Title (e.g. Day 1-2: Math of Self-Attention)\",\n"
        "      \"concept\": \"Focus Concept name\",\n"
        "      \"description\": \"Milestone objective summary...\",\n"
        "      \"duration\": \"Estimated time (e.g. 2 days)\",\n"
        "      \"learning_sequence\": {\n"
        "        \"intuition\": \"Why it works conceptually...\",\n"
        "        \"mechanism\": \"How to build/calculate it mathematically/programmatically...\",\n"
        "        \"practice\": \"Practice instructions...\"\n"
        "      },\n"
        "      \"validation_criteria\": \"What they must verify before completing (e.g. derive self-attention weights on paper)\"\n"
        "    }\n"
        "  ],\n"
        "  \"recommended_resources\": [\n"
        "    {\n"
        "      \"title\": \"Resource Title\",\n"
        "      \"url\": \"Resource URL\",\n"
        "      \"estimated_time\": \"Estimated duration\",\n"
        "      \"type\": \"Resource Type (e.g. documentation, article, video)\",\n"
        "      \"difficulty\": \"Difficulty Level\",\n"
        "      \"why_recommended\": \"Brief explanation linking the resource to the candidate's specific score and concept gap.\"\n"
        "    }\n"
        "  ],\n"
        "  \"practice_questions\": [\n"
        "    \"Question/exercise string 1\",\n"
        "    ...\n"
        "  ]\n"
        "}"
    )
    
    prompt_content = {
        "weak_topics": weak_topics,
        "retrieved_resources": resources
    }
    
    try:
        response = llm.invoke([
            ("system", system_prompt),
            ("human", f"Build a study plan for this profile:\n\n{json.dumps(prompt_content, indent=2)}")
        ])
        
        content_val = response.content
        if isinstance(content_val, list):
            content_val = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content_val)
        elif not isinstance(content_val, str):
            content_val = str(content_val)
        data = json.loads(content_val.strip())
        
        # Overwrite with sanitized and fully populated resources
        recommended = data.get("recommended_resources", [])
        if not recommended:
            # Fallback map resources
            for res in resources:
                res_topic = res.get("topic")
                topic_stats = mastery_map.get(res_topic) if res_topic else None
                avg_score = topic_stats.get("average_score", 50) if isinstance(topic_stats, dict) else 50
                for r in res.get("resources", []):
                    recommended.append({
                        "title": r["title"],
                        "url": r["url"],
                        "estimated_time": res.get("estimated_completion_time", "30 minutes"),
                        "type": res.get("resource_type", "article"),
                        "difficulty": res.get("difficulty_level", "intermediate"),
                        "why_recommended": f"Matches your weak score of {avg_score}%."
                    })
                    
        roadmap = data.get("roadmap", [])
        practice_qs = data.get("practice_questions", [])
        
        plan = StudyPlan(
            user_id=user_profile.user_id,
            associated_interview_id=associated_interview_id,
            roadmap_json=json.dumps(roadmap),
            recommended_resources_json=json.dumps(recommended),
            practice_questions_json=json.dumps(practice_qs),
            status="active"
        )
        
        db.add(plan)
        db.commit()
        db.refresh(plan)
        try:
            from app.routers.interview import log_structured_event
            log_structured_event("Study Plan Generated", {
                "user_id": user_profile.user_id,
                "associated_interview_id": associated_interview_id
            })
        except:
            pass
        return plan
        
    except Exception as e:
        print(f"[ERROR] Failed LLM generation for Planning Agent: {e}")
        # Return fallback plan
        plan = StudyPlan(
            user_id=user_profile.user_id,
            associated_interview_id=associated_interview_id,
            roadmap_json=json.dumps([]),
            recommended_resources_json=json.dumps([]),
            practice_questions_json=json.dumps([]),
            status="active"
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        try:
            from app.routers.interview import log_structured_event
            log_structured_event("Study Plan Generated", {
                "user_id": user_profile.user_id,
                "associated_interview_id": associated_interview_id
            })
        except:
            pass
        return plan
