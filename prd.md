# Veriq AI

## AI-Powered Adaptive Interview Preparation Platform

### Vision

Veriq AI is a voice-based interview preparation platform that helps students and professionals practice realistic interviews, identify weaknesses, track long-term progress, and improve through personalized learning plans.

Unlike traditional interview tools that only conduct mock interviews, Veriq acts as a complete interview preparation coach.

The platform supports multiple interview modes, adapts questions dynamically during conversations, evaluates complete interview sessions, tracks progress across time, and generates targeted improvement plans.

---

# Core Philosophy

Most interview tools:

Interview → Score → End

Veriq:

Interview → Evaluation → Progress Tracking → Learning Plan → Re-Interview → Improvement

The system continuously learns about the user and helps them become interview-ready.

---

# Interview Modes

## Quick Mock Interview

No resume required.

User selects:

* Role
* Difficulty
* Duration

Examples:

* AI/ML Intern
* Data Scientist
* Backend Developer
* Frontend Developer
* Full Stack Engineer

Start interview immediately.

---

## Company Specific Interview

User selects:

* Google
* Amazon
* Microsoft
* Meta
* OpenAI
* Startup

The system generates interview styles and questions tailored to that company.

---

## Resume-Based Interview

User uploads resume.

The system generates highly personalized questions based on:

* Projects
* Skills
* Experience

Example:

"Tell me about your Retinal Age Gap Prediction project."

---

## JD-Based Interview

User uploads a Job Description.

The system extracts:

* Required Skills
* Preferred Skills
* Responsibilities

Questions are generated accordingly.

---

## Custom Interview

User selects:

* Role
* Topics
* Difficulty
* Duration

Examples:

Role:
AI Engineer

Topics:

* RAG
* Fine Tuning
* Transformers

Duration:
45 Minutes

---

# Adaptive Interview Engine

The interview behaves like a human interviewer.

Instead of asking fixed questions, it:

* Generates follow-up questions
* Changes difficulty dynamically
* Tracks covered topics
* Explores depth where necessary

Example:

Candidate:
"I used FAISS."

Interviewer:
"Why FAISS instead of Qdrant?"

Candidate answers.

Interviewer:
"What scaling limitations would FAISS have?"

---

# Voice Interview System

Supports real-time conversations.

Voice Layer:

Primary:
Vapi

Alternative:
Gemini Live

Responsibilities:

* Speech-to-Text
* Text-to-Speech
* Streaming Conversation
* Turn Taking

---

# Transcript Intelligence

During the interview the system stores:

* Questions
* Answers
* Topics
* Metadata

This transcript becomes the foundation for evaluation.

---

# Full Interview Evaluation

Evaluation occurs after the interview ends.

Categories:

* Technical Knowledge
* Communication
* Confidence
* Project Explanation
* Problem Solving
* Behavioral Performance

Outputs:

* Overall Score
* Topic Scores
* Strengths
* Weaknesses

---

# Readiness Score

A unique platform feature.

Examples:

AI/ML Internship Readiness:
82%

Google SWE Readiness:
68%

Startup Engineer Readiness:
88%

Generated using:

* Interview Performance
* Historical Performance
* Role Requirements

---

# Memory System

Maintains:

* Interview History
* Weak Topics
* Strong Topics
* Learning Trends
* Progress Over Time

Future interviews become personalized.

---

# Global Knowledge Base

A pre-built vector database maintained by the platform.

Contains:

* DSA Roadmaps
* ML Concepts
* Deep Learning
* GenAI
* RAG
* System Design
* Curated Resources

Users do not need to upload study material.

---

# Personalized Study Planner

After evaluation:

Weak Areas are identified.

The Planning System generates:

* Learning Roadmap
* Practice Questions
* Resource Recommendations
* Revision Plans

---

# Targeted Re-Interviews

The system can create focused interviews.

Example:

Weak Topic:
Transformers

Generated Session:

15 Minute Transformer Interview

Used to measure improvement.

---

# Agent Architecture

## Interview Agent

Responsibilities:

* Interview orchestration
* Question generation
* Follow-up generation
* Topic coverage
* Difficulty adjustment

---

## Evaluation Agent

Responsibilities:

* Transcript analysis
* Scoring
* Weakness detection
* Strength identification

---

## Memory Agent

Responsibilities:

* Progress tracking
* Historical analysis
* Readiness scoring
* User profile management

---

## Planning Agent

Responsibilities:

* Resource retrieval
* Study plan generation
* Practice question generation
* Re-interview planning

---

# Technology Stack

Frontend:
Next.js

Backend:
FastAPI

Agent Framework:
LangGraph

LLM:
Gemini 2.5

Voice:
Vapi (Primary)
Gemini Live (Alternative)

Database:
PostgreSQL

Vector Database:
Qdrant

---

# Future Enhancements

* Coding Interview Mode
* Quant Finance Interview Mode
* AI/ML Specialized Interview Mode
* Video Interviews
* Team Interviews
* Multi-Round Interview Simulation
* HR + Technical Combined Interviews

---

# Why This Project Stands Out

This project demonstrates:

* Agentic AI
* LLM Engineering
* Voice AI
* RAG
* Vector Databases
* Memory Systems
* Backend Engineering
* Product Design
* System Architecture

Most importantly, it solves a real-world problem while providing long-term personalization, making it significantly more useful than traditional AI interview applications.

