# Veriq

**Veriq is an AI interview preparation platform designed to simulate a real interview room, evaluate performance with depth, and convert every session into a clear improvement loop.**

It combines adaptive questioning, voice-first interaction, transcript intelligence, progress tracking, and personalized learning recommendations into a single product experience.

---

## Overview

Veriq is built for candidates who want more than a generic mock interview. Instead of asking fixed questions and stopping at a score, the platform adapts to the user’s role, resume, job description, and difficulty level, then turns the session into a structured path for improvement.

The product is organized around five stages:

1. Prepare the session
2. Enter the live interview room
3. Capture transcript and performance data
4. Generate evaluation and readiness insights
5. Translate weak areas into learning and next-step practice

---

## Why Veriq

Traditional interview practice tools usually follow a shallow pattern:

`Interview -> Score -> End`

Veriq follows a more complete loop:

`Interview -> Evaluation -> Progress Tracking -> Learning Plan -> Re-Interview -> Improvement`

This makes the product useful not only for practice, but also for long-term interview readiness.

---

## Product Experience

### Landing Page

The public landing page introduces Veriq with a premium visual system, strong typography, and a scroll-based product story. It is intentionally designed to feel editorial and product-led rather than like a typical SaaS homepage.

### Interview Setup

Users can configure a session by choosing:

- Role-based practice
- Resume-based practice
- JD matching
- Combined resume and JD mode

They can also set:

- Role
- Difficulty
- Duration
- Company style
- Resume or job description inputs

### Live Interview Room

The live interview room is the core of the product. It supports:

- Dynamic question generation
- Follow-up questions
- Voice-based interaction
- Transcript capture
- Human-like pacing and turn-taking

### Results and Progress

After the session, Veriq stores and surfaces:

- Transcript history
- Evaluation scores
- Strengths and weaknesses
- Readiness indicators
- Recommended next steps

### Learning and Profile

The post-interview experience extends into:

- Learning resources
- User profile insights
- History and transcript review
- Billing and plan management

---

## Core Capabilities

### 1. Adaptive Interview Engine

Veriq does not rely on a static question set. It adjusts the interview based on the user’s selected role, difficulty level, and input context. The interviewer can deepen into a topic, shift to another topic, or adapt follow-ups based on the candidate’s answer quality.

### 2. Voice-First Practice

The interview experience is designed for real spoken responses. The user speaks naturally, the session listens, and the conversation progresses as if it were an actual interview.

### 3. Transcript Intelligence

Every session is captured as a transcript, allowing the platform to analyze what the user said, how they explained it, and where they need improvement.

### 4. Structured Evaluation

At the end of the interview, Veriq evaluates the session across multiple categories such as:

- Technical knowledge
- Communication
- Confidence
- Project explanation
- Problem solving
- Behavioral performance

### 5. Personal Readiness Tracking

Veriq turns the evaluation into a readiness view so users can understand how prepared they are for specific interview targets and how that readiness changes over time.

### 6. Learning Loop

The platform does not stop at feedback. It uses the user’s weaknesses and session data to drive the next round of practice and learning.

---

## Who This Is For

Veriq is intended for:

- Students preparing for internships
- Candidates preparing for product or engineering interviews
- Professionals practicing role transitions
- Users who want structured, repeatable interview feedback
- Anyone who wants to improve through deliberate practice rather than ad hoc mock questions

---

## How It Works

1. Open the landing page.
2. Start a new interview session.
3. Select the target role, difficulty, and duration.
4. Provide a resume or JD if needed.
5. Enter the interview room.
6. Respond to live questions naturally.
7. Review transcript, score, and feedback.
8. Move into learning and improvement tracking.
9. Run another interview with better focus.

---

## Feature Map

### Public Pages

- `Home` - landing page and product story
- `Product` - product overview
- `How It Works` - workflow explanation
- `Pricing` - plan overview

### Authenticated Pages

- `New Interview` - session setup
- `Interview Room` - active session
- `Voice Interview` - voice-enabled session
- `History` - previous interviews
- `Learning` - recommendations and resources
- `Profile` - readiness and user insights
- `Billing` - subscription and plan status
- `Settings` - account preferences
- `Transcript` - detailed session transcript

---

## Technology Stack

### Frontend

- Next.js 16
- React 19
- TypeScript
- App Router architecture
- Custom CSS-based premium design system
- Supabase browser client integration
- Vapi web voice integration

### Backend

- FastAPI
- LangGraph agent orchestration
- SQLModel
- Qdrant vector search
- Supabase authentication support
- Voice and transcript services
- Payment and subscription support

### Supporting Services

- Gemini API
- Deepgram or Whisper/Groq for speech handling
- NVIDIA API hooks where configured
- Local SQLite for development by default

---

## Backend Architecture

Veriq uses a split-stack architecture:

- The frontend handles the user experience, navigation, and session entry points.
- The backend orchestrates interview logic, transcript capture, evaluation, and planning.
- The agent layer manages stateful interview behavior.
- The data layer stores sessions, profiles, transcripts, and learning progress.
- The voice layer handles live spoken interaction when enabled.

### Agent Responsibilities

- **Interview Agent**: asks the next question, adapts depth, and manages follow-ups
- **Evaluation Agent**: scores the finished interview and identifies strengths and gaps
- **Memory Agent**: updates the user’s profile and readiness history
- **Planning Agent**: produces the next learning plan and follow-up practice path

---

## Repository Structure

```text
.
├── backend/
│   └── app/
│       ├── agents/
│       ├── payments/
│       ├── routers/
│       ├── services/
│       └── models/
├── frontend/
│   └── app/
│       ├── components/
│       ├── interview/
│       ├── new-interview/
│       ├── history/
│       ├── learning/
│       ├── profile/
│       ├── billing/
│       └── utils/
├── architecture.md
├── database_schema.md
├── prd.md
├── roadmap.md
└── README.md
```

---

## Local Development

### Prerequisites

- Node.js 20 or later
- Python 3.10 or later
- npm

### Backend Setup

From the repository root:

```bash
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

### Local URLs

- Frontend: `http://localhost:3000`
- Backend health check: `http://localhost:8000/api/health`

---

## Environment Variables

### Frontend

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Backend

Create a root `.env` file:

```env
DATABASE_URL=sqlite:///./dev.db
GEMINI_API_KEY=your_gemini_key
DEEPGRAM_API_KEY=your_deepgram_key
WHISPER_API_KEY=your_whisper_or_groq_key
GROQ_API_KEY=your_groq_key_optional
NVIDIA_API_KEY=your_nvidia_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

Notes:

- `DATABASE_URL` defaults to SQLite during development.
- `WHISPER_API_KEY` can fall back to `GROQ_API_KEY` in the backend configuration.

---

## API Surface

Veriq exposes backend services for:

- Authentication
- Interview creation and session preparation
- Transcript retrieval
- Evaluation and reporting
- Learning plan generation
- Profile and readiness tracking
- Voice session support
- Payment and subscription management

The backend also exposes a health endpoint:

- `GET /api/health`

---

## Design Language

The frontend uses a premium visual language built around:

- Warm neutral surfaces
- Gold accent highlights
- Editorial typography
- Soft shadows and glass-like panels
- Subtle motion instead of heavy dashboard treatment

The result is meant to feel calm, intentional, and high-value from the first screen through the final report.

---

## Documentation

Additional project documents:

- `architecture.md`
- `database_schema.md`
- `prd.md`
- `roadmap.md`
- `Frontend_design.md`
- `voice.md`

---

## Verification

The frontend production build has been verified successfully:

```bash
cd frontend
npm run build
```

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for full details.
