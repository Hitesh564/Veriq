import os
import sys
import json
from dotenv import load_dotenv

# Ensure backend directory is in the Python search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environmental variables from .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Check API key configuration
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key or api_key == "placeholder_api_key" or api_key == "your_gemini_api_key_here":
    print("[ERROR] GEMINI_API_KEY is not configured in .env file. Cannot run test suite.")
    sys.exit(1)

from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.agents.interview_agent import interview_agent

# Global metrics tracking
api_calls_count = 0
total_prompt_tokens = 0
total_response_tokens = 0

# Monkeypatch ChatGoogleGenerativeAI to track API calls and token counts
original_invoke = ChatGoogleGenerativeAI.invoke

def wrapped_invoke(self, *args, **kwargs):
    global api_calls_count, total_prompt_tokens, total_response_tokens
    api_calls_count += 1
    
    response = original_invoke(self, *args, **kwargs)
    
    # Track tokens using the new usage_metadata if available, else fallback to response_metadata
    prompt_tokens = 0
    completion_tokens = 0
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        prompt_tokens = response.usage_metadata.get("input_tokens", 0)
        completion_tokens = response.usage_metadata.get("output_tokens", 0)
    else:
        meta = getattr(response, "response_metadata", {}) or {}
        token_usage = meta.get("token_usage", {}) or {}
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
    
    total_prompt_tokens += prompt_tokens
    total_response_tokens += completion_tokens
    
    print(f"    [Gemini Call Detail] Input Tokens: {prompt_tokens} | Output Tokens: {completion_tokens}")
    print(f"    [Gemini Response Content]: {response.content}")
    
    return response

ChatGoogleGenerativeAI.invoke = wrapped_invoke


def create_base_state():
    return {
        "messages": [],
        "role": "AI Engineer",
        "difficulty": "medium",
        "duration_minutes": 10,
        "question_count": 0,
        "max_question_count": 5,
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
            "turns_spent": 0
        },
        "last_question_concepts": [],
        "interview_phase": "INTRODUCTION",
        "debug_dashboard": None
    }


def print_turn_summary(test_name, result):
    # Retrieve details for printing
    phase = result.get("interview_phase")
    strategy = result.get("action")
    db_dash = result.get("debug_dashboard", {}) or {}
    confidence = db_dash.get("confidence", 0)
    claims_list = db_dash.get("claims", [])
    
    print(f"\n[{test_name} Summary]")
    print(json.dumps({
        "phase": phase,
        "strategy": strategy,
        "confidence": confidence,
        "claims": claims_list
    }, indent=2))
    print("=" * 60)


def run_tests():
    global api_calls_count, total_prompt_tokens, total_response_tokens
    
    print("==================================================")
    print("    RUNNING COMPONENT-LEVEL VERIFICATION TESTS    ")
    print("==================================================")
    
    # ----------------------------------------------------
    # TEST A: Claim Extraction
    # ----------------------------------------------------
    print("\n[TEST A] Claim Extraction...")
    state_a = create_base_state()
    state_a["messages"] = [
        AIMessage(content="Welcome to your mock interview. Tell me about yourself."),
        HumanMessage(content="I built a LangGraph RAG system.")
    ]
    state_a["question_count"] = 1
    state_a["interview_phase"] = "INTRODUCTION"
    
    result_a = interview_agent.invoke(state_a)
    unproven_claims = result_a["knowledge_model"]["unproven_claims"]
    
    # Verify claims list is not empty and extracts the LangGraph RAG claim
    claims_text = [c["claim"].lower() for c in unproven_claims]
    has_langgraph = any("langgraph" in text or "rag" in text for text in claims_text)
    
    print(f"    Unproven Claims Extracted: {unproven_claims}")
    assert len(unproven_claims) > 0, "Test A Failed: No claims were extracted."
    assert has_langgraph, "Test A Failed: Could not extract LangGraph RAG claim."
    print("    [PASS] Test A: Claim Extraction Succeeded!")
    print_turn_summary("Test A", result_a)

    # ----------------------------------------------------
    # TEST B: Project Detection
    # ----------------------------------------------------
    print("\n[TEST B] Project Detection...")
    # Using the same result from Test A since the input described a project
    in_mode = result_a["project_investigation"]["in_mode"]
    proj_name = result_a["project_investigation"]["project_name"]
    
    print(f"    Project Investigation Mode: {in_mode} | Project Name: {proj_name}")
    assert in_mode is True, "Test B Failed: Project investigation mode did not activate."
    assert proj_name is not None, "Test B Failed: Project name was not detected."
    print("    [PASS] Test B: Project Detection Succeeded!")
    print_turn_summary("Test B", result_a)

    # ----------------------------------------------------
    # TEST C: Phase Transition
    # ----------------------------------------------------
    print("\n[TEST C] Phase Transition...")
    # Verify that the phase transitions to PROJECT_DISCOVERY after Turn 0 response
    next_phase = result_a["interview_phase"]
    print(f"    Returning Interview Phase: {next_phase}")
    assert next_phase == "PROJECT_DISCOVERY", f"Test C Failed: Expected phase to transition to PROJECT_DISCOVERY, got {next_phase}."
    print("    [PASS] Test C: Phase Transition Succeeded!")
    print_turn_summary("Test C", result_a)

    # ----------------------------------------------------
    # TEST D: Strategy Selection
    # ----------------------------------------------------
    print("\n[TEST D] Strategy Selection...")
    state_d = create_base_state()
    # Mocking unverified project claim in state
    state_d["messages"] = [
        AIMessage(content="Welcome to your mock interview. Tell me about yourself."),
        HumanMessage(content="I built a LangGraph RAG system.")
    ]
    # Simulate Turn 1 transition
    state_d["interview_phase"] = "PROJECT_DISCOVERY"
    state_d["project_investigation"] = {
        "in_mode": True,
        "project_name": "LangGraph RAG system",
        "verified_categories": [],
        "turns_spent": 1
    }
    state_d["knowledge_model"]["unproven_claims"] = [
        {
            "claim": "I built a LangGraph RAG system",
            "decision": "",
            "project": "LangGraph RAG system",
            "state": "UNVERIFIED"
        }
    ]
    
    result_d = interview_agent.invoke(state_d)
    strategy = result_d["action"]
    print(f"    Selected Strategy Action: {strategy}")
    assert strategy in ["CHALLENGE_CLAIM", "PROBE_DEEPER", "REQUEST_EXAMPLE"], f"Test D Failed: Strategy was {strategy}."
    print("    [PASS] Test D: Strategy Selection Succeeded!")
    print_turn_summary("Test D", result_d)

    # ----------------------------------------------------
    # TEST E: Objective Confidence
    # ----------------------------------------------------
    print("\n[TEST E] Objective Confidence...")
    state_e = create_base_state()
    # Candidate provides strong architecture evidence
    state_e["messages"] = [
        AIMessage(content="Walk me through the architecture of your LangGraph RAG system."),
        HumanMessage(content="I designed a multi-agent routing graph in LangGraph where the main router uses query intent classifier to route to three specific sub-retriever nodes, optimizing retrieval latency.")
    ]
    state_e["interview_phase"] = "TECHNICAL_EVALUATION"
    # Ensure attempts is 0 initially
    state_e["interview_objectives"]["must_verify"]["Project Ownership"]["attempts"] = 0
    state_e["interview_objectives"]["must_verify"]["Project Ownership"]["confidence"] = 0
    
    result_e = interview_agent.invoke(state_e)
    obj_data = result_e["interview_objectives"]["must_verify"]["Project Ownership"]
    confidence = obj_data["confidence"]
    status = obj_data["status"]
    
    print(f"    Confidence: {confidence}% | Status: {status} | Attempts: {obj_data['attempts']}")
    assert confidence > 0, "Test E Failed: Objective confidence did not increase."
    assert status == "unverified", f"Test E Failed: Objective status is {status} instead of unverified on turn 1."
    print("    [PASS] Test E: Objective Confidence Succeeded!")
    print_turn_summary("Test E", result_e)

    # ----------------------------------------------------
    # TEST F: Question Generation
    # ----------------------------------------------------
    print("\n[TEST F] Question Generation...")
    state_f = create_base_state()
    state_f["messages"] = [
        AIMessage(content="What did you build?"),
        HumanMessage(content="I built a LangGraph Agent.")
    ]
    state_f["interview_phase"] = "TECHNICAL_EVALUATION"
    state_f["knowledge_model"]["unproven_claims"] = [
        {
            "claim": "Built LangGraph Agent",
            "decision": "",
            "project": "General",
            "state": "PROBED"  # challenging the claim
        }
    ]
    
    result_f = interview_agent.invoke(state_f)
    next_question = result_f["current_question"]
    print(f"    Generated Question: \"{next_question}\"")
    
    # The question should query the LangGraph Agent claim directly
    has_ref = "langgraph" in next_question.lower() or "agent" in next_question.lower()
    assert has_ref, f"Test F Failed: Question did not reference the challenged claim. Q: {next_question}"
    print("    [PASS] Test F: Question Generation Succeeded!")
    print_turn_summary("Test F", result_f)

    # ----------------------------------------------------
    # TEST G: Objective Verification Guard
    # ----------------------------------------------------
    print("\n[TEST G] Objective Verification Guard...")
    # Verify that a single strong response with high confidence does NOT trigger status verified
    # Setup state where confidence becomes high, but attempts is 0 initially (becoming 1 during node run)
    state_g = create_base_state()
    state_g["messages"] = [
        AIMessage(content="Can you explain the design decisions and tradeoffs of your LangGraph architecture?"),
        # Candidate covers multiple categories (architecture, implementation, tradeoffs) in one response
        HumanMessage(content="I structured the LangGraph as a cyclic graph to enable reflection. I implemented a fallback loop when retriever confidence drops below 0.7. The tradeoff was increased latency, but it improved accuracy by 25% which was critical.")
    ]
    state_g["interview_phase"] = "TECHNICAL_EVALUATION"
    state_g["interview_objectives"]["must_verify"]["Project Ownership"] = {
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
    
    result_g = interview_agent.invoke(state_g)
    obj_data_g = result_g["interview_objectives"]["must_verify"]["Project Ownership"]
    
    print(f"    Confidence: {obj_data_g['confidence']}% | Status: {obj_data_g['status']} | Attempts: {obj_data_g['attempts']}")
    assert obj_data_g["attempts"] == 1, f"Expected attempts count to be 1, got {obj_data_g['attempts']}"
    assert obj_data_g["status"] == "unverified", f"Test G Failed: Objective was verified on attempts = 1. Status: {obj_data_g['status']}"
    print("    [PASS] Test G: Objective Verification Guard Succeeded!")
    print_turn_summary("Test G", result_g)

    # ----------------------------------------------------
    # PRINT SUMMARY METRICS
    # ----------------------------------------------------
    print("\n==================================================")
    print("    API USAGE & METRIC LOGS")
    print("==================================================")
    print(f"Total Gemini API calls: {api_calls_count}")
    print(f"Total Prompt input tokens: {total_prompt_tokens}")
    print(f"Total Response output tokens: {total_response_tokens}")
    if api_calls_count > 0:
        print(f"Avg input tokens per call: {total_prompt_tokens // api_calls_count}")
        print(f"Avg output tokens per call: {total_response_tokens // api_calls_count}")
    print("==================================================")
    print("\nALL COMPONENT TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()
