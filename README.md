# LifeOS: AI-Powered Personal Optimization 🚀

**LifeOS** is a premium, privacy-first personal planner that runs 100% locally. It uses advanced AI orchestration and RAG (Retrieval-Augmented Generation) to turn your goals into a realistic, gap-free daily schedule.

---

## 📖 Documentation Suite

- **[DOCUMENTATION.md](DOCUMENTATION.md)**: **End-User Guide**. Start here for setup, core features (Sleep Guard, Self-Healing), and chatbot usage.
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: **Technical Deep Dive**. Detailed explanation of the agent pipeline, RAG lifecycle, and data flow.
- **[WORK_UPDATE.md](WORK_UPDATE.md)**: Recent development progress and feature releases.

---

## ⚡ Quick Start

1. **Spin up the stack**:
   ```bash
   cd infrastructure
   docker compose up -d --build
   ```

2. **Wait for the AI**:
   The backend will automatically initialize its memory index in the background. Your first schedule generation might take a few minutes as it warms up.

---

## 🛠️ Performance & Privacy

- **100% Local**: No data leaves your machine. Powered by **Ollama** (`phi3:mini`).
- **Resilient**: Optimized with a 15-minute wait window for heavy AI tasks.
- **Reliable**: Built-in "Self-Healing" ensures your schedule is always logical.

---
*Optimized Living through Orchestrated AI.*
