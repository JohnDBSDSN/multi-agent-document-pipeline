import sys
sys.stdout.reconfigure(encoding='utf-8')

﻿# agent2_extractor.py
# Agent 2 — Extraction Agent
# Loads FAISS index from Agent 1, runs semantic search queries,
# extracts key contract fields using GPT, saves structured JSON.

import os
import json
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ── 1. LOAD ENV ──────────────────────────────────────────────
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

# ── 2. LOAD FAISS INDEX (built by Agent 1) ───────────────────
print("\n[Agent 2] Loading FAISS index...")

embeddings = OpenAIEmbeddings(openai_api_key=api_key)

faiss_index = FAISS.load_local(
    "agent_faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)
print("[Agent 2] FAISS index loaded successfully.")

# ── 3. LOAD AGENT 1 METADATA ─────────────────────────────────
with open("agent1_metadata.json", "r") as f:
    agent1_meta = json.load(f)

print(f"[Agent 2] Document: {agent1_meta['pdf_path']}")
print(f"[Agent 2] Total chunks available: {agent1_meta['chunks']}")

# ── 4. DEFINE EXTRACTION QUERIES ─────────────────────────────
# Each query targets a specific contract field.
# FAISS will find the most relevant chunk for each.

extraction_queries = {
    "parties_involved":   "Who are the parties involved in this contract? Names of the client and service provider.",
    "contract_date":      "What is the contract start date, effective date, or signing date?",
    "contract_duration":  "What is the duration or term of this contract? When does it expire or end?",
    "payment_terms":      "What are the payment terms? Amount, schedule, and method of payment.",
    "deliverables":       "What are the deliverables or services to be provided under this contract?",
    "termination_clause": "What are the conditions or terms for terminating this contract?",
    "governing_law":      "What governing law or jurisdiction applies to this contract?",
    "confidentiality":    "Is there a confidentiality or non-disclosure clause? What does it say?"
}

# ── 5. SETUP LLM ─────────────────────────────────────────────
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,          # deterministic — we want facts, not creativity
    openai_api_key=api_key
)

# ── 6. EXTRACTION PROMPT ─────────────────────────────────────
# Instructs GPT to extract ONLY from the provided context chunk.
# If info is missing, it says "Not found" — no hallucination.

extraction_prompt = PromptTemplate(
    input_variables=["field", "context"],
    template="""You are a contract analysis assistant.
Extract the following information from the contract text below.
Be concise and factual. Only use information present in the text.
If the information is not found, respond with exactly: Not found

Field to extract: {field}

Contract text:
{context}

Extracted value:"""
)

chain = extraction_prompt | llm | StrOutputParser()

# ── 7. RUN EXTRACTION LOOP ───────────────────────────────────
print("\n[Agent 2] Starting extraction...\n")

extracted_fields = {}
retrieval_log = []     # tracks which chunk answered which query

for field_name, query in extraction_queries.items():

    # Semantic search — find the most relevant chunk for this query
    docs = faiss_index.similarity_search(query, k=1)

    if not docs:
        extracted_fields[field_name] = "Not found"
        print(f"  FAIL {field_name}: No relevant chunk found")
        continue

    top_chunk = docs[0].page_content

    # Run LLM extraction on the retrieved chunk
    result = chain.invoke({"field": field_name.replace("_", " "), "context": top_chunk})
    extracted_value = result.strip()

    extracted_fields[field_name] = extracted_value

    # Log which chunk was used (useful for Agent 4 validation)
    retrieval_log.append({
        "field": field_name,
        "query_used": query,
        "source_chunk_preview": top_chunk[:200] + "..." if len(top_chunk) > 200 else top_chunk
    })

    print(f"  OK {field_name}: {extracted_value}")

# ── 8. SAVE OUTPUT JSON ──────────────────────────────────────
output = {
    "agent": "Agent 2 — Extraction Agent",
    "source_file": agent1_meta["pdf_path"],
    "total_chunks_in_index": agent1_meta["chunks"],
    "fields_extracted": len(extracted_fields),
    "extracted_fields": extracted_fields,
    "retrieval_log": retrieval_log
}

output_file = "agent2_extractions.json"
with open(output_file, "w") as f:
    json.dump(output, f, indent=2)

print(f"\n[Agent 2] Extraction complete.")
print(f"[Agent 2] {len(extracted_fields)} fields extracted.")
print(f"[Agent 2] Results saved -> {output_file}")
print("\n--- EXTRACTION SUMMARY ---")
for field, value in extracted_fields.items():
    print(f"  {field}: {value}")
