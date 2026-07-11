import os
import sys
import json

# Define candidate profiles and their simulated responses per objective
CANDIDATE_PROFILES = {
    "senior_builder": {
        "name": "Alex (Well-rounded Senior Builder)",
        "resume": "Alex has 5 years of experience building machine learning applications in PyTorch. Stated project: Retinal Age Prediction pipeline.",
        "turns": [
            {
                "objective": "Project Ownership",
                "question": "Could you start by giving me an overview of the Retinal Age Prediction pipeline and your specific contributions to it?",
                "answer": "I was the lead architect and developer for the Retinal Age Prediction pipeline. I led the development from data loader design to training and final cloud deployment, coordinating tasks with two other engineers.",
                "extraction": {
                    "score": 5,
                    "evaluation": "Excellent evidence of end-to-end design and team leadership.",
                    "reasoning_summary": "Candidate clearly led the design, code implementation, and coordination, showcasing strong project ownership.",
                    "extracted_data": {
                        "claims": ["Lead architect and developer of the pipeline", "Coordinated tasks with two other engineers"],
                        "technologies": ["PyTorch"],
                        "decisions": ["Architected end-to-end pipeline from data loader to cloud deployment"],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": ["Successfully built and deployed retinal prediction pipeline"],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Project Ownership": 85
                    },
                    "proposed_hypotheses": [
                        {
                            "hypothesis": "Candidate has strong execution and project leadership experience.",
                            "status": "confirmed",
                            "reason": "Exhibits detailed architectural ownership of the core pipeline."
                        }
                    ]
                },
                "next_question_action": "PROBE_DEEPER",
                "next_question_topic": "PyTorch Attention Models",
                "next_question": "Now, let's talk about the models you implemented. How did you structure your neural network layers?"
            },
            {
                "objective": "System Understanding",
                "question": "Now, let's talk about the models you implemented. How did you structure your neural network layers?",
                "answer": "We used a ResNet-50 backbone modified with self-attention layers to focus on retinal vessel density. I wrote custom PyTorch modules for the attention heads and calculated MACs to optimize the forward pass.",
                "extraction": {
                    "score": 5,
                    "evaluation": "Shows deep model-level and layer-level mathematical awareness.",
                    "reasoning_summary": "Extremely detailed description of modifying ResNet backbones, implementing custom attention layers, and tracking computational complexity (MACs).",
                    "extracted_data": {
                        "claims": ["Modified ResNet-50 backbone with self-attention layers", "Wrote custom PyTorch attention head modules"],
                        "technologies": ["PyTorch", "ResNet-50"],
                        "decisions": ["Used modified ResNet-50 with attention for vessel density segmentation"],
                        "tradeoffs": ["MACs calculation to optimize forward pass"],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "System Understanding": 90
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "CHALLENGE",
                "next_question_topic": "Framework Choices",
                "next_question": "Why did you choose PyTorch over TensorFlow for this project? What were the main tradeoffs you encountered?"
            },
            {
                "objective": "Decision & Tradeoff Thinking",
                "question": "Why did you choose PyTorch over TensorFlow for this project? What were the main tradeoffs you encountered?",
                "answer": "I chose PyTorch over TensorFlow because of its dynamic computation graph, which allowed our researchers to debug custom loss functions on the fly. We traded off some inference speed, which we recovered by compiling with TensorRT for deployment.",
                "extraction": {
                    "score": 5,
                    "evaluation": "Excellent comparison of frameworks and concrete production optimizations.",
                    "reasoning_summary": "Clear understanding of research developer experience (dynamic graph) vs production deployment speed, showing strong tradeoff thinking.",
                    "extracted_data": {
                        "claims": ["We traded off research flexibility with inference speed"],
                        "technologies": ["TensorFlow", "TensorRT"],
                        "decisions": ["Chose PyTorch over TensorFlow for research debugging", "Compiled model with TensorRT for production speed"],
                        "tradeoffs": ["Dynamic computation graph flexibility vs static optimization compiler speed"],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": ["Optimized inference speed via TensorRT compiler"],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Decision & Tradeoff Thinking": 95
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "CHALLENGE",
                "next_question_topic": "Error Handling",
                "next_question": "Can you describe a challenging bug or system error you encountered during training, and how you tracked it down?"
            },
            {
                "objective": "Problem Solving & Debugging",
                "question": "Can you describe a challenging bug or system error you encountered during training, and how you tracked it down?",
                "answer": "During training, we hit GPU out-of-memory errors. I used PyTorch Profiler and traced the issue to tensor references being kept in our loss history list. Calling `.detach()` on the loss solved the leak.",
                "extraction": {
                    "score": 5,
                    "evaluation": "Outstanding problem-solving details and familiarity with profiling tools.",
                    "reasoning_summary": "Direct experience debugging PyTorch memory leak via PyTorch Profiler and detaching graph history tensors.",
                    "extracted_data": {
                        "claims": ["Encountered and solved GPU out-of-memory leaks"],
                        "technologies": ["PyTorch Profiler"],
                        "decisions": [],
                        "tradeoffs": [],
                        "failures": ["GPU out-of-memory error during custom training loops"],
                        "debugging_experiences": ["Traced leak via PyTorch Profiler and detached loss tensors using .detach()"],
                        "achievements": ["Resolved training memory leak"],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Problem Solving & Debugging": 90
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "STRESS_TEST",
                "next_question_topic": "System Scaling",
                "next_question": "How did you scale this retinal scan prediction system to support high request throughput?"
            },
            {
                "objective": "Scaling & Production Thinking",
                "question": "How did you scale this retinal scan prediction system to support high request throughput?",
                "answer": "To scale prediction requests to 10k users, I deployed the model on AWS ECS using a FastAPI wrapper with gunicorn workers, and set up Redis to cache predictions for identical macular scans.",
                "extraction": {
                    "score": 5,
                    "evaluation": "Solid backend scaling strategy combining container orchestration and caching.",
                    "reasoning_summary": "Logical production design using FastAPI, gunicorn scaling, container deployment, and Redis caching.",
                    "extracted_data": {
                        "claims": ["Scaled system to support 10k concurrent users"],
                        "technologies": ["AWS ECS", "FastAPI", "gunicorn", "Redis"],
                        "decisions": ["Deployed FastAPI on AWS ECS", "Used Redis to cache identical retinal scans"],
                        "tradeoffs": ["Cached scan results to save computation cost at the expense of memory"],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": ["Configured ECS and Redis caching layer to handle 10k user requests"],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Scaling & Production Thinking": 85
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "PROBE_DEEPER",
                "next_question_topic": "Project Delivery",
                "next_question": "Describe a situation where project timelines were compressed. How did you coordinate with stakeholders?"
            },
            {
                "objective": "Behavioral & Communication",
                "question": "Describe a situation where project timelines were compressed. How did you coordinate with stakeholders?",
                "answer": "When a dataset delivery was delayed by three weeks, I immediately conducted a risk analysis, presented it to the product team, and scoped down our secondary objectives to hit our launch date.",
                "extraction": {
                    "score": 5,
                    "evaluation": "Clear, professional communication and risk-managed delivery strategy.",
                    "reasoning_summary": "Demonstrated pragmatism, proactive risk identification, and excellent alignment with product goals.",
                    "extracted_data": {
                        "claims": ["Conducted risk analysis and renegotiated project scope"],
                        "technologies": [],
                        "decisions": ["Scoped down secondary objectives due to dataset delays"],
                        "tradeoffs": [],
                        "failures": ["Dataset delivery delayed by three weeks"],
                        "debugging_experiences": [],
                        "achievements": ["Successfully hit launch target date despite database delay"],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Behavioral & Communication": 90
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "wrap_up",
                "next_question_topic": "Wrap-up",
                "next_question": "Thank you for sharing your experience. This concludes our mock interview. You did an exceptional job."
            }
        ]
    },
    "theory_memorizer": {
        "name": "Bob (Theoretical Memorizer - lacks practical experience)",
        "resume": "Bob has a Master's degree in CS. Familiar with neural networks, scaling, and system design.",
        "turns": [
            {
                "objective": "Project Ownership",
                "question": "Could you start by giving me an overview of the Retinal Age Prediction pipeline and your specific contributions to it?",
                "answer": "I was a developer on a Retinal Age Prediction project. The team worked together on it. I helped write the code, and we all shared responsibilities for running the experiments.",
                "extraction": {
                    "score": 3,
                    "evaluation": "Vague explanation of individual contribution and responsibility.",
                    "reasoning_summary": "Candidate struggles to define their specific tasks or design choices, indicating low hands-on project ownership.",
                    "extracted_data": {
                        "claims": ["Worked as a developer on Retinal Age Prediction"],
                        "technologies": [],
                        "decisions": [],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Project Ownership": 30
                    },
                    "proposed_hypotheses": [
                        {
                            "hypothesis": "Candidate may have memorized concepts without practical implementation experience.",
                            "status": "unconfirmed",
                            "reason": "Very abstract claims about project roles and lack of specific code contributions."
                        }
                    ]
                },
                "next_question_action": "VERIFY_OWNERSHIP",
                "next_question_topic": "Project Tasks",
                "next_question": "Let's dig in. Can you name one specific component or function you wrote for that pipeline, and how it worked?"
            },
            {
                "objective": "Project Ownership",
                "question": "Let's dig in. Can you name one specific component or function you wrote for that pipeline, and how it worked?",
                "answer": "We all worked on the codebase together in a shared Git repository. I helped write parts of the python script that loaded images and passed them to the neural net, but it was mostly a collective effort.",
                "extraction": {
                    "score": 2,
                    "evaluation": "Fails to present clear individual contribution to design or coding.",
                    "reasoning_summary": "Continues to shift responsibility to the team, showing very weak ownership of the engineering work.",
                    "extracted_data": {
                        "claims": ["Helped write image loading parts of the python script"],
                        "technologies": ["Git", "Python"],
                        "decisions": [],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Project Ownership": 35
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "PROBE_DEEPER",
                "next_question_topic": "CNN Backbones",
                "next_question": "Understood. Let's move to the neural net model itself. Can you explain the skip connections in ResNet and how they work mathematically?"
            },
            {
                "objective": "System Understanding",
                "question": "Can you explain the skip connections in ResNet and how they work mathematically?",
                "answer": "A neural network is composed of input, hidden, and output layers. It uses weights, biases, and activation functions like ReLU. ResNet uses residual connections to prevent vanishing gradients by bypassing layers.",
                "extraction": {
                    "score": 4,
                    "evaluation": "Strong academic definitions, but missing mathematical formulation.",
                    "reasoning_summary": "Correctly defines feedforward layers, activations, and residual paths, but doesn't explain the mathematical equation H(x) = F(x) + x.",
                    "extracted_data": {
                        "claims": ["Understands feedforward networks and residual connections"],
                        "technologies": ["ResNet"],
                        "decisions": [],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "System Understanding": 65
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "PIVOT_TO_FUNDAMENTAL",
                "next_question_topic": "Framework tradeoffs",
                "next_question": "Let's pivot to first-principles. If we remove the residual addition and just multiply inputs, how does that affect gradient backpropagation mathematically?"
            },
            {
                "objective": "System Understanding",
                "question": "Let's pivot to first-principles. If we remove the residual addition and just multiply inputs, how does that affect gradient backpropagation mathematically?",
                "answer": "If you multiply the inputs instead of adding them, it behaves like a standard deep network. In standard deep networks, the derivative of multiplication chain rules can cause gradients to vanish or explode. Skip connections bypass this because addition has a derivative of 1, allowing the gradient to flow directly back.",
                "extraction": {
                    "score": 5,
                    "evaluation": "Good mathematical understanding of backpropagation and skip connection derivatives.",
                    "reasoning_summary": "Candidate correctly identifies that addition preserves the gradient by injecting 1 into the chain rule derivative, unlike multiplication which propagates vanishing gradients.",
                    "extracted_data": {
                        "claims": ["Understands backpropagation math and vanishing gradients"],
                        "technologies": ["ResNet"],
                        "decisions": [],
                        "tradeoffs": ["Addition vs multiplication derivative dynamics"],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "System Understanding": 80
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "PROBE_DEEPER",
                "next_question_topic": "Databases",
                "next_question": "Excellent explanation. Let's look at your database choices. What is the difference between vector similarity search and scalar search in databases?"
            },
            {
                "objective": "Problem Solving & Debugging",
                "question": "Excellent explanation. Let's look at your database choices. What is the difference between vector similarity search and scalar search in databases?",
                "answer": "Vector similarity search uses distance metrics like cosine similarity or Euclidean distance to find nearest neighbors, usually using index types like HNSW. Scalar search uses B-trees or hash maps to find exact matches on values like integers or strings.",
                "extraction": {
                    "score": 4,
                    "evaluation": "Solid theoretical explanation of nearest neighbors and index types.",
                    "reasoning_summary": "Explains cosine similarity/Euclidean distance, exact value matching, and correctly mentions HNSW vs B-trees, though lacks production scale experience.",
                    "extracted_data": {
                        "claims": ["Understands nearest neighbor search and traditional scalar indexing"],
                        "technologies": ["HNSW", "B-trees", "Redis"],
                        "decisions": [],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Problem Solving & Debugging": 80
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "STRESS_TEST",
                "next_question_topic": "API Rate Limiting",
                "next_question": "Okay. How would you design a rate limiter for a production ML model API to prevent abuse?"
            },
            {
                "objective": "Scaling & Production Thinking",
                "question": "Okay. How would you design a rate limiter for a production ML model API to prevent abuse?",
                "answer": "A rate limiter restricts incoming requests. We can use a token bucket algorithm or leaky bucket algorithm implemented in Redis to track client IP addresses or API keys and drop requests exceeding the limit.",
                "extraction": {
                    "score": 4,
                    "evaluation": "Clear explanation of rate limiting algorithms and caching architecture.",
                    "reasoning_summary": "Correctly outlines token bucket/leaky bucket and Redis-based tracking, demonstrating good theoretical scaling understanding.",
                    "extracted_data": {
                        "claims": ["Knows rate limiting algorithms"],
                        "technologies": ["Redis"],
                        "decisions": ["Used Redis for rate limiting cache tracking"],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Scaling & Production Thinking": 75,
                        "Decision & Tradeoff Thinking": 75,
                        "Behavioral & Communication": 80
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "wrap_up",
                "next_question_topic": "Wrap-up",
                "next_question": "Thank you for sharing your experience. This concludes our mock interview."
            }
        ]
    },
    "practical_coder": {
        "name": "Charlie (Practical Coder - struggles with theory/scaling)",
        "resume": "Charlie has built several personal projects and bootcamps. Stated project: Retinal Age Prediction pipeline.",
        "turns": [
            {
                "objective": "Project Ownership",
                "question": "Could you start by giving me an overview of the Retinal Age Prediction pipeline and your specific contributions to it?",
                "answer": "I built the whole Retinal Age Prediction project myself. I wrote all the files, created the training loop, and ran it on my local laptop GPU.",
                "extraction": {
                    "score": 4,
                    "evaluation": "Strong individual builder experience, though limited team/collaboration scope.",
                    "reasoning_summary": "Candidate wrote code independently, showing high ownership of the code, but lacks experience in larger, coordinated team environments.",
                    "extracted_data": {
                        "claims": ["Built the Retinal Age Prediction pipeline independently"],
                        "technologies": ["Python", "PyTorch"],
                        "decisions": ["Ran training on local laptop GPU"],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": ["Successfully built and trained prediction pipeline"],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Project Ownership": 80
                    },
                    "proposed_hypotheses": [
                        {
                            "hypothesis": "Candidate is highly practical but may struggle with deep architecture theory or large-scale design.",
                            "status": "unconfirmed",
                            "reason": "Independently built projects on laptop, but lacks corporate project contexts."
                        }
                    ]
                },
                "next_question_action": "PROBE_DEEPER",
                "next_question_topic": "Model Tuning",
                "next_question": "Great. Let's discuss your modeling choices. How did you handle model architecture and tuning?"
            },
            {
                "objective": "System Understanding",
                "question": "Great. Let's discuss your modeling choices. How did you handle model architecture and tuning?",
                "answer": "I just imported ResNet from torchvision and ran it. I don't know the exact math of the skip connections, but it got 90% accuracy on our test set.",
                "extraction": {
                    "score": 3,
                    "evaluation": "Relies on pre-built modules; struggles with model internal mathematics.",
                    "reasoning_summary": "Candidate imports ResNet and runs training successfully, but admits lack of knowledge about the mathematical mechanisms of ResNet internals.",
                    "extracted_data": {
                        "claims": ["Achieved 90% accuracy on test set"],
                        "technologies": ["ResNet", "torchvision"],
                        "decisions": ["Used pre-built torchvision ResNet"],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "System Understanding": 45
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "PIVOT_TO_FUNDAMENTAL",
                "next_question_topic": "ResNet Mathematics",
                "next_question": "Let's dig into that. What does the skip connection in ResNet actually do to help training converge?"
            },
            {
                "objective": "System Understanding",
                "question": "Let's dig into that. What does the skip connection in ResNet actually do to help training converge?",
                "answer": "I'm not sure about the math, but I know it helps the gradients flow directly through the layers so the model can be deeper without gradients disappearing.",
                "extraction": {
                    "score": 4,
                    "evaluation": "High-level understanding of skip connections and vanishing gradients.",
                    "reasoning_summary": "Correctly identifies that skip connections help gradient flow and address vanishing gradients in deep models, even if math details are omitted.",
                    "extracted_data": {
                        "claims": ["Understand that skip connections prevent vanishing gradients"],
                        "technologies": [],
                        "decisions": [],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "System Understanding": 75
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "PROBE_DEEPER",
                "next_question_topic": "Debugging experiences",
                "next_question": "Good intuition. Can you describe a challenging bug you encountered in the pipeline and how you resolved it?"
            },
            {
                "objective": "Problem Solving & Debugging",
                "question": "Good intuition. Can you describe a challenging bug you encountered in the pipeline and how you resolved it?",
                "answer": "The code crashed with a shape mismatch error in the linear layer. I fixed it by printing the tensor shape and changing the linear layer input features to match the output of the conv layer.",
                "extraction": {
                    "score": 4,
                    "evaluation": "Simple, practical debugging approach using print statements.",
                    "reasoning_summary": "Resolved shape mismatch by inspecting tensor shapes and correcting linear layer inputs. Practical but basic debugging methodology.",
                    "extracted_data": {
                        "claims": [],
                        "technologies": [],
                        "decisions": [],
                        "tradeoffs": [],
                        "failures": ["Shape mismatch error in the linear layer"],
                        "debugging_experiences": ["Printed tensor shapes to find mismatched dimensions in conv-to-linear transitions"],
                        "achievements": ["Resolved tensor size mismatch"],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Problem Solving & Debugging": 80
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "CHALLENGE_CLAIM",
                "next_question_topic": "Framework Choices",
                "next_question": "Okay. How did you choose your framework for the prediction pipeline?"
            },
            {
                "objective": "Decision & Tradeoff Thinking",
                "question": "Okay. How did you choose your framework for the prediction pipeline?",
                "answer": "I used PyTorch because I learned it in a tutorial. I didn't think about TensorFlow or other options. It worked fine for me.",
                "extraction": {
                    "score": 2,
                    "evaluation": "Selection based on familiarity rather than technical analysis.",
                    "reasoning_summary": "Chose framework solely based on learning tutorials and personal familiarity, without evaluating architectural or production tradeoffs.",
                    "extracted_data": {
                        "claims": [],
                        "technologies": ["PyTorch"],
                        "decisions": ["Used PyTorch based on tutorial familiarity"],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Decision & Tradeoff Thinking": 40
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "STRESS_TEST",
                "next_question_topic": "Application Scaling",
                "next_question": "Fair enough. If you had to scale this prediction app to handle thousands of requests, how would you go about it?"
            },
            {
                "objective": "Scaling & Production Thinking",
                "question": "Fair enough. If you had to scale this prediction app to handle thousands of requests, how would you go about it?",
                "answer": "I haven't run this on large servers or handled high traffic. It was just running on my local machine. I guess we would deploy it to AWS if we wanted to scale it.",
                "extraction": {
                    "score": 2,
                    "evaluation": "Very limited production deployment or scaling knowledge.",
                    "reasoning_summary": "Struggles to propose concrete scaling plans (load balancing, caching, databases) and relies on generic service mentions like AWS.",
                    "extracted_data": {
                        "claims": [],
                        "technologies": ["AWS"],
                        "decisions": [],
                        "tradeoffs": [],
                        "failures": [],
                        "debugging_experiences": [],
                        "achievements": [],
                        "notable_project_details": []
                    },
                    "confidence_score_updates": {
                        "Scaling & Production Thinking": 40,
                        "Behavioral & Communication": 75
                    },
                    "proposed_hypotheses": []
                },
                "next_question_action": "wrap_up",
                "next_question_topic": "Wrap-up",
                "next_question": "Thank you for sharing your experience. This concludes our mock interview."
            }
        ]
    }
}

def run_mock_simulation(profile_key):
    profile = CANDIDATE_PROFILES.get(profile_key)
    if not profile:
        print(f"Unknown profile: {profile_key}")
        return
        
    print(f"\n======================================================================")
    print(f" [MOCK SIMULATION] RUNNING INTERVIEW FOR: {profile['name']}")
    print(f" Resume: {profile['resume']}")
    print(f"======================================================================\n")
    
    # Initialize states
    evidence_store = {
        "claims": [],
        "technologies": [],
        "decisions": [],
        "tradeoffs": [],
        "failures": [],
        "debugging_experiences": [],
        "achievements": [],
        "notable_project_details": [],
        "hypotheses": []
    }
    
    blueprint = {
        "active_objective": "Project Ownership",
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
            },
            "Problem Solving & Debugging": {
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
            "Scaling & Production Thinking": {
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
    }
    
    interview_phase = "INTRODUCTION"
    project_investigation = {
        "in_mode": False,
        "project_name": None,
        "verified_categories": [],
        "turns_spent": 0
    }
    
    MAX_ATTEMPTS = 3
    ordered_objectives = [
        "Project Ownership",
        "System Understanding",
        "Decision & Tradeoff Thinking",
        "Problem Solving & Debugging",
        "Scaling & Production Thinking",
        "Behavioral & Communication"
    ]
    
    # Loop over the turns
    for idx, turn_data in enumerate(profile["turns"]):
        turn_num = idx + 1
        print(f"\n--- TURN {turn_num} ---")
        
        # 1. State Manager before turn
        active_objective = blueprint["active_objective"]
        # Find active objective details
        obj_details = None
        for category in ["must_verify", "nice_to_verify"]:
            if active_objective in blueprint[category]:
                obj_details = blueprint[category][active_objective]
                break
        if not obj_details:
            obj_details = {
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
            
        obj_details["attempts"] += 1
        current_attempts = obj_details["attempts"]
        
        # Phase transitions in simulation
        if interview_phase == "INTRODUCTION" and turn_num >= 1:
            interview_phase = "PROJECT_DISCOVERY"
            
        if interview_phase == "PROJECT_DISCOVERY":
            if not project_investigation["in_mode"]:
                project_investigation["in_mode"] = True
                project_investigation["project_name"] = "Retinal Age Prediction"
                project_investigation["verified_categories"] = []
                project_investigation["turns_spent"] = 0
            
            project_investigation["turns_spent"] += 1
            
            # Simulate category verification
            if active_objective == "Project Ownership":
                project_investigation["verified_categories"].append("architecture")
            elif active_objective == "System Understanding":
                project_investigation["verified_categories"].append("implementation")
                
            if len(project_investigation["verified_categories"]) >= 4 or project_investigation["turns_spent"] >= 5:
                project_investigation["in_mode"] = False
                
            if turn_num >= 2 or len(evidence_store["claims"]) > 0:
                interview_phase = "TECHNICAL_EVALUATION"
        
        print(f"[Strategy Manager Selected Objective]: {active_objective} (Probes spent: {current_attempts})")
        print(f"[Interviewer Question]: \"{turn_data['question']}\"")
        print(f"[Candidate Answer]: \"{turn_data['answer']}\"")
        
        # 2. Extract and merge signals (Simulated LLM call 1)
        extraction = turn_data["extraction"]
        score_val = extraction["score"]
        eval_msg = extraction["evaluation"]
        reasoning = extraction["reasoning_summary"]
        extracted_data = extraction["extracted_data"]
        confidence_updates = extraction["confidence_score_updates"]
        proposed_hypotheses = extraction.get("proposed_hypotheses", [])
        
        # Merge evidence store
        for key in ["claims", "technologies", "decisions", "tradeoffs", "failures", "debugging_experiences", "achievements", "notable_project_details"]:
            existing_items = evidence_store.setdefault(key, [])
            new_items = extracted_data.get(key, [])
            for item in new_items:
                if item and item not in existing_items:
                    existing_items.append(item)
                    
        existing_hypotheses = evidence_store.setdefault("hypotheses", [])
        for prop in proposed_hypotheses:
            hyp_text = prop.get("hypothesis", "")
            if not hyp_text:
                continue
            found = False
            for ext in existing_hypotheses:
                if ext.get("hypothesis", "").lower() == hyp_text.lower():
                    ext["status"] = prop.get("status", "unconfirmed")
                    ext["reason"] = prop.get("reason", "")
                    found = True
                    break
            if not found:
                existing_hypotheses.append({
                    "hypothesis": hyp_text,
                    "status": prop.get("status", "unconfirmed"),
                    "reason": prop.get("reason", "")
                })
                
        # Update blueprint confidence scores
        for obj, val in confidence_updates.items():
            for category in ["must_verify", "nice_to_verify"]:
                if obj in blueprint[category]:
                    obj_ref = blueprint[category][obj]
                    score = max(0, min(100, int(val)))
                    cats_count = score // 20
                    available_cats = ["architecture", "debugging", "tradeoffs", "implementation", "scaling"]
                    for c_idx, cat in enumerate(available_cats):
                        if c_idx < cats_count:
                            obj_ref["evidence_categories"][cat] = True
                            
        # Recalculate status for ALL objectives in the blueprint
        for category in ["must_verify", "nice_to_verify"]:
            for obj_name, obj_ref in blueprint[category].items():
                true_cats = [c for c, val in obj_ref["evidence_categories"].items() if val]
                obj_ref["confidence"] = len(true_cats) * 20
                attempts_count = obj_ref.get("attempts", 0)
                if obj_ref["confidence"] >= 80 and attempts_count >= 2:
                    obj_ref["status"] = "verified"
                else:
                    obj_ref["status"] = "unverified"
                        
        # 3. Strategy Manager Advancement check
        if obj_details["status"] == "verified" or obj_details["attempts"] >= MAX_ATTEMPTS:
            # Shift active objective
            advanced = False
            for obj_name, state_info in blueprint["must_verify"].items():
                if state_info["status"] != "verified":
                    blueprint["active_objective"] = obj_name
                    advanced = True
                    break
            if not advanced:
                for obj_name, state_info in blueprint["nice_to_verify"].items():
                    if state_info["status"] != "verified":
                        blueprint["active_objective"] = obj_name
                        advanced = True
                        break
            if not advanced:
                print(">>> ALL OBJECTIVES SUCCESSFULLY VERIFIED! <<<")
                
        # Final phase check for wrap up
        all_objectives_verified = True
        for category in ["must_verify", "nice_to_verify"]:
            for obj_name, state_info in blueprint[category].items():
                if state_info["status"] != "verified":
                    all_objectives_verified = False
                    break
        if all_objectives_verified or turn_num >= len(profile["turns"]):
            interview_phase = "WRAP_UP"
            
        print("\n[Strategy Analysis]")
        print(f"LLM Critique Score: {score_val}/5 | Evaluation: {eval_msg}")
        print(f"Interview Phase: {interview_phase}")
        print(f"Project Investigation State: {json.dumps(project_investigation)}")
        
        # Build and print debug dashboard
        debug_dashboard = {
            "objective": active_objective,
            "confidence": obj_details.get("confidence", 0),
            "claims": evidence_store["claims"],
            "strategy": turn_data['next_question_action'],
            "reason_for_next_question": f"Simulation step for {active_objective}"
        }
        print(f"Debug Dashboard Payload:\n{json.dumps(debug_dashboard, indent=2)}")
        
        # Print blueprint progress
        progress_list = []
        for category in ["must_verify", "nice_to_verify"]:
            for obj_name, state_info in blueprint[category].items():
                progress_list.append(f"{obj_name} ({category}): {state_info['confidence']}% ({state_info['status']}, Probes: {state_info['attempts']})")
        print(f"Objectives Grid:\n  - " + "\n  - ".join(progress_list))
        
        # Print hypotheses
        if evidence_store["hypotheses"]:
            print("Candidate Hypotheses:")
            for h in evidence_store["hypotheses"]:
                print(f"  * {h['hypothesis']} ({h['status']}) [Reason: {h['reason']}]")
                
        print(f"\n[Reaction Router Selected Action]: {turn_data['next_question_action']}")
        print(f"[Next Question Drafted]: \"{turn_data['next_question']}\"")
        print("-" * 70)
        
    print(f"\n[SUCCESS] Mock Simulation of {profile['name']} complete!\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            for profile in CANDIDATE_PROFILES.keys():
                run_mock_simulation(profile)
        elif sys.argv[1] in CANDIDATE_PROFILES:
            run_mock_simulation(sys.argv[1])
        else:
            print("Please choose a candidate profile or run 'all':")
            for k in CANDIDATE_PROFILES.keys():
                print(f"  python backend/simulate_mock_interviews.py {k}")
            print("  python backend/simulate_mock_interviews.py all")
    else:
        # Run all profiles by default
        for profile in CANDIDATE_PROFILES.keys():
            run_mock_simulation(profile)
