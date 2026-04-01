# fastapi_app.py
# FastAPI REST API for Multi-Agent Document Intelligence Pipeline
# Endpoint: POST /analyze — upload PDF, get extracted fields as JSON

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import shutil
import subprocess
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Multi-Agent Document Intelligence API",
    description="Upload a contract PDF → 4 AI agents extract and validate key fields automatically.",
    version="1.0.0"
)

# ── HELPER: RUN AGENT ────────────────────────────────────────
def run_agent(script_name):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    return result.returncode == 0, result.stdout + result.stderr

# ── HELPER: LOAD JSON ────────────────────────────────────────
def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

# ── ROOT ENDPOINT ────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "Multi-Agent Document Intelligence API",
        "version": "1.0.0",
        "built_by": "ZenithQuest",
        "endpoints": {
            "POST /analyze": "Upload PDF → get extracted contract fields",
            "GET /report": "Download the latest PDF report",
            "GET /health": "API health check"
        }
    }

# ── HEALTH CHECK ─────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "healthy", "message": "Pipeline API is running"}

# ── MAIN ENDPOINT — ANALYZE PDF ──────────────────────────────
@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    """
    Upload a contract PDF.
    Returns extracted fields, validation scores, and pipeline summary.
    """

    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    # Save uploaded file as sample_document.pdf
    upload_path = "sample_document.pdf"
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run all 4 agents in sequence
    agents = [
        "agent1_loader.py",
        "agent2_extractor.py",
        "agent3_generator.py",
        "agent4_validator.py"
    ]

    agent_logs = {}
    for script in agents:
        success, output = run_agent(script)
        agent_logs[script] = {
            "status": "success" if success else "failed",
            "output": output[-500:] if len(output) > 500 else output
        }
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"{script} failed. Check logs for details."
            )

    # Load results
    agent2_data = load_json("agent2_extractions.json")
    agent4_data = load_json("agent4_validation_report.json")

    if not agent2_data or not agent4_data:
        raise HTTPException(
            status_code=500,
            detail="Pipeline completed but output files not found."
        )

    # Build clean response
    response = {
        "status": "success",
        "source_file": file.filename,
        "pipeline_summary": {
            "total_fields": agent4_data["total_fields"],
            "confirmed": agent4_data["supported"],
            "flags_raised": agent4_data["flags_raised"],
            "pipeline_score": agent4_data["pipeline_score"]
        },
        "extracted_fields": agent2_data["extracted_fields"],
        "validation": [
            {
                "field": v["field"],
                "status": v["status"],
                "confidence": v["confidence"],
                "flag": v["flag"]
            }
            for v in agent4_data["field_validations"]
        ],
        "report_available": os.path.exists("agent3_contract_report.pdf")
    }

    return JSONResponse(content=response)

# ── DOWNLOAD REPORT ENDPOINT ─────────────────────────────────
@app.get("/report")
def download_report():
    """Download the latest generated PDF report."""
    report_path = "agent3_contract_report.pdf"
    if not os.path.exists(report_path):
        raise HTTPException(
            status_code=404,
            detail="No report found. Run /analyze first."
        )
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename="contract_intelligence_report.pdf"
    )