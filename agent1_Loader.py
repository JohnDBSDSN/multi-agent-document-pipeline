"""
============================================================
Multi-Agent Document Intelligence Pipeline
============================================================
Agent 1 — Document Loader Agent
Author  : John Daniel Bakht Singh A | ZenithQuest
Date    : April 2026

WHAT THIS AGENT DOES:
→ Accepts any PDF document
→ Loads and splits into chunks
→ Creates embeddings using Ada-002
→ Builds FAISS vector index
→ Saves index to disk for other agents
→ Returns: chunk count, page count, status

HOW TO RUN:
    python agent1_loader.py

PRE-REQUISITES:
    pip install langchain langchain-community
    pip install langchain-openai faiss-cpu
    pip install pypdf python-dotenv
    .env file with OPENAI_API_KEY
============================================================
"""

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os
import json

# ── Load environment ──────────────────────────────────────
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found. Check your .env file.")

# ── Agent 1 — Document Loader Agent ──────────────────────
def agent1_load_document(pdf_path: str, index_folder: str = "agent_faiss_index") -> dict:
    """
    Agent 1: Loads PDF, chunks it, builds FAISS index.
    
    INPUT:  Path to any PDF document
    OUTPUT: Status report as dictionary
    """
    
    print("\n" + "="*60)
    print("AGENT 1 — Document Loader Agent")
    print("="*60)
    
    # ── Step 1: Load PDF ──────────────────────────────────
    print(f"\n[Step 1] Loading PDF: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        return {
            "status": "error",
            "message": f"PDF not found: {pdf_path}",
            "agent": "Agent 1 — Document Loader"
        }
    
    loader = PyPDFLoader(pdf_path)
    pages  = loader.load()
    
    print(f"         Pages loaded: {len(pages)}")
    
    # ── Step 2: Chunk the pages ───────────────────────────
    print(f"\n[Step 2] Splitting into chunks...")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = 500,   # Max 500 characters per chunk
        chunk_overlap = 50,    # 50 char overlap between chunks
        length_function = len
    )
    
    chunks = splitter.split_documents(pages)
    
    print(f"         Total chunks: {len(chunks)}")
    print(f"         Avg chunk size: {sum(len(c.page_content) for c in chunks) // len(chunks)} chars")
    
    # ── Step 3: Create embeddings + FAISS index ───────────
    print(f"\n[Step 3] Creating embeddings + FAISS index...")
    print(f"         (Calling OpenAI Ada-002 — costs fractions of a cent)")
    
    embeddings   = OpenAIEmbeddings(model="text-embedding-ada-002")
    vectorstore  = FAISS.from_documents(chunks, embeddings)
    
    print(f"         Vectors stored: {vectorstore.index.ntotal}")
    print(f"         Dimensions: 1536")
    
    # ── Step 4: Save index to disk ────────────────────────
    print(f"\n[Step 4] Saving FAISS index to disk...")
    
    vectorstore.save_local(index_folder)
    
    print(f"         Saved to: {index_folder}/")
    print(f"         Files: index.faiss + index.pkl")
    
    # ── Step 5: Save metadata for other agents ────────────
    metadata = {
        "pdf_path"    : pdf_path,
        "pages"       : len(pages),
        "chunks"      : len(chunks),
        "index_folder": index_folder,
        "status"      : "ready"
    }
    
    with open("agent1_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n[Step 5] Metadata saved → agent1_metadata.json")
    
    # ── Agent 1 Complete ──────────────────────────────────
    result = {
        "status"      : "success",
        "agent"       : "Agent 1 — Document Loader",
        "pdf_path"    : pdf_path,
        "pages"       : len(pages),
        "chunks"      : len(chunks),
        "index_folder": index_folder,
        "message"     : "Document loaded and indexed. Ready for Agent 2."
    }
    
    print("\n" + "="*60)
    print("AGENT 1 COMPLETE ")
    print(f"Pages: {len(pages)} | Chunks: {len(chunks)}")
    print(f"Index saved to: {index_folder}/")
    print(f"Status: Document ready for Agent 2")
    print("="*60 + "\n")
    
    return result


# ── RUN AGENT 1 ───────────────────────────────────────────
if __name__ == "__main__":
    
    # ── CHANGE THIS to your PDF path ─────────────────────
    PDF_PATH = "sample_document.pdf"
    
    # ── If no PDF exists, create a simple test one ────────
    if not os.path.exists(PDF_PATH):
        print(f"\n  No PDF found at: {PDF_PATH}")
        print("Creating a simple test PDF...")
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            
            c = canvas.Canvas(PDF_PATH, pagesize=letter)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 750, "Sample Business Contract")
            c.setFont("Helvetica", 12)
            
            lines = [
                "",
                "Section 1 - Parties",
                "This agreement is between TechCorp Inc and ClientCo Ltd.",
                "Effective date: January 1, 2026.",
                "",
                "Section 2 - Services",
                "TechCorp will provide AI development services including:",
                "- RAG pipeline development",
                "- Multi-agent system design",
                "- FastAPI deployment",
                "- Streamlit UI development",
                "",
                "Section 3 - Payment",
                "Client agrees to pay $5,000 per month.",
                "Payment is due within 30 days of invoice.",
                "Late payments incur 2% monthly interest.",
                "",
                "Section 4 - Duration",
                "This contract runs for 6 months from the effective date.",
                "Either party may terminate with 30 days written notice.",
                "",
                "Section 5 - Confidentiality",
                "Both parties agree to keep all project details confidential.",
                "This obligation survives termination of the agreement.",
                "",
                "Section 6 - Intellectual Property",
                "All work product belongs to the client upon full payment.",
                "TechCorp retains rights to reusable code components.",
                "",
                "Section 7 - Dispute Resolution",
                "Disputes will be resolved through arbitration in New York.",
                "Governing law: State of New York.",
            ]
            
            y = 720
            for line in lines:
                c.drawString(100, y, line)
                y -= 20
                if y < 100:
                    c.showPage()
                    y = 750
            
            c.save()
            print(f" Test PDF created: {PDF_PATH}")
            
        except ImportError:
            print("reportlab not installed.")
            print("Please provide your own PDF file.")
            print("Update PDF_PATH variable in this script.")
            exit(1)
    
    # ── Run Agent 1 ───────────────────────────────────────
    result = agent1_load_document(PDF_PATH)
    
    print("\nAgent 1 Output:")
    print(json.dumps(result, indent=2))