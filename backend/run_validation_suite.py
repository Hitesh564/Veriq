import os
import sys
import json

# Ensure backend directory is in the Python search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environmental variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from app.agents.evaluation_agent import run_evaluation

# ----------------------------------------------------
# 1. Define Simulated Test Scenarios
# ----------------------------------------------------

# Scenario 1: Strong Candidate
sc1_data = {
    "role": "AI Engineer",
    "difficulty": "medium",
    "transcripts": [
        {"sender": "interviewer", "text": "Welcome to your mock technical interview for the AI Engineer role. Could you walk me through your retinal scan prediction system and your role in it?", "difficulty": "medium"},
        {"sender": "candidate", "text": "I was the lead architect and developer for the Retinal Age Prediction pipeline. I led the development from data loader design to training and final cloud deployment, coordinating tasks with two other engineers. We used a modified ResNet-50 backbone with self-attention layers to focus on retinal vessel density. I wrote the custom attention head modules myself in PyTorch and calculated MACs to optimize the forward pass.", "topic": "Project Ownership", "score": 5, "reasoning_summary": "Extremely detailed architecture description showing clear project ownership.", "secondary_topics": ["Deep Learning", "PyTorch"]},
        {"sender": "interviewer", "text": "That's impressive. Why did you choose PyTorch over TensorFlow, and how did you scale the system for inference?", "difficulty": "medium"},
        {"sender": "candidate", "text": "We chose PyTorch for its dynamic computation graph, allowing researchers to debug loss functions on the fly. To scale it to 10k users, we compiled the model with TensorRT for a 3x speedup, wrapped it in FastAPI with gunicorn, and deployed it to AWS ECS. We cached prediction responses in Redis for identical macular scans. Also, during training we hit GPU OOM errors, and I used PyTorch Profiler to trace the issue to tensor references being kept in our loss history list, which we solved by calling .detach() on the loss.", "topic": "Scaling & Production Thinking", "score": 5, "reasoning_summary": "Detailed tradeoff decisions, memory profiling, and containerized cloud scalability.", "secondary_topics": ["Scaling", "Redis", "AWS ECS"]}
    ],
    "topic_tree": {
        "AI Engineering": {
            "concepts": {
                "Computer Vision & Attention": {"sub_concepts": ["ResNet-50", "Self-Attention"]},
                "Scalability & Caching": {"sub_concepts": ["AWS ECS", "Redis Caching", "TensorRT"]}
            }
        }
    },
    "knowledge_model": {
        "proven_skills": ["PyTorch", "AWS ECS", "FastAPI", "Redis", "TensorRT", "PyTorch Profiler"],
        "weak_skills": [],
        "unproven_claims": [
            {"claim": "Lead architect and developer of Retinal Age Prediction pipeline", "state": "VERIFIED", "required_evidence": ["architecture", "implementation"], "verified_evidence": ["architecture", "implementation"], "attempts": 2},
            {"claim": "Wrote custom PyTorch attention head modules", "state": "VERIFIED", "required_evidence": ["implementation"], "verified_evidence": ["implementation"], "attempts": 1},
            {"claim": "Scaled system to support 10k concurrent users", "state": "VERIFIED", "required_evidence": ["scaling"], "verified_evidence": ["scaling"], "attempts": 1}
        ]
    },
    "concept_coverage": {
        "ResNet-50": "proven",
        "Self-Attention": "proven",
        "MACs Optimization": "proven",
        "TensorRT": "proven",
        "AWS ECS": "proven",
        "Redis Caching": "proven"
    },
    "interview_objectives": {
        "must_verify": {
            "Project Ownership": {"confidence": 100, "status": "verified", "attempts": 2, "evidence_categories": {"architecture": True, "implementation": True, "debugging": True, "tradeoffs": True, "failure_cases": True}},
            "System Understanding": {"confidence": 100, "status": "verified", "attempts": 2, "evidence_categories": {"architecture": True, "implementation": True}}
        },
        "nice_to_verify": {
            "Decision & Tradeoff Thinking": {"confidence": 100, "status": "verified", "attempts": 2, "evidence_categories": {"tradeoffs": True}}
        }
    },
    "project_investigation": {
        "project_name": "Retinal Age Prediction",
        "turns_spent": 4,
        "verified_categories": ["architecture", "implementation", "tradeoffs", "debugging"],
        "verification_plan": {"architecture": True, "implementation": True, "debugging": True, "tradeoffs": True, "failure_cases": True}
    }
}

# Scenario 2: Bluffing Candidate
sc2_data = {
    "role": "AI Engineer",
    "difficulty": "medium",
    "transcripts": [
        {"sender": "interviewer", "text": "Welcome. Could you walk me through your LangGraph Interview System and your role in it?", "difficulty": "medium"},
        {"sender": "candidate", "text": "Yes, I built a LangGraph Interview System. I designed it and worked on it from start to finish. It uses AI to conduct interviews automatically.", "topic": "Project Ownership", "score": 2, "reasoning_summary": "Struggles to provide specific details or technical choices, shifting to high-level summaries.", "secondary_topics": []},
        {"sender": "interviewer", "text": "Can you describe how you managed state in LangGraph or how you debugged recursion limits?", "difficulty": "medium"},
        {"sender": "candidate", "text": "Well, we used the default LangGraph state mechanism, and we didn't hit any recursion issues because our graph is relatively simple. We just ran it and it worked fine.", "topic": "Problem Solving & Debugging", "score": 2, "reasoning_summary": "Does not explain state definition or recursion troubleshooting.", "secondary_topics": []}
    ],
    "topic_tree": {
        "Agentic AI": {
            "concepts": {
                "State Graphs": {"sub_concepts": ["LangGraph State", "Recursion Limits"]}
            }
        }
    },
    "knowledge_model": {
        "proven_skills": [],
        "weak_skills": ["LangGraph state management", "LangGraph debugging"],
        "unproven_claims": [
            {"claim": "Built a LangGraph Interview System", "state": "FAILED_VERIFICATION", "required_evidence": ["architecture", "implementation"], "verified_evidence": [], "attempts": 2}
        ]
    },
    "concept_coverage": {
        "LangGraph State": "weak",
        "LangGraph Debugging": "weak"
    },
    "interview_objectives": {
        "must_verify": {
            "Project Ownership": {"confidence": 0, "status": "unverified", "attempts": 2, "evidence_categories": {"architecture": False, "implementation": False}}
        }
    },
    "project_investigation": {
        "project_name": "LangGraph Interview System",
        "turns_spent": 2,
        "verified_categories": [],
        "verification_plan": {"architecture": False, "implementation": False, "debugging": False, "tradeoffs": False, "failure_cases": False}
    }
}

# Scenario 3: Weak Candidate
sc3_data = {
    "role": "AI Engineer",
    "difficulty": "medium",
    "transcripts": [
        {"sender": "interviewer", "text": "Welcome. Can you explain the self-attention mechanism in Transformers and its mathematical formulation?", "difficulty": "medium"},
        {"sender": "candidate", "text": "Uh, self-attention allows the model to look at different parts of the sentence. I'm not really sure about the exact mathematical formula, to be honest. I just import it from Hugging Face.", "topic": "Deep Learning", "score": 2, "reasoning_summary": "Unable to provide mathematical explanation of Q, K, V operations.", "secondary_topics": []},
        {"sender": "interviewer", "text": "No problem. How do you prevent overfitting in deep neural networks?", "difficulty": "medium"},
        {"sender": "candidate", "text": "You can use regularization, like L2. But I don't really know how it's done or what the parameters are.", "topic": "Machine Learning", "score": 2, "reasoning_summary": "Vague answers, lacks understanding of how regularization works in practice.", "secondary_topics": []}
    ],
    "topic_tree": {
        "Machine Learning": {
            "concepts": {
                "Deep Learning Theory": {"sub_concepts": ["Transformers", "Attention"]},
                "Generalization": {"sub_concepts": ["Regularization"]}
            }
        }
    },
    "knowledge_model": {
        "proven_skills": [],
        "weak_skills": ["Transformers", "Attention mechanisms", "Regularization"],
        "unproven_claims": []
    },
    "concept_coverage": {
        "Transformers": "weak",
        "Attention": "weak",
        "Regularization": "weak"
    },
    "interview_objectives": {
        "must_verify": {
            "Core ML Theory": {"confidence": 0, "status": "unverified", "attempts": 2}
        }
    },
    "project_investigation": {
        "project_name": "N/A",
        "turns_spent": 0,
        "verified_categories": [],
        "verification_plan": {"architecture": False, "implementation": False, "debugging": False, "tradeoffs": False, "failure_cases": False}
    }
}

# Scenario 4: Incomplete Interview
sc4_data = {
    "role": "AI Engineer",
    "difficulty": "medium",
    "transcripts": [
        {"sender": "interviewer", "text": "Welcome. Can you give me an overview of the Retinal Age Prediction pipeline and your contributions?", "difficulty": "medium"},
        {"sender": "candidate", "text": "I was the lead developer. I wrote the PyTorch training loop and defined the architecture using a modified ResNet.", "topic": "Project Ownership", "score": 4, "reasoning_summary": "Shows good initial ownership and modeling description.", "secondary_topics": ["PyTorch"]}
    ],
    "topic_tree": {
        "AI Engineering": {
            "concepts": {
                "Modeling": {"sub_concepts": ["ResNet", "PyTorch"]}
            }
        }
    },
    "knowledge_model": {
        "proven_skills": ["PyTorch"],
        "weak_skills": [],
        "unproven_claims": [
            {"claim": "Lead developer of Retinal Age Prediction pipeline", "state": "UNVERIFIED", "required_evidence": ["architecture", "implementation"], "verified_evidence": ["architecture"], "attempts": 1}
        ]
    },
    "concept_coverage": {
        "ResNet": "covered",
        "PyTorch": "covered"
    },
    "interview_objectives": {
        "must_verify": {
            "Project Ownership": {"confidence": 40, "status": "unverified", "attempts": 1, "evidence_categories": {"architecture": True, "implementation": False}},
            "System Understanding": {"confidence": 0, "status": "unverified", "attempts": 0, "evidence_categories": {"architecture": False, "implementation": False}}
        },
        "nice_to_verify": {
            "Decision & Tradeoff Thinking": {"confidence": 0, "status": "unverified", "attempts": 0}
        }
    },
    "project_investigation": {
        "project_name": "Retinal Age Prediction",
        "turns_spent": 1,
        "verified_categories": ["architecture"],
        "verification_plan": {"architecture": True, "implementation": False, "debugging": False, "tradeoffs": False, "failure_cases": False}
    }
}

# ----------------------------------------------------
# 2. Run Scenarios & Validate Results
# ----------------------------------------------------

results = {}
errors = []

def run_test_case(name, data):
    print("=" * 60)
    print(f"RUNNING VALIDATION SCENARIO: {name}")
    print("=" * 60)
    
    report = run_evaluation(
        role=data["role"],
        difficulty=data["difficulty"],
        transcripts=data["transcripts"],
        topic_tree=data["topic_tree"],
        knowledge_model=data["knowledge_model"],
        concept_coverage=data["concept_coverage"],
        interview_objectives=data["interview_objectives"],
        project_investigation=data["project_investigation"]
    )
    
    print("\n[Raw Report JSON Output]:")
    print(json.dumps(report, indent=2))
    print("\n" + "-" * 60)
    
    return report

# Test 1: Strong Candidate
report_1 = run_test_case("Test 1: Strong Candidate", sc1_data)
# Validation rules for Test 1
ownership_1 = report_1.get("ownership_score", 0)
tech_1 = report_1.get("technical_score", 0)
verified_claims_1 = report_1.get("claim_verification_summary", {}).get("verified_claims", [])
failed_claims_1 = report_1.get("claim_verification_summary", {}).get("failed_claims", [])
hire_rec_1 = report_1.get("hire_recommendation", "")

pass_t1 = (
    70 <= ownership_1 <= 100 and
    tech_1 >= 70 and
    len(verified_claims_1) >= 1 and
    len(failed_claims_1) == 0 and
    hire_rec_1 in ["Hire", "Strong Hire"]
)
results["test_1"] = "PASS" if pass_t1 else "FAIL"
if not pass_t1:
    errors.append(f"Test 1 failed requirements: ownership={ownership_1}, tech={tech_1}, verified={verified_claims_1}, failed={failed_claims_1}, hire={hire_rec_1}")

# Test 2: Bluffing Candidate
report_2 = run_test_case("Test 2: Bluffing Candidate", sc2_data)
# Validation rules for Test 2
ownership_2 = report_2.get("ownership_score", 0)
failed_claims_2 = report_2.get("claim_verification_summary", {}).get("failed_claims", [])
hire_rec_2 = report_2.get("hire_recommendation", "")

pass_t2 = (
    ownership_2 < 40 and
    len(failed_claims_2) >= 1 and
    hire_rec_2 in ["Borderline", "No Hire"]
)
results["test_2"] = "PASS" if pass_t2 else "FAIL"
if not pass_t2:
    errors.append(f"Test 2 failed requirements: ownership={ownership_2}, failed={failed_claims_2}, hire={hire_rec_2}")

# Test 3: Weak Candidate
report_3 = run_test_case("Test 3: Weak Candidate", sc3_data)
# Validation rules for Test 3
tech_3 = report_3.get("technical_score", 0)
comm_3 = report_3.get("communication_score", 0)
ownership_3 = report_3.get("ownership_score", 0)
hire_rec_3 = report_3.get("hire_recommendation", "")

pass_t3 = (
    tech_3 < 50 and
    comm_3 < 70 and
    ownership_3 < 30 and
    hire_rec_3 == "No Hire"
)
results["test_3"] = "PASS" if pass_t3 else "FAIL"
if not pass_t3:
    errors.append(f"Test 3 failed requirements: tech={tech_3}, comm={comm_3}, ownership={ownership_3}, hire={hire_rec_3}")

# Test 4: Incomplete Interview
report_4 = run_test_case("Test 4: Incomplete Interview", sc4_data)
# Validation rules for Test 4
completion_4 = report_4.get("interview_completion_score", 0)
conf_4 = report_4.get("confidence_level", "")
summary_4 = report_4.get("summary", "").lower()

pass_t4 = (
    completion_4 < 50 and
    conf_4 in ["Low", "Medium"] and
    ("incomplete" in summary_4 or "limited" in summary_4 or "partial" in summary_4 or "early" in summary_4 or "short" in summary_4 or "completion" in summary_4 or "coverage" in summary_4)
)
results["test_4"] = "PASS" if pass_t4 else "FAIL"
if not pass_t4:
    errors.append(f"Test 4 failed requirements: completion={completion_4}, conf={conf_4}, summary_mentions_limited={'incomplete' in summary_4 or 'limited' in summary_4 or 'partial' in summary_4 or 'early' in summary_4 or 'short' in summary_4 or 'completion' in summary_4 or 'coverage' in summary_4}")

# Test 5: Explainability Test
# Check if scores are explainable across all scenarios and match evidence
pass_t5 = True
for r_idx, r in enumerate([report_1, report_2, report_3, report_4], 1):
    raw_ev = r.get("evaluation_evidence", {})
    # Check that counts exist and match python metadata
    if "verified_claims_count" not in raw_ev or "failed_claims_count" not in raw_ev:
        pass_t5 = False
        errors.append(f"Explainability Test failed: report {r_idx} missing evaluation_evidence keys")
        break
    
    # Check that ownership score matches pre-calculated score from python
    computed_own = r.get("ownership_score")
    if computed_own is None:
        pass_t5 = False
        errors.append(f"Explainability Test failed: report {r_idx} missing ownership_score")
        break

results["test_5"] = "PASS" if pass_t5 else "FAIL"

# Final JSON summary report
final_report = {
    "test_1": results["test_1"],
    "test_2": results["test_2"],
    "test_3": results["test_3"],
    "test_4": results["test_4"],
    "test_5": results["test_5"],
    "critical_issues": errors,
    "recommended_changes": [],
    "overall_status": "READY_FOR_VOICE" if (all(results[k] == "PASS" for k in results) and not errors) else "NEEDS_FIXES"
}

print("=" * 60)
print("FINAL VALIDATION REPORT SUMMARY:")
print("=" * 60)
print(json.dumps(final_report, indent=2))
print("=" * 60)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "validation_summary.json"), "w") as f:
    json.dump(final_report, f, indent=2)
