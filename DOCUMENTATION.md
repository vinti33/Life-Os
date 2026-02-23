# LifeOS: The AI Personal Optimizer 🚀

LifeOS is a premium, privacy-first personal planning platform that uses local AI to orchestrate your time, health, and goals.

---

## ✨ Core Features

### 🛡️ Sleep Guard Protocol
Ensures your productivity never comes at the cost of your health. The system enforces an absolute "Sleep Boundary" that prevents any tasks from being scheduled past your bedtime.

### 🩹 Self-Healing Protocol
If the AI makes a mistake or a plan becomes fragmented, the system automatically:
- Programmatically corrects task names based on time (e.g., "Afternoon" tasks at 8 PM are renamed to "Evening").
- Resolves overlapping tasks by prioritized shifting.
- Fills gaps with meaningful routine blocks.

### 🧠 RAG (Retrieval-Augmented) Memory
A local knowledge base that stores your "Rules of Life." The AI retrieves these patterns every time it generates a plan to ensure your schedule reflects your long-term values.

---

## 🚀 Getting Started

### 1. Requirements
- **Ollama**: Must be running on your host machine.
- **Docker**: For running the database, cache, and backend services.

### 2. Setup (Docker Stack)
```bash
cd infrastructure
docker compose up -d --build
```

### 3. Initialize Memory
Run the RAG builder to index your initial patterns:
```bash
docker exec -it infrastructure-backend-1 python3 -m rag.manager
```

### 4. Configuration
Edit your profile and AI settings in:
- **Profile**: Accessible via the UI dashboard.
- **Environment**: [backend/.env](file:///home/vinti/LifeOS/backend/.env)

---

## 🛠️ Technical Stack

- **Frontend**: Next.js 15 (React) + Tailwind CSS (Optimized for dark mode).
- **Backend**: FastAPI (Python) — High-performance async API.
- **Database**: 
  - **MongoDB**: Primary storage for plans and tasks (via Beanie ODM).
  - **Redis**: Caching and background job queueing.
- **AI Engine**: Local Ollama (optimized for `phi3:mini`).
- **Vector Search**: FAISS for lightning-fast memory retrieval.

---

## 🧭 How to Use

### 🏗️ The Auto-Architect
Click the **"Auto-Architect"** button on the dashboard. The AI will:
1.  Analyze your recent feedback and failure patterns.
2.  Retrieve your "Rules of Life" from memory.
3.  Generate a 100% gap-free, overlap-free daily plan.

### 💬 Chatbot Commands
You can interact with the AI via the chat interface:
- *"Plan my day"* — Forces a fresh generation.
- *"Add gym at 6pm"* — Real-time plan modification.
- *"Move my work block to 9am"* — Intelligent rescheduling with conflict resolution.

---

## 🔧 Troubleshooting

### 🌐 "Network Error" on Generation
If you see a Network Error during planning:
1.  **Timeout**: The system is configured with a **15-minute** wait window to accommodate slower CPUs. Ensure your hardware isn't under extreme load.
2.  **Refresh**: Sometimes the browser drops the connection; a simple refresh usually fixes this.

### 🔄 Slow Backend Response / Timeouts
- **Local AI Speed**: Generation can take 2-10 minutes depending on your CPU/GPU. The system has a **15-minute window** to prevent errors.
- **Optimization**: We've tuned the AI to use **768 tokens** and a **lean profile** for maximum speed.
- **Protocol**: If the chatbot feels stuck, try the **"Auto-Architect"** button on the dashboard for a direct override.

---

*LifeOS — Optimized Living through Orchestrated AI.*
