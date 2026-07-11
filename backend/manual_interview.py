import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Ensure backend directory is in the Python search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environmental variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from langchain_core.messages import AIMessage, HumanMessage
from app.agents.interview_agent import interview_agent

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_interview.log")

def create_base_state():
    return {
        "messages": [],
        "role": "AI Engineer",
        "difficulty": "medium",
        "duration_minutes": 10,
        "question_count": 0,
        "max_question_count": 6,
        "status": "in_progress",
        "current_question": "",
        "covered_topics": [],
        "missing_topics": ["PyTorch", "Deep Learning", "Transformers"],
        "score_history": [],
        "company_name": "Target Company",
        "topic_tree": {
            "Machine Learning": {
                "concepts": {
                    "Deep Neural Networks": {
                        "sub_concepts": ["Backpropagation", "Activations"]
                    }
                }
            }
        },
        "concept_coverage": {
            "Deep Neural Networks": "uncovered",
            "Backpropagation": "uncovered",
            "Activations": "uncovered"
        },
        "interview_objectives": {
            "must_verify": {
                "Project Ownership": {
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
                },
                "System Understanding": {
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
            },
            "nice_to_verify": {
                "Decision & Tradeoff Thinking": {
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
                },
                "Behavioral & Communication": {
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
            }
        },
        "knowledge_model": {
            "proven_skills": [],
            "weak_skills": [],
            "unproven_claims": [],
            "understanding_styles": [],
            "evaluation_history": []
        },
        "project_investigation": {
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
        },
        "last_question_concepts": [],
        "interview_phase": "INTRODUCTION",
        "debug_dashboard": None,
        "objective_turns_spent": {},
        "project_turns_spent": {},
        "failed_attempts_per_concept": {},
        "category_counts": {
            "project": 0,
            "technical": 0,
            "behavioral": 0
        },
        "question_bucket_history": []
    }

def log_turn(turn_num, phase, strategy, style, bucket, objective, confidence, question, reasoning, state=None, answer=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"==================================================\n"
        f"TURN {turn_num} DECISION LOG\n"
        f"==================================================\n"
        f"Timestamp:          {timestamp}\n"
        f"Interview Phase:    {phase}\n"
        f"Strategy Selected:  {strategy}\n"
        f"Question Style:     {style}\n"
        f"Question Bucket:    {bucket}\n"
        f"Active Objective:   {objective}\n"
        f"Objective Confidence: {confidence}%\n"
    )
    if state:
        log_entry += f"Objective Turns Spent: {state.get('objective_turns_spent')}\n"
        log_entry += f"Project Turns Spent:   {state.get('project_turns_spent')}\n"
        log_entry += f"Category Counts:       {state.get('category_counts')}\n"
        proj_inv = state.get("project_investigation", {})
        if proj_inv.get("in_mode"):
            log_entry += f"Project Investigation Mode: Active ({proj_inv.get('project_name')})\n"
            log_entry += f"Project Verification Plan:  {proj_inv.get('verification_plan')}\n"
        log_entry += f"Weak Skills Catalog:   {state.get('knowledge_model', {}).get('weak_skills', [])}\n"
        
    log_entry += (
        f"Reasoning Summary:  {reasoning}\n"
        f"Generated Question: {question}\n"
    )
    if answer is not None:
        log_entry += f"Candidate Answer:   {answer}\n"
    log_entry += "==================================================\n\n"
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def main():
    # Clear previous logs
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        
    print("==================================================")
    print("      STARTING MANUAL AI TECHNICAL INTERVIEW      ")
    print("==================================================")
    print(f"Decision logs will be saved to: {LOG_FILE}\n")
    
    state = create_base_state()
    turn_num = 1
    
    while True:
        # Run agent to get next question/metrics
        print("\n[Thinking...] Running Interview Agent...")
        result = interview_agent.invoke(state)
        
        # Update our active state with agent return values
        state.update(result)
        
        # Extract variables for printing and logging
        phase = state.get("interview_phase")
        strategy = state.get("action")
        db_dash = state.get("debug_dashboard", {}) or {}
        objective = db_dash.get("objective", "N/A")
        confidence = db_dash.get("confidence", 0)
        style = db_dash.get("question_style", "N/A")
        bucket = db_dash.get("question_bucket", "N/A")
        question = state.get("current_question")
        reasoning = state.get("reasoning_summary", "N/A")
        
        # Print decision metadata to console
        print(f"\n--- Turn {turn_num} Decision Metadata ---")
        print(f"  * Phase:      {phase}")
        print(f"  * Strategy:   {strategy}")
        print(f"  * Style:      {style}")
        print(f"  * Bucket:     {bucket}")
        print(f"  * Objective:  {objective}")
        print(f"  * Confidence: {confidence}%")
        print(f"  * Objective Turns Spent: {state.get('objective_turns_spent')}")
        print(f"  * Project Turns Spent:   {state.get('project_turns_spent')}")
        print(f"  * Category Counts:       {state.get('category_counts')}")
        proj_inv = state.get("project_investigation", {})
        if proj_inv.get("in_mode"):
            print(f"  * Project Investigation: {proj_inv.get('project_name')} (Turns: {state.get('project_turns_spent', {}).get(proj_inv.get('project_name'), 0)})")
            print(f"  * Project Verification Plan: {proj_inv.get('verification_plan')}")
        print(f"  * Weak Skills Catalog:   {state.get('knowledge_model', {}).get('weak_skills', [])}")
        print(f"  * Reasoning:  {reasoning}")
        print("----------------------------------------")
        
        # Print the question
        print(f"\nInterviewer: {question}")
        
        # If wrap_up or completed, exit
        if state.get("status") == "completed" or phase == "WRAP_UP":
            log_turn(turn_num, phase, strategy, style, bucket, objective, confidence, question, reasoning, state)
            print("\nInterview completed. Thank you!")
            break
            
        # Get human response
        try:
            answer = input("\nYou: ").strip()
            while not answer:
                answer = input("You (please provide an answer): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nInterview aborted.")
            break
            
        # Log turn details to file
        log_turn(turn_num, phase, strategy, style, bucket, objective, confidence, question, reasoning, state, answer)
        
        # Update messages list and counters in the state
        state["messages"].append(HumanMessage(content=answer))
        
        turn_num += 1

if __name__ == "__main__":
    main()
