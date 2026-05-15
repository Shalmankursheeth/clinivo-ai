# Clinivo AI

## Intelligent Voice Infrastructure for Healthcare Communication

Clinivo AI is a multilingual AI-powered healthcare communication platform designed to automate patient interaction workflows, appointment inquiries, scheduling operations, and clinic communication systems using low-latency conversational AI infrastructure.

The platform combines telephony, speech recognition, conversational AI orchestration, distributed session management, and voice synthesis into a unified healthcare voice workflow system.

---
## Live Frontend Demo

https://clinivo-ai.vercel.app/

# Platform Overview

Clinivo AI is designed around asynchronous voice communication pipelines capable of:

* Handling inbound patient calls
* Processing multilingual speech input
* Understanding conversational intent
* Managing appointment workflows
* Maintaining conversational memory
* Generating natural AI voice responses
* Supporting healthcare operational workflows

The system architecture is modular, service-oriented, and designed for scalable voice workflow orchestration.

---

# AI Voice Workflow Architecture

```mermaid
flowchart TB

%% =========================
%% CLIENT LAYER
%% =========================

subgraph CLIENT["Patient Communication Layer"]

A[Patient Voice Call]
B[Clinic Operations Dashboard]

end

%% =========================
%% TELEPHONY
%% =========================

subgraph TELEPHONY["Telephony & Audio Gateway"]

C[Twilio Voice Gateway]
D[Streaming Audio Pipeline]

end

%% =========================
%% SPEECH PROCESSING
%% =========================

subgraph SPEECH["Speech Processing Layer"]

E[Deepgram Speech-to-Text]
F[Multilingual Transcript Engine]

end

%% =========================
%% AI ORCHESTRATION
%% =========================

subgraph AI["Conversational AI Orchestration"]

G[Groq LLM]
H[Intent Extraction Engine]
I[Conversation Router]
J[Workflow Decision Engine]

end

%% =========================
%% MEMORY
%% =========================

subgraph MEMORY["Session & Context Infrastructure"]

K[Redis Session Memory]
L[Conversation Context Store]

end

%% =========================
%% HEALTHCARE SERVICES
%% =========================

subgraph SERVICES["Healthcare Workflow Services"]

M[Doctor Availability Service]
N[Appointment Scheduling Engine]
O[Patient Query Processing]

end

%% =========================
%% RESPONSE PIPELINE
%% =========================

subgraph RESPONSE["Voice Response Pipeline"]

P[ElevenLabs Text-to-Speech]
Q[AI Voice Response Generator]

end

%% =========================
%% FLOW CONNECTIONS
%% =========================

A --> C
C --> D
D --> E
E --> F
F --> G

G --> H
H --> I
I --> J

J --> K
K --> L

J --> M
J --> N
J --> O

M --> P
N --> P
O --> P

P --> Q
Q --> A

%% =========================
%% DASHBOARD CONNECTIONS
%% =========================

B --> J
B --> K
B --> N

%% =========================
%% STYLING
%% =========================

style CLIENT fill:#0f172a,stroke:#60a5fa,color:#ffffff
style TELEPHONY fill:#1e293b,stroke:#38bdf8,color:#ffffff
style SPEECH fill:#0f766e,stroke:#5eead4,color:#ffffff
style AI fill:#1e3a8a,stroke:#93c5fd,color:#ffffff
style MEMORY fill:#312e81,stroke:#a5b4fc,color:#ffffff
style SERVICES fill:#581c87,stroke:#d8b4fe,color:#ffffff
style RESPONSE fill:#7c2d12,stroke:#fdba74,color:#ffffff
```


---

# System Architecture

## Telephony Layer

Responsible for handling inbound and outbound clinic communication workflows.

### Technologies

* Twilio Voice
* Webhook-based communication routing
* Real-time voice event handling

---

## Speech Processing Layer

Converts multilingual patient audio into structured conversational text.

### Technologies

* Deepgram Speech-to-Text
* Streaming transcription pipeline
* Multilingual voice processing

---

## Conversational AI Layer

Processes conversational intent, appointment requests, scheduling logic, and operational workflows.

### Technologies

* Groq LLM
* Prompt orchestration
* Intent extraction
* Conversational routing

---

## Session Memory Layer

Maintains conversational state and workflow continuity across patient interactions.

### Technologies

* Redis
* Distributed session persistence
* Context-aware conversation tracking

---

## Voice Response Layer

Generates multilingual AI voice responses for patient communication.

### Technologies

* ElevenLabs TTS
* Voice synthesis pipeline
* Real-time audio generation

---

# Backend Architecture

```text
backend/
│
├── app/
│   ├── core/
│   ├── middleware/
│   ├── routes/
│   ├── services/
│   ├── voice/
│   ├── ai/
│   ├── models/
│   └── utils/
│
├── tests/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── main.py
```

---

# Key Features

## Multilingual Voice Communication

Supports multilingual patient interactions including English, Tamil, and Tanglish conversational workflows.

---

## AI-Powered Appointment Handling

Automates doctor availability checks, appointment inquiries, and scheduling workflows.

---

## Distributed Conversational Memory

Maintains contextual conversation state using Redis-backed session infrastructure.

---

## Low-Latency AI Pipeline

Built around asynchronous FastAPI workflows for real-time conversational responsiveness.

---

## Modular Service Architecture

Designed using modular backend services for maintainability and scalable orchestration.

---

# Technology Stack

| Layer              | Technologies   |
| ------------------ | -------------- |
| Backend Framework  | FastAPI        |
| Telephony          | Twilio         |
| Speech Recognition | Deepgram       |
| Conversational AI  | Groq           |
| Session Memory     | Redis          |
| Voice Synthesis    | ElevenLabs     |
| Containerization   | Docker         |
| CI/CD              | GitHub Actions |

---

# Repository Architecture Linking

The frontend architecture diagram directly links to relevant backend implementation modules.

## Example Mappings

| Architecture Node | Backend Module                     |
| ----------------- | ---------------------------------- |
| Twilio Voice      | `/app/routes/voice_routes.py`      |
| Deepgram STT      | `/app/voice/`                      |
| Groq LLM          | `/app/services/ai_brain.py`        |
| Redis Sessions    | `/app/services/session_service.py` |
| ElevenLabs TTS    | `/app/voice/tts_service.py`        |

---

# Deployment Roadmap

## Current Status

* Backend architecture implemented
* Voice workflow orchestration implemented
* Frontend operational workflow simulation completed
* Architecture visualization integrated
* API integrations in progress

---

## Planned Improvements

* Real-time streaming voice pipeline
* Production deployment infrastructure
* Kubernetes orchestration
* Healthcare CRM integration
* Analytics dashboards
* Multi-clinic tenancy
* AI workflow optimization

---

# Local Development Setup

## Clone Repository

```bash
git clone https://github.com/yourusername/clinivo-ai.git
```

---

## Create Environment

```bash
python -m venv venv
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file:

```env
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
DEEPGRAM_API_KEY=
GROQ_API_KEY=
ELEVENLABS_API_KEY=
REDIS_URL=
```

---

## Run Application

```bash
uvicorn main:app --reload
```

---

# Frontend Workflow Visualization

The landing page includes:

* Animated AI workflow architecture
* Interactive infrastructure nodes
* GitHub-linked backend modules
* Operational workflow simulation dashboard
* Responsive healthcare SaaS interface

---

# Disclaimer

This project is currently an engineering prototype and workflow simulation platform focused on healthcare voice automation infrastructure.

It is not currently deployed in production clinical environments.

---

# Contact

## Mohamed Shalman Kursheeth K

Backend Engineering • AI Systems • Voice Infrastructure

📧 [nailashalman001@gmail.com](mailto:nailashalman001@gmail.com)


---

# License

MIT License
