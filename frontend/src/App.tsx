/**
 * App.tsx
 * =======
 * Noise-Aware Adaptive Bootstrapping for CKKS FHE
 * Research Dashboard
 *
 * Uses the async job API (POST /api/experiments/run-all → job_id → poll status).
 * All displayed values come from real backend data.
 * No hardcoded or fabricated numbers.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import "./index.css";

/* =========================================================
   CONSTANTS
========================================================= */

const API_BASE   = "http://127.0.0.1:8000";
const POLL_MS    = 2000;   // poll interval while job is running
const REFRESH_MS = 10000;  // auto-refresh dashboard data

/* =========================================================
   TYPES
========================================================= */

type Page =
  | "dashboard"
  | "new-experiment"
  | "history"
  | "details"
  | "compare";

type Strategy =
  | "No Bootstrap"
  | "Fixed Bootstrap"
  | "Adaptive Bootstrap";

type JobStatus = "queued" | "running" | "done" | "failed";

interface OperationData {
  operation            : number;
  operation_type?      : string;
  ciphertext_level     : number;
  level_before?        : number;
  level_after?         : number;
  remaining_levels?    : number;
  indicator_value?     : number;
  indicator_name?      : string;
  configured_threshold?: number;
  condition?           : string;
  decision             : string;
  bootstrap_triggered? : boolean;
  bootstrap_time       : number;
}

interface ExperimentResult {
  experiment_id?          : string;
  timestamp?              : string;
  strategy                : Strategy | string;
  input_data              : number[];
  operations              : number;
  fixed_interval?         : number | null;
  adaptive_threshold?     : number | null;
  controller_type?        : string;
  controller_description? : string;
  expected_values         : number[];
  decrypted_values        : number[];
  maximum_absolute_error  : number | null;
  final_ciphertext_level  : number | null;
  bootstrap_count         : number;
  total_bootstrap_time    : number;
  total_execution_time    : number;
  encrypt_time?           : number;
  compute_time?           : number;
  decrypt_time?           : number;
  operation_data          : OperationData[];
  status                  : string;
  error_message?          : string | null;
}

interface Summary {
  total_experiments?    : number;
  completed_experiments?: number;
  running_experiments?  : number;
  failed_experiments?   : number;
  avg_execution_time?   : number;
  total_bootstraps?     : number;
  max_error_recorded?   : number;
}

interface HistoryResponse {
  total   : number;
  offset  : number;
  limit   : number;
  results : ExperimentResult[];
}

/* =========================================================
   API HELPERS
========================================================= */

async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${path} → ${response.status}: ${text}`);
  }
  return response.json() as Promise<T>;
}

/** Submit a run-all job; returns the job_id immediately */
async function submitRunAllJob(
  inputData    : number[],
  operations   : number,
  fixedInterval: number,
  threshold    : number
): Promise<string> {
  const data = await apiFetch<{ success: boolean; job_id: string; message?: string }>(
    "/api/experiments/run-all",
    {
      method : "POST",
      body   : JSON.stringify({
        input_data    : inputData,
        operations    : operations,
        fixed_interval: fixedInterval,
        threshold     : threshold,
      }),
    }
  );
  if (!data.success || !data.job_id) {
    throw new Error("Backend did not return a job_id.");
  }
  return data.job_id;
}

/** Poll job status. Returns status and results when done. */
async function pollJob(jobId: string): Promise<{
  status : JobStatus;
  results?: ExperimentResult[];
  error? : string;
}> {
  const data = await apiFetch<{
    status   : JobStatus;
    results? : ExperimentResult[];
    result?  : ExperimentResult;
    error?   : string;
  }>(`/api/experiments/status/${jobId}`);

  return {
    status : data.status,
    results: data.results ?? (data.result ? [data.result] : undefined),
    error  : data.error,
  };
}

async function fetchSummary(): Promise<Summary> {
  return apiFetch<Summary>("/api/summary");
}

async function fetchHistory(
  limit: number = 50,
  offset: number = 0
): Promise<HistoryResponse> {
  return apiFetch<HistoryResponse>(
    `/api/experiments?limit=${limit}&offset=${offset}`
  );
}

/* =========================================================
   FORMATTERS
========================================================= */

function formatTime(v?: number | null): string {
  if (v == null || !Number.isFinite(v)) return "—";
  return `${v.toFixed(3)} s`;
}

function formatError(v?: number | null): string {
  if (v == null || !Number.isFinite(v)) return "—";
  return v.toExponential(3);
}

function formatDate(iso?: string): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function parseInputVector(raw: string): number[] {
  return raw
    .split(",")
    .map((s) => Number(s.trim()))
    .filter((n) => Number.isFinite(n));
}

function strategyClass(s: string): string {
  if (s.includes("Adaptive")) return "adaptive";
  if (s.includes("Fixed"))    return "fixed";
  return "none";
}

function strategyShort(s: string): string {
  if (s.includes("Adaptive")) return "Adaptive";
  if (s.includes("Fixed"))    return "Fixed";
  return "No Bootstrap";
}

/* =========================================================
   REUSABLE COMPONENTS
========================================================= */

function StatCard({
  title,
  value,
  subtitle,
}: {
  title   : string;
  value   : string | number;
  subtitle?: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-title">{title}</div>
      <div className="stat-value">{value}</div>
      {subtitle && <div className="stat-subtitle">{subtitle}</div>}
    </div>
  );
}

function StatusBadge({
  children,
  type = "success",
}: {
  children : React.ReactNode;
  type?    : "success" | "warning" | "danger" | "info";
}) {
  return (
    <span className={`status-badge ${type}`}>● {children}</span>
  );
}

function EmptyState({
  icon = "◎",
  title,
  message,
  action,
}: {
  icon?   : string;
  title   : string;
  message : string;
  action? : React.ReactNode;
}) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <h2>{title}</h2>
      <p>{message}</p>
      {action}
    </div>
  );
}

/* =========================================================
   SVG CIPHERTEXT LEVEL GRAPH
========================================================= */

function CiphertextGraph({
  experiment,
}: {
  experiment: ExperimentResult | null;
}) {
  if (
    !experiment ||
    !experiment.operation_data ||
    experiment.operation_data.length === 0
  ) {
    return (
      <div className="empty-graph">No operation data available.</div>
    );
  }

  const data = experiment.operation_data;
  const W = 760, H = 300;
  const pL = 55, pR = 30, pT = 24, pB = 50;
  const gW = W - pL - pR;
  const gH = H - pT - pB;

  const maxLevel = Math.max(...data.map((d) => d.ciphertext_level), 1);
  const maxOp    = Math.max(...data.map((d) => d.operation), 1);

  const pts = data.map((d) => ({
    ...d,
    x : pL + ((d.operation - 1) / Math.max(maxOp - 1, 1)) * gW,
    y : pT + gH - (d.ciphertext_level / maxLevel) * gH,
  }));

  const poly = pts.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <div className="graph-wrapper">
      <svg viewBox={`0 0 ${W} ${H}`} className="graph">
        {/* Grid lines */}
        {Array.from({ length: maxLevel + 1 }).map((_, i) => {
          const y = pT + gH - (i / maxLevel) * gH;
          return (
            <g key={`g${i}`}>
              <line x1={pL} y1={y} x2={W - pR} y2={y} className="grid-line" />
              <text x={pL - 8} y={y + 4} textAnchor="end" className="axis-text">
                {i}
              </text>
            </g>
          );
        })}

        {/* Axes */}
        <line x1={pL} y1={H - pB} x2={W - pR} y2={H - pB} className="axis-line" />
        <line x1={pL} y1={pT}     x2={pL}      y2={H - pB} className="axis-line" />

        {/* X labels */}
        {pts.map((p) => (
          <text key={`xl${p.operation}`} x={p.x} y={H - 25} textAnchor="middle" className="axis-text">
            {p.operation}
          </text>
        ))}

        {/* Line */}
        <polyline points={poly} className="graph-line" fill="none" />

        {/* Points */}
        {pts.map((p) => {
          const isBS = p.decision === "BOOTSTRAP";
          return (
            <g key={`pt${p.operation}`}>
              {isBS && <circle cx={p.x} cy={p.y} r="10" className="bootstrap-ring" />}
              <circle
                cx={p.x}
                cy={p.y}
                r="5"
                className={isBS ? "bootstrap-point" : "normal-point"}
              />
              {isBS && (
                <text x={p.x} y={p.y - 14} textAnchor="middle" className="bootstrap-label">
                  BOOT
                </text>
              )}
            </g>
          );
        })}

        {/* Axis titles */}
        <text x={W / 2} y={H - 6} textAnchor="middle" className="axis-title">
          Operation
        </text>
        <text
          x="14"
          y={H / 2}
          textAnchor="middle"
          transform={`rotate(-90 14 ${H / 2})`}
          className="axis-title"
        >
          Level
        </text>
      </svg>

      <div className="graph-legend">
        <span><span className="legend-dot normal" /> Continue</span>
        <span><span className="legend-dot bootstrap" /> Bootstrap</span>
      </div>
    </div>
  );
}

/* =========================================================
   COMPARISON BAR GRAPH
========================================================= */

function ComparisonBarGraph({
  results,
  metric,
  title,
}: {
  results: ExperimentResult[];
  metric : "time" | "bootstrap" | "error";
  title  : string;
}) {
  if (!results.length) {
    return (
      <div className="empty-graph">
        No comparison data — run experiments first.
      </div>
    );
  }

  const getValue = (r: ExperimentResult) => {
    if (metric === "time")      return r.total_execution_time ?? 0;
    if (metric === "bootstrap") return r.bootstrap_count ?? 0;
    return r.maximum_absolute_error ?? 0;
  };

  const values   = results.map(getValue);
  const maxVal   = Math.max(...values, 1e-20);

  const fmt = (v: number) => {
    if (metric === "error") return formatError(v);
    if (metric === "time")  return formatTime(v);
    return String(v);
  };

  return (
    <div>
      <div className="panel-kicker">{title}</div>
      <div className="bar-chart">
        {results.map((r, i) => {
          const v   = values[i];
          let pct   = (v / maxVal) * 100;
          if (v > 0 && pct < 5) pct = 5;
          return (
            <div className="bar-column" key={r.strategy}>
              <div className="bar-value">{fmt(v)}</div>
              <div className="bar-container">
                <div
                  className={`bar ${strategyClass(r.strategy)}`}
                  style={{ height: `${Math.min(pct, 100)}%` }}
                />
              </div>
              <div className="bar-label">{strategyShort(r.strategy)}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* =========================================================
   DASHBOARD PAGE
========================================================= */

function DashboardPage({
  summary,
  history,
  latestExperiment,
  compareResults,
  backendOnline,
  onNewExperiment,
  onDetails,
  onCompare,
  onHistory,
}: {
  summary          : Summary | null;
  history          : ExperimentResult[];
  latestExperiment : ExperimentResult | null;
  compareResults   : ExperimentResult[];
  backendOnline    : boolean;
  onNewExperiment  : () => void;
  onDetails        : () => void;
  onCompare        : () => void;
  onHistory        : () => void;
}) {
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="eyebrow">RESEARCH CONTROL CENTER</div>
          <h1>
            Noise-Aware Adaptive<br />Bootstrapping
          </h1>
          <p>
            Execute, monitor and compare CKKS homomorphic computations.
          </p>
        </div>
        <div>
          <StatusBadge type={backendOnline ? "success" : "danger"}>
            {backendOnline ? "Backend Connected" : "Backend Offline"}
          </StatusBadge>
        </div>
      </div>

      <div className="dashboard-actions">
        <button className="primary-button" onClick={onNewExperiment}>
          + New Experiment
        </button>
        <button className="secondary-button" onClick={onCompare}>
          Compare Strategies
        </button>
        <button className="secondary-button" onClick={onHistory}>
          Experiment History
        </button>
      </div>

      {/* Summary cards — from real backend data */}
      <div className="stats-grid">
        <StatCard
          title="Total Experiments"
          value={summary?.total_experiments ?? 0}
          subtitle="All runs recorded"
        />
        <StatCard
          title="Completed"
          value={summary?.completed_experiments ?? 0}
          subtitle="Successful runs"
        />
        <StatCard
          title="Running"
          value={summary?.running_experiments ?? 0}
          subtitle="In progress"
        />
        <StatCard
          title="Failed"
          value={summary?.failed_experiments ?? 0}
          subtitle="Errors recorded"
        />
        <StatCard
          title="Avg. Execution Time"
          value={formatTime(summary?.avg_execution_time)}
          subtitle="Per experiment"
        />
        <StatCard
          title="Total Bootstraps"
          value={summary?.total_bootstraps ?? 0}
          subtitle="Across all runs"
        />
        <StatCard
          title="Max Absolute Error"
          value={formatError(summary?.max_error_recorded)}
          subtitle="Highest recorded"
        />
      </div>

      {/* Latest experiment summary */}
      {latestExperiment ? (
        <div className="panel latest-panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">LATEST EXPERIMENT</div>
              <h2>
                {latestExperiment.strategy}
              </h2>
            </div>
            <StatusBadge
              type={
                latestExperiment.status === "success" ? "success" :
                latestExperiment.status === "failed"  ? "danger"  : "info"
              }
            >
              {latestExperiment.status}
            </StatusBadge>
          </div>

          <div className="latest-grid">
            <div>
              <span>Timestamp</span>
              <strong>{formatDate(latestExperiment.timestamp)}</strong>
            </div>
            <div>
              <span>Operations</span>
              <strong>{latestExperiment.operations}</strong>
            </div>
            <div>
              <span>Runtime</span>
              <strong>{formatTime(latestExperiment.total_execution_time)}</strong>
            </div>
            <div>
              <span>Bootstraps</span>
              <strong>{latestExperiment.bootstrap_count}</strong>
            </div>
            <div>
              <span>Max Error</span>
              <strong>{formatError(latestExperiment.maximum_absolute_error)}</strong>
            </div>
            <div>
              <span>Input Size</span>
              <strong>{latestExperiment.input_data?.length ?? "—"}</strong>
            </div>
          </div>

          <button className="link-button" onClick={onDetails}>
            View Full Details →
          </button>
        </div>
      ) : (
        <EmptyState
          title="No experiments yet"
          message="Run your first CKKS experiment to see real measurements and graphs."
          action={
            <button className="primary-button" onClick={onNewExperiment}>
              Run First Experiment
            </button>
          }
        />
      )}

      {/* Recent history table */}
      {history.length > 0 && (
        <div className="panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">RECENT RUNS</div>
              <h2>Experiment History</h2>
            </div>
            <button className="link-button" onClick={onHistory}>
              View All →
            </button>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Strategy</th>
                  <th>Operations</th>
                  <th>Bootstraps</th>
                  <th>Exec Time</th>
                  <th>Max Error</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {history.slice(0, 8).map((r, i) => (
                  <tr key={r.experiment_id ?? i}>
                    <td>{formatDate(r.timestamp)}</td>
                    <td>
                      <span className={`strategy-tag ${strategyClass(r.strategy)}`}>
                        {strategyShort(r.strategy)}
                      </span>
                    </td>
                    <td>{r.operations}</td>
                    <td>{r.bootstrap_count}</td>
                    <td>{formatTime(r.total_execution_time)}</td>
                    <td>{formatError(r.maximum_absolute_error)}</td>
                    <td>
                      <span className={`status-tag ${r.status === "success" ? "ok" : "err"}`}>
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Comparison graphs from compare results */}
      {compareResults.length >= 2 && (
        <div className="panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">COMPARISON CHARTS</div>
              <h2>Strategy Comparison</h2>
            </div>
          </div>
          <div className="charts-row">
            <ComparisonBarGraph results={compareResults} metric="time"      title="Execution Time" />
            <ComparisonBarGraph results={compareResults} metric="bootstrap" title="Bootstrap Count" />
            <ComparisonBarGraph results={compareResults} metric="error"     title="Max Absolute Error" />
          </div>
        </div>
      )}
    </div>
  );
}

/* =========================================================
   NEW EXPERIMENT PAGE
========================================================= */

/**
 * Supported CKKS configuration:
 *   RingDim        : 4096
 *   ScalingModSize : 59 bits
 *   MultiplicativeDepth : 32
 *   NumSlots       : 2048
 *
 * Safe input range (with N squarings):
 *   max(|x|)^(2^N)  <  4.5e15
 *
 * Examples:
 *   [0.1..0.9] × N≤32 : always safe
 *   [1..9]     × N≤24 : (9^(2^24) overflows — validate before running)
 *   [10..99]   × N≤12 : (99^(2^12) > safe limit — must normalize)
 */

const CKKS_SAFE_LIMIT = 4.5e15;

function computeSafeOps(maxAbs: number): number {
  if (maxAbs === 0) return 32;
  let n = 0;
  let v = maxAbs;
  while (v < CKKS_SAFE_LIMIT && n < 32) {
    v = v ** 2;
    n++;
    if (!Number.isFinite(v)) break;
  }
  return Math.max(n - 1, 0);
}

function NewExperimentPage({
  onComplete,
}: {
  onComplete: (results: ExperimentResult[]) => void;
}) {
  const [inputText,    setInputText]    = useState("0.1, 0.2, 0.3, 0.4");
  const [operations,   setOperations]   = useState(4);
  const [strategy,     setStrategy]     = useState<Strategy>("Adaptive Bootstrap");
  const [threshold,    setThreshold]    = useState(2);
  const [fixedAfter,   setFixedAfter]   = useState(2);

  const [jobId,        setJobId]        = useState<string | null>(null);
  const [jobStatus,    setJobStatus]    = useState<JobStatus | null>(null);
  const [running,      setRunning]      = useState(false);
  const [error,        setError]        = useState("");
  const [runAllMode,   setRunAllMode]   = useState(true);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const inputData = useMemo(
    () => parseInputVector(inputText),
    [inputText]
  );

  const maxAbs = useMemo(
    () => (inputData.length > 0 ? Math.max(...inputData.map(Math.abs)) : 0),
    [inputData]
  );

  const safeOps = useMemo(
    () => computeSafeOps(maxAbs),
    [maxAbs]
  );

  const expectedMax = useMemo(() => {
    if (maxAbs === 0) return 0;
    try {
      const v = maxAbs ** (2 ** operations);
      return Number.isFinite(v) ? v : Infinity;
    } catch {
      return Infinity;
    }
  }, [maxAbs, operations]);

  const inputWarning = useMemo(() => {
    if (inputData.length === 0) return "No valid values parsed.";
    if (!Number.isFinite(expectedMax) || expectedMax > CKKS_SAFE_LIMIT) {
      return (
        `⚠ max(|x|)=${maxAbs.toExponential(2)}, ` +
        `max(|x|)^(2^${operations}) = ${
          Number.isFinite(expectedMax)
            ? expectedMax.toExponential(2)
            : "overflow"
        } exceeds CKKS safe limit ${CKKS_SAFE_LIMIT.toExponential(2)}. ` +
        `Safe operations for this input: ≤${safeOps}.`
      );
    }
    return "";
  }, [inputData.length, expectedMax, maxAbs, operations, safeOps]);

  /* Stop polling */
  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  /* Start polling a job */
  const startPolling = useCallback(
    (id: string) => {
      stopPolling();
      pollRef.current = setInterval(async () => {
        try {
          const status = await pollJob(id);
          setJobStatus(status.status);

          if (status.status === "done") {
            stopPolling();
            setRunning(false);
            if (status.results && status.results.length > 0) {
              onComplete(status.results);
            } else {
              setError("Experiment finished but no results were returned.");
            }
          } else if (status.status === "failed") {
            stopPolling();
            setRunning(false);
            setError(status.error ?? "Experiment failed on the backend.");
          }
        } catch (e: any) {
          stopPolling();
          setRunning(false);
          setError(`Polling error: ${e.message}`);
        }
      }, POLL_MS);
    },
    [stopPolling, onComplete]
  );

  /* Validate and submit */
  const handleRun = useCallback(async () => {
    setError("");
    setJobId(null);
    setJobStatus(null);

    if (inputData.length === 0) {
      setError("Please enter at least one valid numeric value.");
      return;
    }
    if (operations < 1 || operations > 32) {
      setError("Operations must be between 1 and 32.");
      return;
    }
    if (!Number.isFinite(expectedMax) || expectedMax > CKKS_SAFE_LIMIT) {
      setError(
        `Input values too large for ${operations} operations. ` +
        `Safe max operations for these values: ${safeOps}. ` +
        `Reduce input magnitudes or decrease operation count.`
      );
      return;
    }
    if (strategy === "Fixed Bootstrap") {
      if (fixedAfter < 1 || fixedAfter > operations) {
        setError(
          `Fixed interval must be between 1 and ${operations}.`
        );
        return;
      }
    }
    if (strategy === "Adaptive Bootstrap") {
      if (threshold < 1) {
        setError("Adaptive threshold must be at least 1.");
        return;
      }
    }

    try {
      setRunning(true);
      setJobStatus("queued");

      const id = await submitRunAllJob(
        inputData,
        operations,
        fixedAfter,
        threshold
      );

      setJobId(id);
      setJobStatus("running");
      startPolling(id);
    } catch (e: any) {
      setRunning(false);
      setJobStatus(null);
      setError(e.message ?? "Failed to submit experiment.");
    }
  }, [
    inputData,
    operations,
    fixedAfter,
    threshold,
    strategy,
    expectedMax,
    safeOps,
    startPolling,
  ]);

  useEffect(() => () => stopPolling(), [stopPolling]);

  const jobStatusText = () => {
    if (!jobStatus) return null;
    if (jobStatus === "queued")  return "Job queued — waiting to start…";
    if (jobStatus === "running") return "OpenFHE experiment is running. This may take 10–60 seconds for bootstrapping strategies…";
    if (jobStatus === "done")    return "Experiment completed!";
    if (jobStatus === "failed")  return "Experiment failed.";
    return null;
  };

  return (
    <div className="page narrow-page">
      <div className="page-header compact">
        <div>
          <div className="eyebrow">EXPERIMENT CONFIGURATION</div>
          <h1>New Experiment</h1>
          <p>Configure and execute a real OpenFHE CKKS computation.</p>
        </div>
      </div>

      <div className="panel form-panel">
        {/* CKKS configuration info */}
        <div className="config-info-box">
          <strong>CKKS Configuration:</strong>
          &nbsp;RingDim=4096 | ScalingModSize=59 | MultiplicativeDepth=32 |
          Slots=2048 | SecurityLevel=NotSet (research mode)
          <br />
          <strong>Safe range:</strong> max(|x|)^(2^N) &lt; 4.5×10¹⁵
        </div>

        {/* Input vector */}
        <div className="form-section">
          <label>Input Vector (comma-separated numbers)</label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="0.1, 0.2, 0.3, 0.4"
            rows={3}
          />
          <div className="field-help">
            Supports positive, negative, and decimal values.
            Parsed values: <strong>{inputData.length}</strong>
            {inputData.length > 0 && (
              <> | max(|x|) = <strong>{maxAbs.toExponential(3)}</strong>
              </>
            )}
          </div>
        </div>

        {/* Operation count */}
        <div className="form-row">
          <div className="form-section">
            <label>Operation Count (squarings)</label>
            <input
              type="number"
              min={1}
              max={32}
              value={operations}
              onChange={(e) => setOperations(Number(e.target.value))}
            />
            <div className="field-help">
              {inputData.length > 0
                ? `Safe max for this input: ≤${safeOps} operations`
                : "How many times to square the ciphertext"}
            </div>
          </div>

          {/* Fixed interval (only when Fixed Bootstrap selected) */}
          {strategy === "Fixed Bootstrap" && (
            <div className="form-section">
              <label>Fixed Bootstrap Interval</label>
              <input
                type="number"
                min={1}
                max={operations}
                value={fixedAfter}
                onChange={(e) => setFixedAfter(Number(e.target.value))}
              />
              <div className="field-help">
                Bootstrap after every N operations (never after final op).
                Example: interval=2, ops=7 → bootstraps at ops 2, 4, 6.
              </div>
            </div>
          )}

          {/* Adaptive threshold (only when Adaptive selected) */}
          {strategy === "Adaptive Bootstrap" && (
            <div className="form-section">
              <label>Level Threshold (adaptive)</label>
              <input
                type="number"
                min={1}
                max={30}
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
              />
              <div className="field-help">
                Bootstrap when remaining ciphertext levels ≤ threshold.
                Controller type: level-aware (not direct noise measurement).
              </div>
            </div>
          )}
        </div>

        {/* Strategy selector */}
        <div className="form-section">
          <label>Bootstrapping Policy</label>
          <div className="strategy-grid">
            {(["No Bootstrap", "Fixed Bootstrap", "Adaptive Bootstrap"] as Strategy[]).map((s) => (
              <button
                key={s}
                type="button"
                className={`strategy-card ${strategy === s ? "selected" : ""}`}
                onClick={() => setStrategy(s)}
              >
                <span className="radio">{strategy === s ? "●" : "○"}</span>
                <strong>{s}</strong>
                <small>
                  {s === "No Bootstrap"
                    ? "Baseline — no level refresh."
                    : s === "Fixed Bootstrap"
                    ? "Bootstrap every N operations (never after last)."
                    : "Level-aware: bootstrap when remaining levels ≤ threshold."}
                </small>
              </button>
            ))}
          </div>
        </div>

        {/* Expected result preview */}
        {inputData.length > 0 && (
          <div className="form-section">
            <label>Workload Preview</label>
            <div className="field-help">
              After {operations} squarings, x → x^(2^{operations}).
              Expected max output: <strong>
                {Number.isFinite(expectedMax)
                  ? expectedMax.toExponential(4)
                  : "overflow (exceeds safe range)"}
              </strong>
            </div>
          </div>
        )}

        {/* Input warning */}
        {inputWarning && (
          <div className="warning-box">{inputWarning}</div>
        )}

        {/* Error */}
        {error && <div className="error-box">{error}</div>}

        {/* Job status */}
        {jobStatusText() && (
          <div className={`status-box ${jobStatus === "failed" ? "error" : "info"}`}>
            {jobStatusText()}
            {jobId && <div className="job-id">Job ID: {jobId}</div>}
          </div>
        )}

        {/* Submit */}
        <div className="run-area">
          <div className="mode-toggle">
            <label>
              <input
                type="checkbox"
                checked={runAllMode}
                onChange={(e) => setRunAllMode(e.target.checked)}
              />
              &nbsp;Run all three strategies for comparison
            </label>
          </div>

          <button
            className="primary-button large"
            onClick={handleRun}
            disabled={running || !!inputWarning}
          >
            {running ? "Running…" : "RUN EXPERIMENT"}
          </button>

          {running && (
            <p className="running-text">
              OpenFHE experiment submitted. Polling every {POLL_MS / 1000}s…
              Bootstrap strategies may take 10–60 seconds per experiment.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   HISTORY PAGE
========================================================= */

function HistoryPage({
  history,
  onSelectExperiment,
}: {
  history            : ExperimentResult[];
  onSelectExperiment : (exp: ExperimentResult) => void;
}) {
  if (history.length === 0) {
    return (
      <div className="page">
        <EmptyState
          title="No experiment history"
          message="Run experiments to build a history of results."
        />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header compact">
        <div>
          <div className="eyebrow">EXPERIMENT HISTORY</div>
          <h1>All Experiments</h1>
          <p>{history.length} run(s) recorded.</p>
        </div>
      </div>

      <div className="panel">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Timestamp</th>
                <th>Strategy</th>
                <th>Input</th>
                <th>Operations</th>
                <th>Bootstraps</th>
                <th>Exec Time</th>
                <th>Max Error</th>
                <th>Status</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {history.map((r, i) => (
                <tr key={r.experiment_id ?? i}>
                  <td>{history.length - i}</td>
                  <td>{formatDate(r.timestamp)}</td>
                  <td>
                    <span className={`strategy-tag ${strategyClass(r.strategy)}`}>
                      {strategyShort(r.strategy)}
                    </span>
                  </td>
                  <td>
                    <span title={(r.input_data ?? []).join(", ")}>
                      [{(r.input_data ?? []).slice(0, 3).join(", ")}
                      {(r.input_data ?? []).length > 3 ? ", …" : ""}]
                    </span>
                  </td>
                  <td>{r.operations}</td>
                  <td>{r.bootstrap_count}</td>
                  <td>{formatTime(r.total_execution_time)}</td>
                  <td>{formatError(r.maximum_absolute_error)}</td>
                  <td>
                    <span className={`status-tag ${r.status === "success" ? "ok" : "err"}`}>
                      {r.status}
                    </span>
                  </td>
                  <td>
                    <button
                      className="link-button small"
                      onClick={() => onSelectExperiment(r)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   DETAILS PAGE
========================================================= */

function DetailsPage({
  experiment,
  onBack,
}: {
  experiment : ExperimentResult | null;
  onBack     : () => void;
}) {
  if (!experiment) {
    return (
      <div className="page">
        <EmptyState
          title="No experiment selected"
          message="Select an experiment from the history page."
          action={<button className="primary-button" onClick={onBack}>Go Back</button>}
        />
      </div>
    );
  }

  const isFailed = experiment.status === "failed";

  return (
    <div className="page">
      <div className="page-header compact">
        <div>
          <div className="eyebrow">EXPERIMENT DETAILS</div>
          <h1>{experiment.strategy}</h1>
          <p>
            {experiment.timestamp && `Recorded: ${formatDate(experiment.timestamp)}`}
            {experiment.experiment_id && ` | ID: ${experiment.experiment_id.slice(0, 8)}…`}
          </p>
        </div>
        <StatusBadge type={isFailed ? "danger" : "success"}>
          {experiment.status}
        </StatusBadge>
      </div>

      {isFailed && experiment.error_message && (
        <div className="error-box">
          <strong>Failure reason:</strong> {experiment.error_message}
        </div>
      )}

      {/* Metrics */}
      <div className="detail-top-grid">
        <StatCard title="Policy"           value={strategyShort(experiment.strategy)} />
        <StatCard title="Operations"       value={experiment.operations} />
        <StatCard title="Execution Time"   value={formatTime(experiment.total_execution_time)} />
        <StatCard title="Bootstrap Count"  value={experiment.bootstrap_count} />
        <StatCard title="Max Error"        value={formatError(experiment.maximum_absolute_error)} />
        <StatCard title="Final Level"      value={experiment.final_ciphertext_level ?? "—"} />
        {experiment.encrypt_time != null && (
          <StatCard title="Encrypt Time"   value={formatTime(experiment.encrypt_time)} />
        )}
        {experiment.compute_time != null && (
          <StatCard title="Compute Time"   value={formatTime(experiment.compute_time)} />
        )}
        {experiment.decrypt_time != null && (
          <StatCard title="Decrypt Time"   value={formatTime(experiment.decrypt_time)} />
        )}
      </div>

      {/* Controller info */}
      <div className="panel">
        <div className="panel-heading">
          <div>
            <div className="panel-kicker">CKKS CONFIGURATION</div>
            <h2>Experiment Parameters</h2>
          </div>
        </div>
        <div className="config-table">
          <div><span>Strategy</span><span>{experiment.strategy}</span></div>
          <div><span>Controller Type</span><span>{experiment.controller_type ?? "—"}</span></div>
          {experiment.controller_description && (
            <div><span>Controller Note</span><span>{experiment.controller_description}</span></div>
          )}
          {experiment.fixed_interval != null && (
            <div><span>Fixed Interval</span><span>{experiment.fixed_interval}</span></div>
          )}
          {experiment.adaptive_threshold != null && (
            <div><span>Adaptive Threshold</span><span>{experiment.adaptive_threshold}</span></div>
          )}
          <div>
            <span>Input Vector</span>
            <span>{(experiment.input_data ?? []).join(", ")}</span>
          </div>
          <div><span>Input Count</span><span>{(experiment.input_data ?? []).length}</span></div>
          <div><span>Ring Dimension</span><span>4096</span></div>
          <div><span>Scaling Mod Size</span><span>59 bits</span></div>
          <div><span>Multiplicative Depth</span><span>32</span></div>
          <div><span>NumSlots</span><span>2048</span></div>
        </div>
      </div>

      {/* Ciphertext level graph */}
      {experiment.operation_data && experiment.operation_data.length > 0 && (
        <div className="panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">CIPHERTEXT CONDITION</div>
              <h2>Level vs Operation</h2>
            </div>
          </div>
          <CiphertextGraph experiment={experiment} />
        </div>
      )}

      {/* Operation trace table */}
      {experiment.operation_data && experiment.operation_data.length > 0 && (
        <div className="panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">DECISION LOG</div>
              <h2>Per-Operation Trace</h2>
            </div>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Op #</th>
                  <th>Type</th>
                  <th>Level Before</th>
                  <th>Level After</th>
                  {experiment.operation_data[0]?.remaining_levels != null && (
                    <th>Remaining</th>
                  )}
                  {experiment.operation_data[0]?.condition != null && (
                    <th>Condition</th>
                  )}
                  {experiment.operation_data[0]?.configured_threshold != null && (
                    <th>Threshold</th>
                  )}
                  <th>Decision</th>
                  <th>Bootstrap Time</th>
                </tr>
              </thead>
              <tbody>
                {experiment.operation_data.map((row) => (
                  <tr key={row.operation}>
                    <td>{row.operation}</td>
                    <td>{row.operation_type ?? "EvalMult"}</td>
                    <td>{row.level_before ?? row.ciphertext_level}</td>
                    <td>{row.level_after  ?? row.ciphertext_level}</td>
                    {row.remaining_levels != null && (
                      <td>{row.remaining_levels}</td>
                    )}
                    {row.condition != null && (
                      <td>
                        <span className={`cond-badge ${row.condition === "HIGH-RISK" ? "highrisk" : "safe"}`}>
                          {row.condition}
                        </span>
                      </td>
                    )}
                    {row.configured_threshold != null && (
                      <td>{row.configured_threshold}</td>
                    )}
                    <td>
                      <span className={`decision-badge ${row.decision === "BOOTSTRAP" ? "boot" : "cont"}`}>
                        {row.decision}
                      </span>
                    </td>
                    <td>
                      {row.bootstrap_time > 0
                        ? formatTime(row.bootstrap_time)
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Numerical results */}
      {experiment.expected_values &&
        experiment.expected_values.length > 0 && (
        <div className="panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">NUMERICAL ACCURACY</div>
              <h2>Expected vs Decrypted Values</h2>
            </div>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Index</th>
                  <th>Input</th>
                  <th>Expected (x^(2^N))</th>
                  <th>Decrypted</th>
                  <th>Absolute Error</th>
                </tr>
              </thead>
              <tbody>
                {experiment.expected_values.map((exp, idx) => {
                  const dec = (experiment.decrypted_values ?? [])[idx];
                  const err = dec != null ? Math.abs(exp - dec) : null;
                  return (
                    <tr key={idx}>
                      <td>{idx + 1}</td>
                      <td>{(experiment.input_data ?? [])[idx]?.toExponential(4) ?? "—"}</td>
                      <td>{Number.isFinite(exp) ? exp.toExponential(6) : "overflow"}</td>
                      <td>{dec != null ? dec.toExponential(6) : "—"}</td>
                      <td>{err != null ? err.toExponential(4) : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

/* =========================================================
   COMPARISON PAGE
========================================================= */

function ComparisonPage({
  onComplete,
}: {
  onComplete: (results: ExperimentResult[]) => void;
}) {
  const [inputText,  setInputText]  = useState("0.1, 0.2, 0.3, 0.4");
  const [operations, setOperations] = useState(4);
  const [threshold,  setThreshold]  = useState(2);
  const [fixedAfter, setFixedAfter] = useState(2);

  const [results,    setResults]    = useState<ExperimentResult[]>([]);
  const [running,    setRunning]    = useState(false);
  const [jobId,      setJobId]      = useState<string | null>(null);
  const [jobStatus,  setJobStatus]  = useState<JobStatus | null>(null);
  const [error,      setError]      = useState("");

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const inputData = useMemo(
    () => parseInputVector(inputText),
    [inputText]
  );

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPolling = useCallback(
    (id: string) => {
      stopPolling();
      pollRef.current = setInterval(async () => {
        try {
          const s = await pollJob(id);
          setJobStatus(s.status);
          if (s.status === "done") {
            stopPolling();
            setRunning(false);
            if (s.results) {
              setResults(s.results);
              onComplete(s.results);
            }
          } else if (s.status === "failed") {
            stopPolling();
            setRunning(false);
            setError(s.error ?? "Comparison failed.");
          }
        } catch (e: any) {
          stopPolling();
          setRunning(false);
          setError(e.message);
        }
      }, POLL_MS);
    },
    [stopPolling, onComplete]
  );

  const handleRun = async () => {
    setError("");
    setResults([]);
    if (inputData.length === 0) {
      setError("Enter at least one valid number.");
      return;
    }
    try {
      setRunning(true);
      setJobStatus("queued");
      const id = await submitRunAllJob(inputData, operations, fixedAfter, threshold);
      setJobId(id);
      setJobStatus("running");
      startPolling(id);
    } catch (e: any) {
      setRunning(false);
      setJobStatus(null);
      setError(e.message ?? "Failed to start comparison.");
    }
  };

  useEffect(() => () => stopPolling(), [stopPolling]);

  return (
    <div className="page">
      <div className="page-header compact">
        <div>
          <div className="eyebrow">STRATEGY COMPARISON</div>
          <h1>Compare All Three</h1>
          <p>Run all three strategies on identical input and workload.</p>
        </div>
      </div>

      <div className="panel form-panel">
        <div className="form-section">
          <label>Input Vector</label>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="0.1, 0.2, 0.3, 0.4"
            rows={3}
          />
          <div className="field-help">
            All three strategies receive the same input.
          </div>
        </div>

        <div className="form-row">
          <div className="form-section">
            <label>Operations</label>
            <input type="number" min={1} max={32} value={operations}
              onChange={(e) => setOperations(Number(e.target.value))} />
          </div>
          <div className="form-section">
            <label>Fixed Interval</label>
            <input type="number" min={1} max={operations} value={fixedAfter}
              onChange={(e) => setFixedAfter(Number(e.target.value))} />
            <div className="field-help">For fixed bootstrap strategy</div>
          </div>
          <div className="form-section">
            <label>Adaptive Threshold</label>
            <input type="number" min={1} max={30} value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))} />
            <div className="field-help">For adaptive strategy</div>
          </div>
        </div>

        {error && <div className="error-box">{error}</div>}

        {jobStatus && (
          <div className="status-box info">
            {jobStatus === "queued"  && "Queued…"}
            {jobStatus === "running" && "Running all three strategies. This can take 30–120 seconds…"}
            {jobStatus === "done"    && "All experiments completed!"}
            {jobId && <div className="job-id">Job: {jobId.slice(0, 8)}…</div>}
          </div>
        )}

        <div className="run-area">
          <button
            className="primary-button large"
            onClick={handleRun}
            disabled={running}
          >
            {running ? "Running All Three…" : "RUN COMPARISON"}
          </button>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <>
          <div className="panel">
            <div className="panel-heading">
              <div>
                <div className="panel-kicker">RESULTS</div>
                <h2>Strategy Comparison</h2>
              </div>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Strategy</th>
                    <th>Operations</th>
                    <th>Bootstraps</th>
                    <th>Bootstrap Time</th>
                    <th>Total Time</th>
                    <th>Max Error</th>
                    <th>Final Level</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r) => (
                    <tr key={r.strategy}>
                      <td>
                        <span className={`strategy-tag ${strategyClass(r.strategy)}`}>
                          {strategyShort(r.strategy)}
                        </span>
                      </td>
                      <td>{r.operations}</td>
                      <td>{r.bootstrap_count}</td>
                      <td>{formatTime(r.total_bootstrap_time)}</td>
                      <td><strong>{formatTime(r.total_execution_time)}</strong></td>
                      <td>{formatError(r.maximum_absolute_error)}</td>
                      <td>{r.final_ciphertext_level ?? "—"}</td>
                      <td>
                        <span className={`status-tag ${r.status === "success" ? "ok" : "err"}`}>
                          {r.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel">
            <div className="panel-heading">
              <div>
                <div className="panel-kicker">CHARTS</div>
                <h2>Visual Comparison</h2>
              </div>
            </div>
            <div className="charts-row">
              <ComparisonBarGraph results={results} metric="time"      title="Execution Time" />
              <ComparisonBarGraph results={results} metric="bootstrap" title="Bootstrap Count" />
              <ComparisonBarGraph results={results} metric="error"     title="Max Absolute Error" />
            </div>
          </div>

          {/* Per-strategy level graphs */}
          {results.map((r) => (
            r.operation_data && r.operation_data.length > 0 && (
              <div className="panel" key={r.strategy}>
                <div className="panel-heading">
                  <div>
                    <div className="panel-kicker">{strategyShort(r.strategy).toUpperCase()}</div>
                    <h2>Ciphertext Level — {r.strategy}</h2>
                  </div>
                </div>
                <CiphertextGraph experiment={r} />
              </div>
            )
          ))}
        </>
      )}
    </div>
  );
}

/* =========================================================
   APP ROOT
========================================================= */

export default function App() {
  const [page,             setPage]            = useState<Page>("dashboard");
  const [backendOnline,    setBackendOnline]    = useState(false);
  const [summary,          setSummary]          = useState<Summary | null>(null);
  const [history,          setHistory]          = useState<ExperimentResult[]>([]);
  const [latestExperiment, setLatestExperiment] = useState<ExperimentResult | null>(null);
  const [compareResults,   setCompareResults]   = useState<ExperimentResult[]>([]);
  const [selectedExp,      setSelectedExp]      = useState<ExperimentResult | null>(null);

  const refreshData = useCallback(async () => {
    try {
      const [sum, hist] = await Promise.all([
        fetchSummary(),
        fetchHistory(50, 0),
      ]);
      setSummary(sum);
      setHistory(hist.results);
      if (hist.results.length > 0) {
        setLatestExperiment(hist.results[0]);
      }
      setBackendOnline(true);
    } catch {
      setBackendOnline(false);
    }
  }, []);

  /* Initial load + periodic refresh */
  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, REFRESH_MS);
    return () => clearInterval(interval);
  }, [refreshData]);

  /* When an experiment run completes */
  const handleExperimentComplete = useCallback(
    (results: ExperimentResult[]) => {
      if (results.length > 0) {
        setLatestExperiment(results[0]);
      }
      refreshData();
      setPage("details");
    },
    [refreshData]
  );

  /* When a comparison run completes */
  const handleCompareComplete = useCallback(
    (results: ExperimentResult[]) => {
      setCompareResults(results);
      refreshData();
    },
    [refreshData]
  );

  const navigation = [
    { id: "dashboard"      as Page, label: "Dashboard",        icon: "⊞" },
    { id: "new-experiment" as Page, label: "New Experiment",   icon: "+" },
    { id: "history"        as Page, label: "History",          icon: "☰" },
    { id: "compare"        as Page, label: "Compare",          icon: "⇌" },
  ];

  return (
    <div className="app-shell">
      {/* ============ SIDEBAR ============ */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">◈</div>
          <div className="brand-text">
            <strong>FHE Research</strong>
            <span>WORKSPACE</span>
          </div>
        </div>

        <nav>
          {navigation.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${page === item.id ? "active" : ""}`}
              onClick={() => setPage(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="backend-status">
            <span className={`connection-dot ${backendOnline ? "online" : "offline"}`} />
            <div>
              <strong>{backendOnline ? "Backend Online" : "Backend Offline"}</strong>
              <span>{API_BASE}</span>
            </div>
          </div>
          <div className="project-info">
            <span>OpenFHE + CKKS</span>
            <span>Research Dashboard</span>
          </div>
        </div>
      </aside>

      {/* ============ MAIN CONTENT ============ */}
      <main className="main">
        {page === "dashboard" && (
          <DashboardPage
            summary={summary}
            history={history}
            latestExperiment={latestExperiment}
            compareResults={compareResults}
            backendOnline={backendOnline}
            onNewExperiment={() => setPage("new-experiment")}
            onDetails={() => setPage("details")}
            onCompare={() => setPage("compare")}
            onHistory={() => setPage("history")}
          />
        )}

        {page === "new-experiment" && (
          <NewExperimentPage onComplete={handleExperimentComplete} />
        )}

        {page === "history" && (
          <HistoryPage
            history={history}
            onSelectExperiment={(exp) => {
              setSelectedExp(exp);
              setPage("details");
            }}
          />
        )}

        {page === "details" && (
          <DetailsPage
            experiment={selectedExp ?? latestExperiment}
            onBack={() => setPage("history")}
          />
        )}

        {page === "compare" && (
          <ComparisonPage onComplete={handleCompareComplete} />
        )}
      </main>
    </div>
  );
}