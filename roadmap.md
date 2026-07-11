# Veriq AI - Development Roadmap

# Phase 0 - System Design & Planning

Duration:
2-3 Days

Goal:
Create a clear blueprint before coding.

---

Tasks

Define:

* Interview Modes
* Agent Responsibilities
* Database Schema
* User Flow
* API Structure

Create:

* Architecture Diagram
* Database Diagram
* LangGraph Flow Diagram

Deliverables

* architecture.md
* roadmap.md
* database_schema.md

Success Criteria

Everyone on the team understands:

* What is being built
* Why it is being built
* Who is responsible for what

---

# Phase 1 - Core Interview Engine (MVP)

Duration:
1 Week

Goal:
Conduct a complete text interview.

NO Voice.
NO RAG.
NO Memory.

Just interviewing.

---

User Flow

User:

Select:

* Role
* Difficulty
* Duration

Start Interview.

---

Backend Responsibilities

Create Interview Session.

Generate questions.

Maintain conversation context.

Store transcript.

End interview.

---

Build

Interview Agent V1

Responsibilities:

* Generate questions
* Generate follow-up questions
* Maintain interview flow

Input:

Role:
AI Engineer

Difficulty:
Medium

Output:

Interview Questions

---

Create Interview State

Stores:

* Current Question
* Question Count
* Covered Topics
* Difficulty
* Transcript

---

Build Topic Coverage Logic

Example:

AI Engineer Interview

Must Cover:

* ML
* DL
* RAG
* Projects
* Behavioral

Ensure no topic dominates.

---

Database

Tables:

users

interviews

transcripts

---

Frontend

Create:

Dashboard

Interview Room

Interview History Page

---

Deliverable

Working text-based interviewer.

---

# Phase 2 - Adaptive Interview Intelligence

Duration:
1 Week

Goal:
Make interviews feel human.

---

Build Follow-Up Logic

Example:

Candidate:

"I used FAISS."

Interview Agent:

"Why FAISS instead of Qdrant?"

---

Build Context Awareness

Interview should remember:

Previous Answers.

Example:

Question 8 can reference Question 2.

---

Build Difficulty Controller

Weak Answers:

Simpler Questions.

Strong Answers:

Harder Questions.

---

Build Topic Tracker

Tracks:

Covered Topics.

Missing Topics.

Interview Balance.

---

Deliverable

Human-like adaptive interview.

---

# Phase 3 - Evaluation Engine

Duration:
1 Week

Goal:
Evaluate complete interview.

---

Create Evaluation Agent

Input:

Entire Transcript.

Output:

Interview Report.

---

Evaluation Categories

Technical Knowledge

Communication

Confidence

Project Explanation

Behavioral Skills

---

Create Scoring Rubric

Example:

Technical:

0-100

Communication:

0-100

Overall:

0-100

---

Generate Feedback

Strengths

Weaknesses

Improvement Areas

---

Frontend

Interview Report Page

Charts

Performance Summary

---

Deliverable

Complete interview evaluation.

---

# Phase 4 - Memory System

Duration:
1 Week

Goal:
Remember users.

---

Create Memory Agent

Stores:

Interview History

Weak Topics

Strong Topics

Improvement Trends

---

Create User Learning Profile

Example:

Weak:

Transformers

Strong:

RAG

---

Create Trend Analysis

Interview 1:

65

Interview 2:

72

Interview 3:

81

---

Build Readiness Score

Examples:

AI/ML Internship:
82%

Google SWE:
68%

---

Frontend

Progress Dashboard

Trend Graphs

Readiness Cards

---

Deliverable

Persistent personalized coaching.

---

# Phase 5 - Learning & Planning System

Duration:
1 Week

Goal:
Convert weaknesses into learning plans.

---

Build Global Knowledge Base

Create curated content for:

DSA

Machine Learning

Deep Learning

RAG

Agents

System Design

Behavioral Interviews

---

Create Embeddings

Store in Qdrant.

---

Build Planning Agent

Input:

Weak Topics

Output:

Learning Plan

---

Generate:

Study Plan

Resources

Practice Questions

Revision Roadmap

---

Create Re-Interview Generator

Example:

Weak Topic:

Transformers

Generate:

15 Minute Transformer Interview

---

Deliverable

AI Learning Coach.

---

# Phase 6 - Resume & JD Personalization

Duration:
4-5 Days

Goal:
Personalized interviews.

---

Resume Upload

Extract:

Projects

Skills

Experience

---

JD Upload

Extract:

Requirements

Preferred Skills

---

Build Gap Analysis

Compare:

Resume

vs

JD

---

Generate:

Missing Skills

Interview Focus Areas

---

Interview Agent Uses:

Resume

JD

Gap Analysis

---

Deliverable

Highly personalized interviews.

---

# Phase 7 - Voice AI Integration

Duration:
1 Week

Goal:
Transform platform into voice interviewer.

---

Integrate Vapi

or

Gemini Live

---

Voice Flow

User Speaks

↓

Speech To Text

↓

Interview Agent

↓

Response

↓

Text To Speech

↓

User Hears Response

---

Build Voice Interview Room

Features:

Start Call

End Call

Mute

Transcript

---

Deliverable

Real-time AI interviewer.

---

# Phase 8 - Production Features

Duration:
1 Week

Goal:
Make project portfolio-ready.

---

Authentication

User Accounts

---

Analytics Dashboard

---

Interview Search

---

Export Reports

PDF Reports

---

Company Specific Interviews

Google

Amazon

Meta

OpenAI

Startups

---

Custom Interviews

Choose Topics

Choose Difficulty

Choose Duration

---

Deliverable

Portfolio-worthy product.

---

# Agent Development Order

Do NOT build all agents together.

Build:

1. Interview Agent

2. Evaluation Agent

3. Memory Agent

4. Planning Agent

Exactly in this order.

Each later agent depends on previous agents.

---

# Final Architecture

Frontend

Next.js

↓

Backend

FastAPI

↓

LangGraph

↓

Interview Agent

↓

Evaluation Agent

↓

Memory Agent

↓

Planning Agent

↓

Gemini

↓

Qdrant

↓

PostgreSQL

↓

Vapi / Gemini Live

---

# Final Success Criteria

By the end the platform should:

Conduct adaptive interviews.

Evaluate complete interviews.

Track progress over time.

Generate readiness scores.

Create personalized study plans.

Generate targeted re-interviews.

Support voice interaction.

Support company-specific interviews.

Support resume and JD personalization.

Function as a complete AI Interview Preparation Platform.
