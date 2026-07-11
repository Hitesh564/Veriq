import os
import sys
import json
import time
from dotenv import load_dotenv

# Ensure backend directory is in the Python search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environmental variables from .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from app.agents.interview_agent import interview_agent
from langchain_core.messages import AIMessage, HumanMessage

# Define candidate profiles and their answers corresponding to the active objective
CANDIDATE_PROFILES = {
    "senior_builder": {
        "name": "Alex (Well-rounded Senior Builder)",
        "resume": "Alex has 5 years of experience building machine learning applications in PyTorch. Stated project: Retinal Age Prediction pipeline.",
        "answers": {
            "Project Ownership": "I was the lead architect and developer for the Retinal Age Prediction pipeline. I led the development from data loader design to training and final cloud deployment, coordinating tasks with two other engineers.",
            "System Understanding": "We used a ResNet-50 backbone modified with self-attention layers to focus on retinal vessel density. I wrote custom PyTorch modules for the attention heads and calculated MACs to optimize the forward pass.",
            "Decision & Tradeoff Thinking": "I chose PyTorch over TensorFlow because of its dynamic computation graph, which allowed us to debug custom layers on the fly. We traded off some inference speed, which we recovered by compiling with TensorRT for deployment.",
            "Problem Solving & Debugging": "During training, we hit GPU out-of-memory errors. I used PyTorch Profiler and traced the issue to tensor references being kept in our loss history list. Calling `.detach()` on the loss solved the leak.",
            "Scaling & Production Thinking": "To scale prediction requests to 10k users, I deployed the model on AWS ECS using a FastAPI wrapper with gunicorn workers, and set up Redis to cache predictions for identical macular scans.",
            "Behavioral & Communication": "When a dataset delivery was delayed by three weeks, I immediately conducted a risk analysis, presented it to the product team, and scoped down our secondary objectives to hit our launch date."
        }
    },
    "theory_memorizer": {
        "name": "Bob (Theoretical Memorizer - lacks practical experience)",
        "resume": "Bob has a Master's degree in CS. Familiar with neural networks, scaling, and system design.",
        "answers": {
            "Project Ownership": "I was a developer on a Retinal Age Prediction project. The team worked together on it. I helped write the code, and we all shared responsibilities for running the experiments.",
            "System Understanding": "A neural network is composed of input, hidden, and output layers. It uses weights, biases, and activation functions like ReLU. ResNet uses residual connections to prevent vanishing gradients.",
            "Decision & Tradeoff Thinking": "PyTorch is a Python library for machine learning. TensorFlow is also a library. People say PyTorch is better for research and TensorFlow is better for production deployment.",
            "Problem Solving & Debugging": "When code has a bug, I use print statements or a debugger to trace the execution and fix the error. Usually it is a syntax error or a shape mismatch.",
            "Scaling & Production Thinking": "Scaling is about handling more traffic. You can scale horizontally by adding more servers or vertically by upgrading server RAM. Load balancers distribute requests.",
            "Behavioral & Communication": "I communicate very well. I always attend team meetings and discuss our updates with the manager and other developers."
        }
    },
    "practical_coder": {
        "name": "Charlie (Practical Coder - struggles with theory/scaling)",
        "resume": "Charlie has built several personal projects and bootcamps. Stated project: Retinal Age Prediction pipeline.",
        "answers": {
            "Project Ownership": "I built the whole Retinal Age Prediction project myself. I wrote all the files, created the training loop, and ran it on my local laptop GPU.",
            "System Understanding": "I just imported ResNet from torchvision and ran it. I don't know the exact math of the skip connections, but it got 90% accuracy on our test set.",
            "Decision & Tradeoff Thinking": "I used PyTorch because I learned it in a tutorial. I didn't think about TensorFlow or other options. It worked fine for me.",
            "Problem Solving & Debugging": "The code crashed with a shape mismatch error in the linear layer. I fixed it by printing the tensor shape and changing the linear layer input features to match the output of the conv layer.",
            "Scaling & Production Thinking": "I haven't run this on large servers or handled high traffic. It was just running on my local machine. I guess we would deploy it to AWS if we wanted to scale it.",
            "Behavioral & Communication": "I like coding. I prefer writing code to talking about it in meetings. I get the work done and push it to git."
        }
    }
}

def simulate_interview(profile_key):
    profile = CANDIDATE_PROFILES[profile_key]
    print(f"\n======================================================================")
    print(f" SIMULATING INTERVIEW FOR: {profile['name']}")
    print(f" Resume Context: {profile['resume']}")
    print(f"======================================================================\n")
    
    # Initialize state
    topic_tree = {
        "Machine Learning": {
            "concepts": {
                "Deep Neural Networks": {
                    "sub_concepts": ["Backpropagation", "Activations"]
                }
            }
        },
        "Python": {
            "concepts": {
                "OOP Programming": {
                    "sub_concepts": ["Inheritance", "Polymorphism"]
                }
            }
        }
    }
    concept_coverage = {
        "Deep Neural Networks": "uncovered",
        "Backpropagation": "uncovered",
        "Activations": "uncovered",
        "OOP Programming": "uncovered",
        "Inheritance": "uncovered",
        "Polymorphism": "uncovered"
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
    import copy
    interview_objectives = {
        "must_verify": {
            "Project Ownership": copy.deepcopy(default_obj_structure),
            "System Understanding": copy.deepcopy(default_obj_structure),
            "Problem Solving & Debugging": copy.deepcopy(default_obj_structure)
        },
        "nice_to_verify": {
            "Decision & Tradeoff Thinking": copy.deepcopy(default_obj_structure),
            "Scaling & Production Thinking": copy.deepcopy(default_obj_structure),
            "Behavioral & Communication": copy.deepcopy(default_obj_structure)
        }
    }
    knowledge_model = {
        "proven_skills": [],
        "weak_skills": [],
        "unproven_claims": [],
        "understanding_styles": [],
        "evaluation_history": []
    }
    project_investigation = {
        "in_mode": False,
        "project_name": None,
        "verified_categories": [],
        "turns_spent": 0
    }
    
    state = {
        "messages": [],
        "role": "AI Engineer",
        "difficulty": "medium",
        "duration_minutes": 10,
        "question_count": 0,
        "max_question_count": 6,
        "status": "in_progress",
        "current_question": "",
        "covered_topics": [],
        "missing_topics": ["PyTorch", "Deep Learning", "System Design"],
        "score_history": [],
        "company_name": "Target Company",
        "topic_tree": topic_tree,
        "concept_coverage": concept_coverage,
        "interview_objectives": interview_objectives,
        "knowledge_model": knowledge_model,
        "project_investigation": project_investigation,
        "last_question_concepts": [],
        "interview_phase": "INTRODUCTION",
        "debug_dashboard": None
    }
    
    # Run loop
    for turn in range(1, 7):
        print(f"\n--- TURN {turn} ---")
        
        # Check API key configuration
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "placeholder_api_key" or api_key == "your_gemini_api_key_here":
            print("[ERROR] GEMINI_API_KEY is not set. Cannot run simulation.")
            return
            
        # Invoke agent to generate the question
        try:
            result = interview_agent.invoke(state)
        except Exception as e:
            print(f"[ERROR] Agent invocation failed: {e}")
            break
            
        interviewer_q = result.get("current_question", "")
        # Get active objective from interview objectives
        must_list = result.get("interview_objectives", {}).get("must_verify", {})
        nice_list = result.get("interview_objectives", {}).get("nice_to_verify", {})
        active_obj = "Project Ownership"
        for k, v in must_list.items():
            status = v.get("status", "unverified") if isinstance(v, dict) else v
            if status != "verified":
                active_obj = k
                break
        else:
            for k, v in nice_list.items():
                status = v.get("status", "unverified") if isinstance(v, dict) else v
                if status != "verified":
                    active_obj = k
                    break
        
        print(f"\n[Interviewer Target]: {active_obj}")
        print(f"[Interviewer Action]: {result.get('action', 'MOVE_TO_NEW_TOPIC')}")
        print(f"[Interviewer Question]: \"{interviewer_q}\"")
        
        if result.get("status") == "completed":
            print("\n[SUCCESS] Interview concluded successfully!")
            break
            
        # Get candidate response
        candidate_ans = profile["answers"].get(active_obj, "I don't have direct experience with that, but I would learn it.")
        print(f"[Candidate Response]: \"{candidate_ans}\"")
        
        # Update messages history in state
        new_messages = state["messages"] + [
            AIMessage(content=interviewer_q),
            HumanMessage(content=candidate_ans)
        ]
        
        # Update state for next turn
        state["messages"] = new_messages
        state["question_count"] = result.get("question_count", turn)
        state["topic_tree"] = result.get("topic_tree", topic_tree)
        state["concept_coverage"] = result.get("concept_coverage", concept_coverage)
        state["interview_objectives"] = result.get("interview_objectives", interview_objectives)
        state["knowledge_model"] = result.get("knowledge_model", knowledge_model)
        state["project_investigation"] = result.get("project_investigation", project_investigation)
        state["last_question_concepts"] = result.get("last_question_concepts", [])
        state["score_history"] = result.get("score_history", [])
        state["status"] = result.get("status", "in_progress")
        state["interview_phase"] = result.get("interview_phase", "INTRODUCTION")
        state["debug_dashboard"] = result.get("debug_dashboard", None)
        
        # Print updated evidence metrics
        print("\n--- Strategy Analysis ---")
        print(f"Evaluation Critique: {result.get('evaluation')}")
        print(f"Score (1-5): {result.get('score')}")
        print(f"Phase: {result.get('interview_phase')}")
        print(f"Debug Dashboard: {json.dumps(result.get('debug_dashboard'), indent=2)}")
        
        objs_str = json.dumps(state["interview_objectives"], indent=2)
        print(f"Objectives Progress:\n{objs_str}")
        
        km = state["knowledge_model"]
        print(f"Knowledge Model: Proven={len(km.get('proven_skills', []))}, Weak={len(km.get('weak_skills', []))}, Unproven Claims={len(km.get('unproven_claims', []))}")
        if km.get("unproven_claims"):
            for uc in km["unproven_claims"]:
                print(f"  - Claim: {uc['claim']} [State: {uc['state']}] (Project: {uc['project']})")
                
        # Sleep to prevent hitting free tier API rate limits
        time.sleep(4)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in CANDIDATE_PROFILES:
        simulate_interview(sys.argv[1])
    else:
        print("Please specify a candidate profile key to run:")
        print("  python backend/simulate_interviews.py senior_builder")
        print("  python backend/simulate_interviews.py theory_memorizer")
        print("  python backend/simulate_interviews.py practical_coder")
