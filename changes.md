# AI Interviewer v2 Improvement Plan

## Goal

The current interviewer architecture is already strong enough for the project.

The goal is NOT to make the interviewer perfect.

The goal is to fix the biggest realism and ownership-verification issues discovered during manual interviews and then move on to Evaluation Agent development.

Only implement the changes listed below.

---

# Problem 1: No Investigation Plan

## Current Behaviour

When a candidate mentions a project:

"I built an AI Interviewer."

The interviewer reacts turn-by-turn.

Example:

Architecture
→ Tradeoff
→ Implementation
→ Architecture again

Question flow is not guided by a structured verification plan.

---

## Desired Behaviour

When a project or claim is detected, create a verification plan.

Example:

```python
project_investigation = {
    "project_name": "AI Interviewer",
    "verification_plan": {
        "architecture": False,
        "implementation": False,
        "debugging": False,
        "tradeoffs": False,
        "failure_cases": False
    }
}
```

The interviewer should prioritize categories that are still unverified.

Example flow:

Q1 Architecture

Q2 Implementation

Q3 Tradeoffs

Q4 Debugging

Q5 Failure Cases

instead of repeatedly asking architecture questions.

---

## Implementation Notes

Add:

```python
verification_plan
```

to project investigation state.

After each answer:

```python
verification_plan[category] = True
```

if sufficient evidence is found.

Question generation should prioritize remaining categories.

---

# Problem 2: Confidence Scoring Is Too Mechanical

## Current Behaviour

Confidence increases by:

```python
number_of_categories * 20
```

This allows shallow answers to gain confidence too quickly.

Example:

Candidate briefly mentions architecture.

Architecture=True

Confidence +20

This is too generous.

---

## Desired Behaviour

Track evidence strength.

Example:

```python
evidence_categories = {
    "architecture": "weak",
    "implementation": "strong",
    "debugging": "none",
    "tradeoffs": "moderate"
}
```

Use:

```python
WEIGHTS = {
    "none": 0,
    "weak": 5,
    "moderate": 15,
    "strong": 20
}
```

Confidence:

```python
confidence = sum(category_scores)
```

This prevents superficial answers from heavily influencing verification confidence.

---

## Implementation Notes

Modify LLM output schema.

Current:

```python
architecture=True
```

New:

```python
architecture="weak"
```

Possible values:

* none
* weak
* moderate
* strong

Confidence should be calculated from evidence strength instead of binary presence.

---

# Problem 3: Claim Verification Workflow Is Incomplete

## Current Behaviour

Claims exist:

UNVERIFIED
PROBED
VERIFIED
FAILED_VERIFICATION

but there is no structured verification process.

---

## Desired Behaviour

Every extracted claim should have required evidence.

Example:

```python
claim = {
    "text": "Built Evaluation Agent",
    "status": "UNVERIFIED",
    "required_evidence": [
        "architecture",
        "implementation"
    ]
}
```

Verification occurs only after required evidence has been gathered.

Example:

Architecture verified

Implementation verified

→ Claim becomes VERIFIED

If repeated probing produces weak evidence:

→ FAILED_VERIFICATION

---

## Implementation Notes

Add:

```python
required_evidence
verified_evidence
```

to claim structure.

Do not verify claims based on a single answer.

---

# Problem 4: Hardcoded Phase Transitions

## Current Behaviour

Current logic:

```python
1 answer -> PROJECT_DISCOVERY

2 answers -> TECHNICAL_EVALUATION
```

This is artificial.

---

## Desired Behaviour

Phase transitions should depend on evidence.

Examples:

PROJECT_DISCOVERY

Only leave after:

* project identified
* architecture discussed

TECHNICAL_EVALUATION

Only leave after:

* sufficient objectives verified
* confidence thresholds reached

WRAP_UP

Only when:

* interview time exhausted
  OR
* objectives sufficiently covered

---

## Implementation Notes

Replace turn-count based transitions with evidence-based transitions.

---

# Problem 5: Objective Fixation (Biggest Manual Interview Issue)

## Current Behaviour

The interviewer can spend 6-8 questions on one project or one objective.

Example:

Project Ownership

Architecture

Implementation

Tradeoffs

Implementation

Architecture

Tradeoffs

This does not resemble real interviews.

---

## Desired Behaviour

The interviewer should rotate objectives and topics.

Real interviewers typically ask:

2-3 questions

then move to another topic.

---

## Implementation

Add:

```python
objective_turns_spent
```

Example:

```python
Project Ownership = 3 turns
```

Rule:

If:

```python
objective_turns_spent >= max_turns_per_objective
```

switch objective.

---

## Dynamic Turn Limits

Turn limit should depend on interview duration.

Example:

### 5 Minute Interview

Maximum:

```python
2 turns per objective
```

### 10 Minute Interview

Maximum:

```python
3 turns per objective
```

### 15 Minute Interview

Maximum:

```python
4-5 turns per objective
```

---

## Exception Rule

If objective confidence is extremely low:

Example:

```python
confidence < 20
```

allow one extra probing question.

Otherwise rotate.

---

# Problem 6: Failure Exit Rule

## Current Behaviour

If a candidate cannot answer a question, the interviewer may continue digging indefinitely.

This feels unrealistic.

---

## Desired Behaviour

Real interviewers typically:

Ask question

↓

Candidate fails

↓

Ask clarification/follow-up

↓

Candidate fails again

↓

Mark concept as weak

↓

Move on

---

## Implementation

Track:

```python
failed_attempts_per_concept
```

Rule:

```python
if failed_attempts >= 2:
```

Then:

```python
concept_status = "weak"
```

Add concept to:

```python
knowledge_model["weak_skills"]
```

and move to next topic.

Do not continue digging.

---

# Out of Scope

Do NOT implement:

* Contradiction Engine
* New Agents
* Voice Features
* Additional Databases
* UI Improvements
* More LangGraph Nodes
* Multi-Agent Rewrites

These can be revisited later.

Current priority is improving interview realism and ownership verification.

After completing these changes, begin manual testing again and then move to Evaluation Agent development.
