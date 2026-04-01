# 🤖 Multi-Agent Document Intelligence Pipeline

> Upload any contract PDF → 4 AI agents extract, analyse, and validate key clauses automatically — in under 60 seconds.

Built by **[ZenithQuest](https://github.com/JohnDBSDSN)** · Powered by LangChain · OpenAI · FAISS · ReportLab · Streamlit

---

## 📌 What This Does

Most businesses spend hours manually reading contracts to extract key information — party names, payment terms, termination clauses, governing law. This pipeline automates that entire process.

Upload any contract PDF through the Streamlit UI. Four AI agents fire in sequence:

| Agent | Role | Output |
|-------|------|--------|
| 🗂 Agent 1 — Loader | Reads the PDF, splits into chunks, builds a FAISS vector index | `agent_faiss_index/` + `agent1_metadata.json` |
| 🔍 Agent 2 — Extractor | Runs semantic search queries, extracts 8 contract fields using GPT | `agent2_extractions.json` |
| 📋 Agent 3 — Generator | Builds a formatted, branded PDF report | `agent3_contract_report.pdf` |
| ✅ Agent 4 — Validator | Cross-checks every extraction against source chunks, scores confidence | `agent4_validation_report.json` |

The Streamlit UI ties all four agents together — one click, live progress, downloadable report.

---

## 🎯 Who Is This For?

- **Legal teams** — auto-extract key clauses from contracts and NDAs
- **HR departments** — review employment agreements at scale
- **Procurement teams** — validate vendor contracts instantly
- **Finance teams** — extract payment and termination terms without manual reading
- **Any business** that handles high volumes of PDF documents

---

## 🖥️ Live Demo

> 📺 **[Watch the full demo on YouTube](#)** ← *(link added after upload)*

---

## 🏗️ Architecture

```
                    ┌─────────────────────────────────┐
                    │        Streamlit UI              │
                    │   Upload PDF → Run All Agents   │
                    └────────────┬────────────────────┘
                                 │
              ┌──────────────────▼──────────────────┐
              │           AGENT 1 — LOADER           │
              │  PyPDF → Text Splitter → Ada-002     │
              │  Embeddings → FAISS Vector Index     │
              └──────────────────┬──────────────────┘
                                 │ agent1_metadata.json
              ┌──────────────────▼──────────────────┐
              │         AGENT 2 — EXTRACTOR          │
              │  8 Semantic Queries → FAISS Search   │
              │  → GPT-3.5 Extraction (temp=0)       │
              └──────────┬───────────────────────────┘
                         │ agent2_extractions.json
          ┌──────────────▼──────┐   ┌───────────────▼──────────────┐
          │  AGENT 3 — GENERATOR│   │    AGENT 4 — VALIDATOR        │
          │  ReportLab PDF      │   │  Re-query FAISS → GPT         │
          │  Branded Report     │   │  Confidence Score per Field   │
          └─────────────────────┘   └──────────────────────────────┘
                         │                       │
               PDF Report Download    agent4_validation_report.json
```

**Key design pattern — JSON handoffs between agents:**
Each agent reads the previous agent's output file. No agent re-does work already done. This is what makes it a true pipeline rather than a single monolithic script.

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| LLM | OpenAI GPT-3.5-turbo |
| Embeddings | OpenAI Ada-002 |
| Vector Store | FAISS (local) |
| Orchestration | LangChain |
| PDF Reading | PyPDF |
| PDF Generation | ReportLab |
| UI | Streamlit |
| Environment | python-dotenv |

---

## ⚙️ Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/JohnDBSDSN/multi-agent-pipeline.git
cd multi-agent-pipeline
```

### 2. Create and Activate Virtual Environment

```bash
# Windows
python -m venv multi_agent_env
multi_agent_env\Scripts\activate

# Mac / Linux
python -m venv multi_agent_env
source multi_agent_env/bin/activate
```

### 3. Install Dependencies

```bash
pip install langchain langchain-community langchain-openai langchain-text-splitters
pip install faiss-cpu pypdf python-dotenv reportlab streamlit
```

### 4. Set Up Your API Key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
```

> ⚠️ **IMPORTANT — Never share your API key.**
> The `.env` file is listed in `.gitignore` and will NOT be pushed to GitHub.
> Never hardcode your API key directly in any Python file.
> Never paste your API key in a public forum, chat, or README.
> If you accidentally expose your key, rotate it immediately at [platform.openai.com](https://platform.openai.com/api-keys).

### 5. Add Your `.gitignore`

Make sure your `.gitignore` includes:

```
.env
__pycache__/
*.pyc
multi_agent_env/
agent_faiss_index/
*.pdf
*.json
```

---

## 🚀 Running the Pipeline

### Option A — Streamlit UI (Recommended)

```bash
python -m streamlit run MAD_Streamlit_app.py
```

- Browser opens at `http://localhost:8501`
- Upload any contract PDF
- Click **Run All Agents**
- Watch live agent-by-agent progress
- View extracted fields with confidence scores
- Download the PDF report

### Option B — Run Agents Individually (Terminal)

```bash
# Step 1 — Load PDF and build FAISS index
python agent1_loader.py

# Step 2 — Extract contract fields
python agent2_extractor.py

# Step 3 — Generate PDF report
python agent3_generator.py

# Step 4 — Validate extractions
python agent4_validator.py
```

---

## 📊 What Gets Extracted

The pipeline queries 8 contract fields:

| Field | Description |
|-------|-------------|
| Parties Involved | Names of client and service provider |
| Contract Date | Effective or signing date |
| Contract Duration | Term length and expiry |
| Payment Terms | Amount, schedule, method |
| Deliverables / Services | What is being provided |
| Termination Clause | Conditions for ending the contract |
| Governing Law | Jurisdiction that applies |
| Confidentiality Clause | NDA / confidentiality terms |

Each field is validated by Agent 4 with a status and confidence score:

| Status | Meaning |
|--------|---------|
| ✅ Supported | Extraction confirmed against source chunk |
| – Not Found | Field genuinely absent from document |
| ~ Partial | Partially matched — may need review |
| ✗ Mismatch | Extraction not supported by source — flagged |

---

## 📁 Project Structure

```
multi-agent-pipeline/
│
├── agent1_loader.py          # Agent 1 — PDF loader and FAISS indexer
├── agent2_extractor.py       # Agent 2 — Contract field extractor
├── agent3_generator.py       # Agent 3 — PDF report generator
├── agent4_validator.py       # Agent 4 — Extraction validator
├── MAD_Streamlit_app.py      # Streamlit UI — orchestrates all agents
│
├── agent_faiss_index/        # FAISS vector index (auto-generated)
├── agent1_metadata.json      # Agent 1 output (auto-generated)
├── agent2_extractions.json   # Agent 2 output (auto-generated)
├── agent3_contract_report.pdf# Agent 3 output (auto-generated)
├── agent4_validation_report.json # Agent 4 output (auto-generated)
│
├── sample_document.pdf       # Your uploaded PDF (replaced on each run)
├── .env                      # API key — NOT committed to GitHub
├── .gitignore
└── README.md
```

---

## 🔐 API Key Security — Read This

```
✅ Store your key in .env file only
✅ Add .env to .gitignore before your first commit
✅ Use os.getenv("OPENAI_API_KEY") in code — never hardcode
❌ Never paste your key in code files
❌ Never share your key in chat, email, or forums
❌ Never commit .env to GitHub
```

If you've already accidentally committed a key:
1. Immediately rotate it at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Remove the key from git history using `git filter-branch` or BFG Repo Cleaner
3. Force push the clean history

---

## 💡 How It Works — Plain English

**Why 4 separate agents instead of one script?**
Each agent has one job. If extraction fails, the loader and index are still intact. If you want to change the report format, you only touch Agent 3 — nothing else changes. This is called separation of concerns — the same principle used in enterprise software.

**Why FAISS?**
FAISS is a local vector store. It finds the most semantically similar text chunk for any query — even if the words don't match exactly. "Who signed this?" will correctly find the chunk that says "This agreement is between TechCorp Inc and ClientCo Ltd."

**Why temperature=0?**
Extraction is a facts-only task. Setting temperature to zero makes GPT deterministic — same input always gives the same output. No creativity needed here.

**Why a separate validation agent?**
Agent 4 independently re-queries the source and asks GPT: "Is this extraction actually supported by the document?" This is a second opinion built into the pipeline — it quantifies trust and catches any extraction errors before the report is delivered.

---

## 🗺️ Production Roadmap

| Enhancement | Description |
|-------------|-------------|
| Persistent vector store | Replace FAISS with Pinecone or Weaviate for multi-document storage |
| Async processing | Replace subprocess orchestration with Celery or LangGraph |
| REST API | Expose pipeline via FastAPI for enterprise integration |
| Human-in-the-loop | Flag PARTIAL extractions for manual review before report generation |
| Auto re-query | If confidence < 70%, automatically re-query with k=2 |
| Multi-document batch | Process entire folders of contracts in one run |

---

## 👨‍💻 About the Author

**John Daniel** — AI/ML Developer · NLP & LLM Systems · Azure ML

3+ years building production AI systems on a foundation of 15+ years enterprise engineering.

- 🌐 [Portfolio](https://johndbsdsn.github.io)
- 💼 [LinkedIn](https://www.linkedin.com/in/john-daniel-ai/)
- 📺 [YouTube — ZenithQuest](https://www.youtube.com/@ZenithQuest-JD)
- 📝 [Medium](https://medium.com/@a.johndaniel)
- 📧 zenithquest2016@gmail.com

---

## 📄 License

MIT License — free to use, modify, and distribute with attribution.

---

*Built with ❤️ by ZenithQuest · Hyderabad, India*