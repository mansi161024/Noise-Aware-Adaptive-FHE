"""
main.py
=======

FastAPI backend for the Noise-Aware Adaptive CKKS FHE experiment dashboard.

Endpoints
---------
GET  /                          Health check
GET  /api/summary               Aggregate metrics from experiment history
GET  /api/experiments           Full experiment history (all runs)
GET  /api/experiments/{id}      Single experiment details
POST /api/experiments/run       Run one strategy (async, returns job id)
POST /api/experiments/run-all   Run all three strategies (async)
GET  /api/experiments/status/{job_id}   Poll job status
GET  /api/experiments/graph-data        Graph-ready data from history

Design notes
------------
- Experiments run in a ThreadPoolExecutor so the HTTP thread is never blocked.
- Results are appended to a JSONL file (one JSON object per line) to support
  unlimited history without in-place rewriting.
- A lock protects concurrent writes to the history file.
- The legacy CSV at results/experiment_results.csv is kept for backward
  compatibility and is also appended to (never overwritten).
- Each experiment run gets a UUID as its experiment_id.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

import csv
import json
import os
import time
import uuid
import threading
import concurrent.futures

from fhe_runner import (
    run_no_bootstrap_experiment,
    run_fixed_bootstrap_experiment,
    run_adaptive_experiment,
    run_all_experiments,
    validate_input,
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Noise-Aware Adaptive FHE API",
    description="Backend API for CKKS FHE bootstrapping strategy experiments",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR  = os.path.join(BASE_DIR, "results")
CSV_PATH     = os.path.join(RESULTS_DIR, "experiment_results.csv")
JSONL_PATH   = os.path.join(RESULTS_DIR, "experiment_history.jsonl")

os.makedirs(RESULTS_DIR, exist_ok=True)


# ============================================================
# THREAD POOL & LOCK
# ============================================================

_executor  = concurrent.futures.ThreadPoolExecutor(max_workers=1)
_write_lock = threading.Lock()

# In-memory job registry:  job_id -> {status, result, error, started_at}
_jobs: Dict[str, Dict[str, Any]] = {}


# ============================================================
# CSV FIELDNAMES (legacy + extended)
# ============================================================

_CSV_FIELDS = [
    "experiment_id",
    "timestamp",
    "policy",
    "strategy",
    "input_values",
    "input_data",
    "operations",
    "fixed_interval",
    "adaptive_threshold",
    "threshold",
    "controller_type",
    "bootstrap_count",
    "bootstrap_time",
    "total_bootstrap_time",
    "encrypt_time",
    "compute_time",
    "decrypt_time",
    "execution_time",
    "total_execution_time",
    "maximum_absolute_error",
    "final_level",
    "final_ciphertext_level",
    "status",
    "failure_reason",
    "error_message",
]


# ============================================================
# POLICY NORMALIZATION
# ============================================================

def normalize_policy_name(policy_str: Optional[str]) -> str:
    """
    Normalizes any policy variant to one of:
    - 'No Bootstrapping'
    - 'Fixed Bootstrapping'
    - 'Adaptive Bootstrapping'
    
    Never falls back to Adaptive.
    """
    if not policy_str:
        return "No Bootstrapping"
    p = policy_str.strip().lower().replace("-", "_").replace(" ", "_")
    if "no" in p or "none" in p:
        return "No Bootstrapping"
    if "fix" in p:
        return "Fixed Bootstrapping"
    if "adapt" in p:
        return "Adaptive Bootstrapping"
    raise ValueError(
        f"Unknown bootstrapping policy: '{policy_str}'. "
        "Supported policies: 'no_bootstrap', 'fixed', 'adaptive'."
    )


# ============================================================
# PERSISTENCE HELPERS
# ============================================================

def _append_to_csv(record: dict) -> None:
    """Append a single experiment record to the CSV file (thread-safe)."""
    with _write_lock:
        file_exists = os.path.isfile(CSV_PATH)
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS, extrasaction="ignore")
            if not file_exists or os.path.getsize(CSV_PATH) == 0:
                writer.writeheader()
            writer.writerow(record)


def _append_to_jsonl(record: dict) -> None:
    """Append a full experiment record (including operation_data) to JSONL."""
    with _write_lock:
        with open(JSONL_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")


def _read_history_jsonl() -> list:
    """Read all experiment records from the JSONL history file."""
    if not os.path.isfile(JSONL_PATH):
        return []
    records = []
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass   # skip corrupted lines
    return records


def _read_history_csv() -> list:
    """Read experiment records from the legacy CSV (summary rows only)."""
    if not os.path.isfile(CSV_PATH):
        return []
    records = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))
    return records


def _persist_result(experiment_id: str, result: dict) -> dict:
    """
    Enrich a raw experiment result with metadata and persist to storage.
    Guarantees all required fields from user specification are present:
    - experiment_id
    - policy
    - timestamp
    - input_values
    - operations
    - fixed_interval
    - adaptive_threshold
    - bootstrap_count
    - bootstrap_time
    - execution_time
    - final_level
    - maximum_absolute_error
    - expected_output
    - decrypted_output
    - status
    - failure_reason
    """
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")

    raw_policy = result.get("policy") or result.get("strategy")
    canonical_policy = normalize_policy_name(raw_policy)

    input_vals = result.get("input_values") or result.get("input_data") or []
    expected_out = result.get("expected_output") or result.get("expected_values") or []
    decrypted_out = result.get("decrypted_output") or result.get("decrypted_values") or []

    b_time = result.get("bootstrap_time", result.get("total_bootstrap_time", 0.0))
    exec_time = result.get("execution_time", result.get("total_execution_time", 0.0))
    f_level = result.get("final_level", result.get("final_ciphertext_level"))
    fail_reason = result.get("failure_reason", result.get("error_message"))

    record = {
        "experiment_id"          : experiment_id,
        "policy"                 : canonical_policy,
        "strategy"               : canonical_policy,
        "timestamp"              : timestamp,
        "input_values"           : input_vals,
        "input_data"             : input_vals,
        "operations"             : result.get("operations", 4),
        "fixed_interval"         : result.get("fixed_interval"),
        "adaptive_threshold"     : result.get("adaptive_threshold"),
        "threshold"              : result.get("threshold", result.get("adaptive_threshold")),
        "controller_type"        : result.get("controller_type", "none"),
        "controller_description" : result.get("controller_description"),
        "bootstrap_count"        : result.get("bootstrap_count", 0),
        "bootstrap_time"         : b_time,
        "total_bootstrap_time"   : b_time,
        "execution_time"         : exec_time,
        "total_execution_time"   : exec_time,
        "encrypt_time"           : result.get("encrypt_time", 0.0),
        "compute_time"           : result.get("compute_time", 0.0),
        "decrypt_time"           : result.get("decrypt_time", 0.0),
        "final_level"            : f_level,
        "final_ciphertext_level" : f_level,
        "maximum_absolute_error" : result.get("maximum_absolute_error"),
        "expected_output"        : expected_out,
        "expected_values"        : expected_out,
        "decrypted_output"       : decrypted_out,
        "decrypted_values"       : decrypted_out,
        "status"                 : result.get("status", "success"),
        "failure_reason"         : fail_reason,
        "error_message"          : fail_reason,
        "operation_data"         : result.get("operation_data", []),
    }

    # Flatten input_data for CSV
    csv_record = dict(record)
    csv_record["input_data"] = json.dumps(record["input_data"])
    csv_record["input_values"] = json.dumps(record["input_values"])
    _append_to_csv(csv_record)

    # Full record (including operation_data) goes to JSONL
    _append_to_jsonl(record)

    return record


# ============================================================
# REQUEST MODELS
# ============================================================

class RunRequest(BaseModel):
    input_data: Optional[List[float]] = None
    input_values: Optional[List[float]] = None
    operations: int          = Field(..., ge=1, le=32)
    policy: Optional[str]    = None
    strategy: Optional[str]  = None
    fixed_interval: int      = Field(default=2, ge=1, le=32)
    threshold: int           = Field(default=2, ge=1, le=32)
    adaptive_threshold: Optional[int] = None
    normalize: bool          = Field(default=False)


class RunAllRequest(BaseModel):
    input_data: Optional[List[float]] = None
    input_values: Optional[List[float]] = None
    operations: int          = Field(..., ge=1, le=32)
    fixed_interval: int      = Field(default=2, ge=1, le=32)
    threshold: int           = Field(default=2, ge=1, le=32)
    adaptive_threshold: Optional[int] = None
    normalize: bool          = Field(default=False)


# ============================================================
# JOB EXECUTION HELPERS
# ============================================================

def _run_single_job(job_id: str, request: RunRequest) -> None:
    """Execute a single-strategy experiment in a background thread."""
    _jobs[job_id]["status"] = "running"
    _jobs[job_id]["started_at"] = time.perf_counter()

    try:
        raw_policy = request.policy or request.strategy or "No Bootstrapping"
        norm_policy = normalize_policy_name(raw_policy)
        raw_input = request.input_values or request.input_data
        if not raw_input:
            raise ValueError("Input vector cannot be empty.")
        input_data = list(raw_input)
        ops        = request.operations
        threshold  = request.adaptive_threshold if request.adaptive_threshold is not None else request.threshold
        interval   = request.fixed_interval

        if norm_policy == "No Bootstrapping":
            result = run_no_bootstrap_experiment(
                input_data=input_data,
                number_of_operations=ops,
            )
        elif norm_policy == "Fixed Bootstrapping":
            result = run_fixed_bootstrap_experiment(
                input_data=input_data,
                number_of_operations=ops,
                fixed_interval=interval,
            )
        elif norm_policy == "Adaptive Bootstrapping":
            result = run_adaptive_experiment(
                input_data=input_data,
                number_of_operations=ops,
                operation_threshold=threshold,
            )
        else:
            raise ValueError(f"Unknown policy: {raw_policy}")

        record = _persist_result(job_id, result)
        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["policy"] = norm_policy
        _jobs[job_id]["result"] = record

    except Exception as exc:
        error_str = str(exc)
        print(f"[Job {job_id}] ERROR: {error_str}")
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"]  = error_str


def _run_all_job(job_id: str, request: RunAllRequest) -> None:
    """Execute all three strategy experiments in a background thread."""
    _jobs[job_id]["status"] = "running"
    _jobs[job_id]["started_at"] = time.perf_counter()

    try:
        raw_input = request.input_values or request.input_data
        if not raw_input:
            raise ValueError("Input vector cannot be empty.")
        input_data = list(raw_input)
        threshold = request.adaptive_threshold if request.adaptive_threshold is not None else request.threshold

        results_dict = run_all_experiments(
            input_data=input_data,
            number_of_operations=request.operations,
            fixed_interval=request.fixed_interval,
            adaptive_threshold=threshold,
        )

        # Generate one experiment_id per strategy
        enriched = []
        for key in ("no_bootstrap", "fixed_bootstrap", "adaptive_bootstrap"):
            r = results_dict[key]
            sub_id = str(uuid.uuid4())
            record = _persist_result(sub_id, r)
            enriched.append(record)

        _jobs[job_id]["status"]  = "done"
        _jobs[job_id]["results"] = enriched

    except Exception as exc:
        error_str = str(exc)
        print(f"[Job {job_id}] ERROR: {error_str}")
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"]  = error_str


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message"   : "Noise-Aware Adaptive FHE API v2.0",
        "endpoints" : [
            "/api/summary",
            "/api/experiments",
            "/api/experiments/{id}",
            "/api/experiments/run",
            "/api/experiments/run-all",
            "/api/experiments/status/{job_id}",
            "/api/experiments/graph-data",
            "/docs",
        ],
    }


# ============================================================
# SUMMARY
# ============================================================

@app.get("/api/summary")
def get_summary():
    """
    Aggregate statistics from experiment history.

    Returns zero-value fields (not an error) when no history exists.
    """
    history = _read_history_jsonl()

    total        = len(history)
    completed    = sum(1 for r in history if r.get("status") == "success")
    failed       = sum(1 for r in history if r.get("status") == "failed")
    running_jobs = sum(1 for j in _jobs.values() if j.get("status") == "running")

    total_bootstraps = sum(
        int(r.get("bootstrap_count", 0) or 0) for r in history
    )

    times = [
        float(r["total_execution_time"])
        for r in history
        if r.get("total_execution_time") is not None
    ]
    avg_time = sum(times) / len(times) if times else 0.0

    errors = [
        float(r["maximum_absolute_error"])
        for r in history
        if r.get("maximum_absolute_error") is not None
        and isinstance(r["maximum_absolute_error"], (int, float))
    ]
    max_error = max(errors) if errors else 0.0

    return {
        "total_experiments"   : total,
        "completed_experiments": completed,
        "running_experiments" : running_jobs,
        "failed_experiments"  : failed,
        "avg_execution_time"  : round(avg_time, 4),
        "total_bootstraps"    : total_bootstraps,
        "max_error_recorded"  : max_error,
    }


# ============================================================
# HISTORY
# ============================================================

@app.get("/api/experiments")
def get_experiments(limit: int = 100, offset: int = 0):
    """
    Return paginated experiment history (most recent first).
    Does NOT include per-operation logs to keep response size small.
    """
    history = _read_history_jsonl()
    history.reverse()   # most-recent first

    # Strip heavy operation_data from list view
    lightweight = []
    for r in history[offset : offset + limit]:
        entry = {k: v for k, v in r.items() if k != "operation_data"}
        lightweight.append(entry)

    return {
        "total"   : len(history),
        "offset"  : offset,
        "limit"   : limit,
        "results" : lightweight,
    }


@app.get("/api/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    """Return a single experiment record with full operation_data."""
    history = _read_history_jsonl()
    for record in history:
        if record.get("experiment_id") == experiment_id:
            return {"result": record}
    raise HTTPException(status_code=404, detail="Experiment not found.")


# ============================================================
# RUN SINGLE EXPERIMENT
# ============================================================

@app.post("/api/experiments/run")
def run_single_experiment(request: RunRequest):
    """
    Start a single-strategy experiment asynchronously.

    Returns immediately with a job_id.
    Poll /api/experiments/status/{job_id} for progress.
    """
    # Validate before submitting
    check = validate_input(list(request.input_data), request.operations)
    if not check["ok"]:
        raise HTTPException(status_code=422, detail=check["error"])

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status"    : "queued",
        "policy"    : request.policy,
        "submitted" : time.strftime("%Y-%m-%dT%H:%M:%S"),
        "result"    : None,
        "error"     : None,
    }

    _executor.submit(_run_single_job, job_id, request)

    return {
        "success"     : True,
        "job_id"      : job_id,
        "message"     : f"Experiment queued. Poll /api/experiments/status/{job_id}",
    }


# ============================================================
# RUN ALL THREE EXPERIMENTS
# ============================================================

@app.post("/api/experiments/run-all")
def run_all_endpoint(request: RunAllRequest):
    """
    Start all three strategy experiments asynchronously.

    Returns immediately with a job_id.
    Poll /api/experiments/status/{job_id} for progress.
    When done, the job result contains a 'results' list with all three.
    """
    # Validate input before submitting
    check = validate_input(list(request.input_data), request.operations)
    if not check["ok"]:
        raise HTTPException(status_code=422, detail=check["error"])

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status"    : "queued",
        "policy"    : "run-all",
        "submitted" : time.strftime("%Y-%m-%dT%H:%M:%S"),
        "results"   : None,
        "error"     : None,
    }

    _executor.submit(_run_all_job, job_id, request)

    return {
        "success" : True,
        "job_id"  : job_id,
        "message" : f"All-three experiment queued. Poll /api/experiments/status/{job_id}",
    }


# ============================================================
# JOB STATUS
# ============================================================

@app.get("/api/experiments/status/{job_id}")
def get_job_status(job_id: str):
    """
    Poll the status of a running or completed experiment job.

    Response
    --------
    status : 'queued' | 'running' | 'done' | 'failed'
    result : ExperimentResult (when status == 'done' and single strategy)
    results: list[ExperimentResult] (when status == 'done' and run-all)
    error  : str (when status == 'failed')
    """
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found.")

    job = _jobs[job_id]
    response = {
        "job_id"    : job_id,
        "status"    : job["status"],
        "policy"    : job.get("policy"),
        "submitted" : job.get("submitted"),
    }

    if job["status"] == "done":
        if "results" in job and job["results"] is not None:
            response["success"] = True
            response["results"] = job["results"]
        elif "result" in job and job["result"] is not None:
            response["success"] = True
            response["result"]  = job["result"]

    elif job["status"] == "failed":
        response["success"] = False
        response["error"]   = job.get("error", "Unknown error")

    return response


# ============================================================
# GRAPH DATA
# ============================================================

@app.get("/api/experiments/graph-data")
def get_graph_data():
    """
    Return pre-computed graph data from full experiment history.

    Provides:
    - execution_time_by_strategy : for bar chart
    - bootstrap_count_by_strategy
    - error_by_strategy
    - level_over_operations : per-run ciphertext level progression
    """
    history = _read_history_jsonl()
    if not history:
        return {"data": {}, "message": "No experiment history found."}

    # Group by strategy
    by_strategy: Dict[str, List] = {}
    for r in history:
        strat = r.get("strategy", "Unknown")
        by_strategy.setdefault(strat, []).append(r)

    def _avg(lst, key):
        vals = [
            float(x[key])
            for x in lst
            if x.get(key) is not None and isinstance(x[key], (int, float))
        ]
        return sum(vals) / len(vals) if vals else 0.0

    strategies = ["No Bootstrap", "Fixed Bootstrap", "Adaptive Bootstrap"]

    exec_time_chart = [
        {
            "strategy": s,
            "avg_time": round(_avg(by_strategy.get(s, []), "total_execution_time"), 4),
            "count"   : len(by_strategy.get(s, [])),
        }
        for s in strategies
    ]

    bootstrap_chart = [
        {
            "strategy"  : s,
            "avg_count" : round(_avg(by_strategy.get(s, []), "bootstrap_count"), 2),
        }
        for s in strategies
    ]

    error_chart = [
        {
            "strategy" : s,
            "avg_error": _avg(by_strategy.get(s, []), "maximum_absolute_error"),
        }
        for s in strategies
    ]

    # Recent operation-level data (last run per strategy)
    level_progressions = {}
    seen = set()
    for r in reversed(history):
        strat = r.get("strategy")
        if strat and strat not in seen and r.get("operation_data"):
            level_progressions[strat] = r["operation_data"]
            seen.add(strat)

    return {
        "data": {
            "execution_time_by_strategy" : exec_time_chart,
            "bootstrap_count_by_strategy": bootstrap_chart,
            "error_by_strategy"          : error_chart,
            "level_progressions"         : level_progressions,
            "total_runs"                 : len(history),
        }
    }


# ============================================================
# VALIDATE ONLY (no experiment run)
# ============================================================

@app.post("/api/validate")
def validate_only(request: RunRequest):
    """
    Check whether the input is safe to run without executing an experiment.
    """
    check = validate_input(list(request.input_data), request.operations)
    return {
        "valid"          : check["ok"],
        "error"          : check["error"],
        "max_abs_input"  : check["max_abs"],
        "expected_max"   : check.get("expected_max"),
        "safe_limit"     : check["safe_limit"],
    }


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("Starting Noise-Aware Adaptive FHE API v2.0 at http://0.0.0.0:8000 ...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)