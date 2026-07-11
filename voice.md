# AI Interviewer - Voice Layer Implementation Plan (Version 1)

## Project Status

The Interview Agent and Evaluation Agent are considered feature-complete for Version 1.

Current architecture already supports:

* Adaptive interviewing
* Project investigation
* Claim verification
* Ownership assessment
* Objective tracking
* Interview evaluation
* Learning roadmap generation
* Hiring recommendation generation

No further architectural redesign should be performed on either agent unless a bug is discovered.

The next milestone is Voice Integration.

---

# Goal

Convert the existing text-based AI Interviewer into a real-time voice interviewer.

The voice layer should function as an interface layer only.

The Interview Agent and Evaluation Agent remain the decision-making brain.

Voice should simply provide:

Speech → Text → Interview Agent → Text → Speech

---

# Final Technology Decisions

## Voice Platform

Use:

Vapi

Reason:

* Fastest implementation path
* Built-in audio streaming
* Built-in speech-to-text
* Built-in text-to-speech
* Built-in interruption handling
* Easy web integration
* Easier than implementing Gemini Live directly

---

## Interview Logic

Continue using:

* LangGraph
* Existing Interview Agent
* Existing Evaluation Agent

Vapi should never generate interview questions.

The backend remains the source of truth.

---

## LLMs

### Interview Agent

Continue using the currently tested Gemini model.

Do not replace it during Voice MVP development.

---

### Evaluation Agent

Continue using the currently tested evaluation configuration.

No redesign required.

---

## Backend

FastAPI

Existing APIs should remain unchanged whenever possible.

---

## Frontend

Next.js

React

TypeScript

---

# High-Level Architecture

Candidate Voice

↓

Vapi

↓

Speech-to-Text

↓

FastAPI

↓

Interview Agent

↓

Question Text

↓

Vapi

↓

Text-to-Speech

↓

Candidate Hears Question

---

# Phase 1 - Voice MVP

## Goal

Conduct a complete interview using voice.

No UI polish required.

Only prove the full voice loop works.

---

## Required Flow

User clicks:

Start Interview

↓

Microphone enabled

↓

Candidate speaks

↓

Vapi converts speech to text

↓

Transcript sent to backend

↓

Interview Agent generates response

↓

Response returned to Vapi

↓

Vapi speaks response

↓

Loop continues

---

## Success Criteria

Candidate can complete an entire interview without typing.

---

# Phase 2 - Session Management

## Goal

Maintain interview state across voice turns.

---

## Requirements

Every voice turn should map to an existing interview session.

Store:

```python
{
    "session_id": "...",
    "speaker": "candidate",
    "text": "...",
    "timestamp": "..."
}
```

Interview Agent state must remain unchanged.

---

# Phase 3 - Transcript Synchronization

## Goal

Generate a complete transcript during the interview.

---

## Requirements

Store:

```python
{
    "speaker": "candidate",
    "text": "...",
    "timestamp": "..."
}
```

and

```python
{
    "speaker": "interviewer",
    "text": "...",
    "timestamp": "..."
}
```

for every turn.

---

## Benefits

Allows:

* Evaluation Agent execution
* Debugging
* Interview replay
* Analytics

---

# Phase 4 - Live Dashboard

## Goal

Display interview progress while voice interaction is occurring.

---

## Show

Current Question

Current Transcript

Interview Duration

Current Objective

Current Project

Interview Progress

---

## Do NOT Show

Ownership Score

Weak Skills

Claim Verification

Evaluation Metrics

These should remain hidden until interview completion.

---

# Phase 5 - Interview Completion

## Goal

Trigger evaluation automatically.

---

## Flow

Interview Ends

↓

Evaluation Agent Runs

↓

Evaluation Report Generated

↓

Frontend Displays Results

---

# Results Page

Display:

Overall Assessment

Technical Score

Communication Score

Ownership Score

Claim Verification Summary

Strengths

Weaknesses

Learning Plan

Recommendations

Hire Recommendation

Confidence Level

---

# API Endpoints

## Start Session

POST

```text
/api/interview/start
```

Returns:

```json
{
  "session_id": "..."
}
```

---

## Voice Turn

POST

```text
/api/interview/turn
```

Input:

```json
{
  "session_id": "...",
  "candidate_text": "..."
}
```

Output:

```json
{
  "interviewer_response": "..."
}
```

---

## End Interview

POST

```text
/api/interview/end
```

Triggers evaluation.

---

## Get Evaluation

GET

```text
/api/evaluation/{session_id}
```

Returns final report.

---

# Out Of Scope (Version 1)

Do NOT implement:

* Emotion Detection
* Eye Tracking
* Webcam Analysis
* Facial Expression Analysis
* Lip Tracking
* AI Avatars
* Video Interviews
* Voice Quality Scoring
* Stress Detection
* Personality Analysis

These features add complexity and do not materially improve the project for internship demonstrations.

---

# Development Order

Sprint 1

* Vapi integration
* Speech-to-text
* Text-to-speech
* Voice interview loop

Sprint 2

* Session management
* Transcript synchronization

Sprint 3

* Live dashboard
* Evaluation integration

Sprint 4

* Frontend polish
* Bug fixing
* Demo preparation

---

# Definition Of Done

The Voice Layer is considered complete when:

✓ Candidate can conduct a full interview using voice

✓ Interview Agent works without modification

✓ Evaluation Agent works without modification

✓ Final report is generated automatically

✓ Frontend displays results correctly

At that point development should shift from feature building to testing, deployment, and demo preparation.
