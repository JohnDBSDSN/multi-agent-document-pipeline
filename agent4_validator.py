import sys
sys.stdout.reconfigure(encoding='utf-8')

﻿# agent4_validator.py
# Agent 4 — Validation Agent
# Cross-checks Agent 2 extractions against source chunks in FAISS.
# Scores confidence per field. Flags low-confidence or missing fields.
# Saves agent4_validation_report.json for pipeline audit trail.

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

# ── 2. LOAD AGENT 2 EXTRACTIONS ──────────────────────────────
print("\n[Agent 4] Loading Agent 2 extraction results...")

with open("agent2_extractions.json", "r") as f:
    agent2_data = json.load(f)

extracted_fields = agent2_data["extracted_fields"]
retrieval_log    = agent2_data["retrieval_log"]
source_file      = agent2_data["source_file"]

print(f"[Agent 4] Source: {source_file}")
print(f"[Agent 4] Fields to validate: {len(extracted_fields)}")

# ── 3. LOAD FAISS INDEX ──────────────────────────────────────
print("[Agent 4] Loading FAISS index for source verification...")

embeddings  = OpenAIEmbeddings(openai_api_key=api_key)
faiss_index = FAISS.load_local(
    "agent_faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)
print("[Agent 4] FAISS index loaded.")

# ── 4. SETUP LLM ─────────────────────────────────────────────
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    openai_api_key=api_key
)

# ── 5. VALIDATION PROMPT ─────────────────────────────────────
# Asks GPT: given the source chunk, is this extracted value supported?
# Returns structured response: SUPPORTED / PARTIAL / NOT_SUPPORTED
# + a confidence score 0-100 + a short reason.

validation_prompt = PromptTemplate(
    input_variables=["field", "extracted_value", "source_chunk"],
    template="""You are a contract validation assistant.
Your job is to verify whether an extracted value is supported by the source text.

Field: {field}
Extracted value: {extracted_value}
Source chunk from document:
{source_chunk}

Evaluate the extracted value against the source chunk.
Respond in this exact format — nothing else:
STATUS: <SUPPORTED | PARTIAL | NOT_SUPPORTED | NOT_FOUND>
CONFIDENCE: <0-100>
REASON: <one sentence explanation>

Rules:
- SUPPORTED: extracted value is clearly present and accurate in source chunk
- PARTIAL: extracted value is close but incomplete or slightly inaccurate
- NOT_SUPPORTED: extracted value contradicts or is absent from source chunk
- NOT_FOUND: extracted value is "Not found" and source chunk confirms absence
- CONFIDENCE: 90-100 for clear matches, 60-89 for partial, 0-59 for weak"""
)

chain = validation_prompt | llm | StrOutputParser()

# ── 6. PARSE VALIDATION RESPONSE ─────────────────────────────
def parse_validation_response(response_text):
    """Parses the structured STATUS/CONFIDENCE/REASON response from LLM."""
    result = {
        "status": "UNKNOWN",
        "confidence": 0,
        "reason": "Could not parse response"
    }
    for line in response_text.strip().splitlines():
        line = line.strip()
        if line.startswith("STATUS:"):
            result["status"] = line.replace("STATUS:", "").strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                result["confidence"] = int(line.replace("CONFIDENCE:", "").strip())
            except ValueError:
                result["confidence"] = 0
        elif line.startswith("REASON:"):
            result["reason"] = line.replace("REASON:", "").strip()
    return result

# ── 7. RUN VALIDATION LOOP ───────────────────────────────────
print("\n[Agent 4] Starting field-by-field validation...\n")

validation_results = []
overall_flags      = []

for field_name, extracted_value in extracted_fields.items():

    # Find the source chunk used for this field (from retrieval log)
    source_chunk = None
    for log_entry in retrieval_log:
        if log_entry["field"] == field_name:
            source_chunk = log_entry["source_chunk_preview"]
            break

    # If not in retrieval log (e.g. "Not found" fields), re-query FAISS
    if not source_chunk:
        docs = faiss_index.similarity_search(field_name.replace("_", " "), k=1)
        source_chunk = docs[0].page_content if docs else "No source chunk available"

    # Run validation
    response = chain.invoke({
        "field":           field_name.replace("_", " "),
        "extracted_value": extracted_value,
        "source_chunk":    source_chunk
    })

    parsed = parse_validation_response(response)

    # Flag low confidence or unsupported fields
    flag = None
    if parsed["status"] == "NOT_SUPPORTED":
        flag = " EXTRACTION MISMATCH — value not found in source"
    elif parsed["status"] == "PARTIAL":
        flag = " PARTIAL MATCH — may need manual review"
    elif parsed["confidence"] < 60:
        flag = "LOW CONFIDENCE — verify manually"

    if flag:
        overall_flags.append({"field": field_name, "flag": flag})

    field_result = {
        "field":           field_name,
        "extracted_value": extracted_value,
        "status":          parsed["status"],
        "confidence":      parsed["confidence"],
        "reason":          parsed["reason"],
        "source_preview":  source_chunk[:150] + "..." if len(source_chunk) > 150 else source_chunk,
        "flag":            flag
    }

    validation_results.append(field_result)

    # Console output
    status_icon = {
        "SUPPORTED":     "OK",
        "PARTIAL":       "~",
        "NOT_SUPPORTED": "FAIL",
        "NOT_FOUND":     "–",
        "UNKNOWN":       "?"
    }.get(parsed["status"], "?")

    print(f"  {status_icon} [{parsed['confidence']:>3}%] {field_name}: {parsed['status']}")
    if flag:
        print(f"         {flag}")

# ── 8. COMPUTE PIPELINE SCORE ────────────────────────────────
supported_count = sum(
    1 for r in validation_results
    if r["status"] in ("SUPPORTED", "NOT_FOUND")
)
total           = len(validation_results)
pipeline_score  = round((supported_count / total) * 100, 1) if total > 0 else 0

# ── 9. SAVE VALIDATION REPORT ────────────────────────────────
validation_report = {
    "agent":            "Agent 4 — Validation Agent",
    "source_file":      source_file,
    "total_fields":     total,
    "supported":        supported_count,
    "flags_raised":     len(overall_flags),
    "pipeline_score":   f"{pipeline_score}%",
    "overall_flags":    overall_flags,
    "field_validations": validation_results
}

output_file = "agent4_validation_report.json"
with open(output_file, "w") as f:
    json.dump(validation_report, f, indent=2)

# ── 10. PRINT FINAL SUMMARY ──────────────────────────────────
print(f"\n{'='*50}")
print(f"[Agent 4] VALIDATION COMPLETE")
print(f"{'='*50}")
print(f"  Total fields validated : {total}")
print(f"  Supported / Confirmed  : {supported_count}")
print(f"  Flags raised           : {len(overall_flags)}")
print(f"  Pipeline Score         : {pipeline_score}%")
print(f"{'='*50}")

if overall_flags:
    print("\n  FLAGS:")
    for flag_item in overall_flags:
        print(f"    -> {flag_item['field']}: {flag_item['flag']}")

print(f"\n[Agent 4] Report saved -> {output_file}")
print("[Agent 4] Pipeline complete. Ready for Streamlit UI.")
