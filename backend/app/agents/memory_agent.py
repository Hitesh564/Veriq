import json
from sqlmodel import Session, select
from datetime import datetime
from typing import List, Dict, Any

from app.models.interview import Interview, EvaluationReport, UserProfile
from app.agents.profiles import ROLE_PROFILES

def is_topic_match(topic_a: str, topic_b: str) -> bool:
    """
    Checks if two topic names match, allowing for substring matches and case-insensitivity
    (e.g., matching 'RAG' with 'RAG (Retrieval-Augmented Generation)').
    """
    ta = topic_a.lower().strip()
    tb = topic_b.lower().strip()
    if ta == tb:
        return True
    if len(ta) >= 3 and ta in tb:
        return True
    if len(tb) >= 3 and tb in ta:
        return True
    return False

def update_user_profile(db: Session, user_id: str = "default") -> UserProfile:

    """
    Analyzes historical evaluation reports for the candidate to compile 
    a structured User Knowledge Graph saved in the UserProfile.
    """
    # 1. Fetch all completed interviews for the user in chronological order
    stmt_interviews = select(Interview).where(
        Interview.status == "completed"
    ).order_by(Interview.created_at.asc())
    interviews = db.exec(stmt_interviews).all()
    interview_ids = [i.id for i in interviews]
    
    # 2. Fetch all evaluation reports for these interviews
    reports = []
    if interview_ids:
        stmt_reports = select(EvaluationReport).where(
            EvaluationReport.interview_id.in_(interview_ids)
        ).order_by(EvaluationReport.created_at.asc())
        reports = db.exec(stmt_reports).all()
        
    topic_scores_history = {}
    role_scores_history = {}
    history_trends = []
    
    # Map report to interview metadata for reference
    interview_map = {i.id: i for i in interviews}
    
    for r in reports:
        inv = interview_map.get(r.interview_id)
        if not inv:
            continue
            
        # Add to chronological history trends
        history_trends.append({
            "date": inv.created_at.isoformat(),
            "score": r.overall_score,
            "role": inv.role
        })
        
        # Add to role overall performance
        if inv.role not in role_scores_history:
            role_scores_history[inv.role] = []
        role_scores_history[inv.role].append(r.overall_score)
        
        # Add topic scores
        try:
            topic_perf = json.loads(r.topic_performance_json)
            for topic, score in topic_perf.items():
                if topic not in topic_scores_history:
                    topic_scores_history[topic] = []
                topic_scores_history[topic].append(score)
        except Exception as e:
            print(f"Error parsing topic performance from report {r.id}: {e}")
            
    # 3. Calculate Topic Mastery Map (Attempts, Averages, Latest, and Trend Direction)
    topic_mastery = {}
    for topic, scores in topic_scores_history.items():
        attempts = len(scores)
        latest_score = scores[-1]
        avg_score = sum(scores) / attempts
        
        # Trend calculation
        if attempts >= 2:
            preceding_avg = sum(scores[:-1]) / (attempts - 1)
            if latest_score > preceding_avg:
                trend = "improving"
            elif latest_score < preceding_avg:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
            
        # Determine mastery state
        if avg_score < 60 or (avg_score < 70 and trend != "improving"):
            mastery_state = "Weak"
        elif avg_score >= 75 and trend != "declining":
            mastery_state = "Strong"
        else:
            mastery_state = "Improving"
            
        topic_mastery[topic] = {
            "average_score": round(avg_score, 1),
            "latest_score": latest_score,
            "attempts": attempts,
            "trend_direction": trend,
            "mastery_state": mastery_state
        }
        
    # 4. Calculate Role Performance Aggregations
    role_performance = {}
    for role, scores in role_scores_history.items():
        role_performance[role] = {
            "average_score": round(sum(scores) / len(scores), 1),
            "attempts": len(scores)
        }
        
    # 5. Calculate Confidence-Aware Readiness Scores
    readiness_scores = {}
    for role_name, profile in ROLE_PROFILES.items():
        core_topics = profile.get("topics", [])
        tested_count = 0
        total_score = 0
        
        for topic in core_topics:
            matched_topic = None
            for mastered_topic in topic_mastery:
                if is_topic_match(topic, mastered_topic):
                    matched_topic = mastered_topic
                    break
            
            if matched_topic:
                tested_count += 1
                total_score += topic_mastery[matched_topic]["average_score"]
            else:
                total_score += 50  # Baseline score for untested topics
                
        avg_readiness = total_score / len(core_topics) if core_topics else 50
        coverage_ratio = tested_count / len(core_topics) if core_topics else 0.0
        
        # Confidence calculation
        if coverage_ratio < 0.4:
            confidence = "low"
        elif coverage_ratio < 0.8:
            confidence = "medium"
        else:
            confidence = "high"
            
        readiness_scores[role_name] = {
            "score": int(avg_readiness),
            "confidence": confidence,
            "coverage_ratio": round(coverage_ratio, 2)
        }
        
    # 6. Generate Weakness-Based Interview Recommendations
    recommendations = []
    weak_topics = []
    
    # Identify weak or improving topics needing practice
    for topic, stats in topic_mastery.items():
        if stats.get("mastery_state") in ["Weak", "Improving"]:
            weak_topics.append((topic, stats))
            
    # Generate recommendations mapping weak topics to target practice profiles
    for topic, stats in weak_topics:
        suggested_roles = []
        for role_name, profile in ROLE_PROFILES.items():
            has_topic = False
            for core_topic in profile.get("topics", []):
                if is_topic_match(topic, core_topic):
                    has_topic = True
                    break
            if has_topic:
                suggested_roles.append(role_name)
                
        reason = f"Your average score in {topic} is low ({stats['average_score']}%)."
        if stats["trend_direction"] == "declining":
            reason = f"Your performance in {topic} is declining (latest: {stats['latest_score']}%)."
            
        for role in suggested_roles[:2]:  # Limit suggestions to top 2 roles testing the topic
            recommendations.append({
                "type": "targeted_practice",
                "role": role,
                "focus_topics": [topic],
                "reason": reason
            })
            
    # Default recommendations if profile is fresh or no weaknesses are present
    if not recommendations:
        recommendations.append({
            "type": "general_practice",
            "role": "AI Engineer",
            "focus_topics": ["Machine Learning", "Generative AI"],
            "reason": "Welcome! Complete your first interview session to start constructing your knowledge profile."
        })
        
    # 7. Persist or Update UserProfile record in DB
    stmt_profile = select(UserProfile).where(UserProfile.user_id == user_id)
    profile_record = db.exec(stmt_profile).first()
    
    if not profile_record:
        import uuid
        profile_record = UserProfile(
            id=str(uuid.uuid4()),
            user_id=user_id
        )
        
    profile_record.topic_mastery_json = json.dumps(topic_mastery)
    profile_record.readiness_scores_json = json.dumps(readiness_scores)
    profile_record.role_performance_json = json.dumps(role_performance)
    profile_record.history_trends_json = json.dumps(history_trends)
    profile_record.recommendations_json = json.dumps(recommendations)
    profile_record.last_updated = datetime.utcnow()
    
    db.add(profile_record)
    db.commit()
    db.refresh(profile_record)
    return profile_record
