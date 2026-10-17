import React, { useEffect, useState, useRef } from "react";
import { createRoot } from "react-dom/client";
import {
  ShieldCheck,
  Layers3,
  Database,
  GitBranch,
  ScanLine,
  SlidersHorizontal,
  Package,
  Settings,
  Plus,
  ArrowUpRight,
  ArrowRight,
  Upload,
  Check,
  ChevronRight,
  LogOut,
  LockKeyhole,
  AlertTriangle,
  FileSpreadsheet,
  RefreshCw,
  X,
  HelpCircle,
  Clock,
  Trash2,
  Download,
  Network,
} from "lucide-react";
import "./style.css";

type O = Record<string, any>;
let csrf = "";
async function api(path: string, method = "GET", body?: any) {
  const r = await fetch("/api" + path, {
    method,
    credentials: "same-origin",
    headers: {
      ...(body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      "X-CSRF-Token": csrf,
    },
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
  });
  const data = await r
    .json()
    .catch(() => ({ detail: "The service returned an unexpected response." }));
  if (!r.ok) throw new Error(data.detail || "Request failed.");
  return data;
}
const icons = [
  Layers3,
  Database,
  GitBranch,
  ScanLine,
  SlidersHorizontal,
  Package,
  Settings,
];
const pages = [
  "Overview",
  "Datasets",
  "Release scenarios",
  "Audits & findings",
  "Repair comparison",
  "Release history",
  "Settings",
];
const steps = [
  "Import",
  "Describe",
  "Map",
  "Audit",
  "Repair",
  "Review & export",
];
function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={"badge " + tone}>{children}</span>;
}
function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      {React.isValidElement(children)
        ? React.cloneElement(
            children as React.ReactElement<Record<string, unknown>>,
            { "aria-label": label },
          )
        : children}
      {hint && <small>{hint}</small>}
    </label>
  );
}
function Empty({
  title,
  children,
}: {
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <Layers3 size={30} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
function App() {
  const [ready, setReady] = useState(false),
    [auth, setAuth] = useState(false),
    [setup, setSetup] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false),
    [ws, setWs] = useState<O[]>([]),
    [wid, setWid] = useState(localStorage.getItem("mosaic-workspace") || ""),
    [state, setState] = useState<O | null>(null),
    [page, setPage] = useState(0),
    [health, setHealth] = useState<O>({});
  const [newName, setNewName] = useState(""),
    [creating, setCreating] = useState(false),
    [assistant, setAssistant] = useState(""),
    [showAssistant, setShowAssistant] = useState(false);
  const [username, setUsername] = useState(""),
    [password, setPassword] = useState("");
  const path = (p: string) => "/w/" + wid + p;
  async function refresh() {
    const list = await api("/workspaces");
    setWs(list);
    if (wid && list.some((w: O) => w.id === wid && !w.deleting))
      setState(await api(path("/state")));
    else if (wid) {
      setWid("");
      setState(null);
      localStorage.removeItem("mosaic-workspace");
    }
  }
  async function act(fn: () => Promise<any>, message = "") {
    setError("");
    setNotice("");
    setBusy(true);
    try {
      const result = await fn();
      if (message) setNotice(message);
      await refresh();
      return result;
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    (async () => {
      try {
        const h = await api("/health");
        setHealth(h);
        const status = await api("/auth/status");
        setSetup(status.setup_required);
        try {
          const me = await api("/auth/me");
          csrf = me.csrf;
          setAuth(true);
        } catch {}
      } finally {
        setReady(true);
      }
    })();
  }, []);
  useEffect(() => {
    if (auth) refresh().catch((e) => setError(e.message));
  }, [auth, wid]);
  useEffect(() => {
    if (!auth || !wid) return;
    const timer = setInterval(() => {
      refresh().catch(() => {});
      api("/health")
        .then(setHealth)
        .catch(() => {});
    }, 2500);
    return () => clearInterval(timer);
  }, [auth, wid]);
  function choose(id: string) {
    setWid(id);
    localStorage.setItem("mosaic-workspace", id);
    setPage(0);
    setState(null);
  }
  async function create(name: string) {
    const w = await api("/workspaces", "POST", { name });
    choose(w.id);
    setCreating(false);
    setNewName("");
    setWs(await api("/workspaces"));
    return w;
  }
  async function example() {
    setBusy(true);
    setError("");
    try {
      const w = await create("Training feedback · fictional example");
      const kit = await api("/examples");
      for (const file of kit) {
        const f = new FormData();
        f.append("file", new File([file.csv], file.name, { type: "text/csv" }));
        const u = await api("/w/" + w.id + "/uploads", "POST", f);
        const parse = {
          encoding: "utf-8-sig",
          delimiter: ",",
          quotechar: '"',
          header: true,
          null_tokens: [],
          skip_bad_rows: false,
        };
        const preview = await api(
          "/w/" + w.id + "/uploads/" + u.id + "/preview",
          "POST",
          parse,
        );
        const columns = preview.columns.map((c: O) => ({
          id: c.id,
          name: c.name,
          type: file.types[c.name] || "text",
          date_format: file.types[c.name] === "date" ? "%Y-%m-%d" : null,
          meaning: "",
          identifier: c.name === "participant_key",
          sensitive: c.name === "rating",
        }));
        const job = await api(
          "/w/" + w.id + "/uploads/" + u.id + "/confirm",
          "POST",
          { parse, columns, role: file.role, row_unit: "person" },
        );
        for (let n = 0; n < 120; n++) {
          const j = await api("/w/" + w.id + "/jobs/" + job.job);
          if (j.state === "complete") break;
          if (j.state === "failed") throw new Error(j.error);
          await new Promise((r) => setTimeout(r, 250));
        }
      }
      setNotice(
        "Five fictional CSVs imported through the normal import service. Review their roles and confirm mappings in a release scenario.",
      );
      setPage(2);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!ready)
    return (
      <div className="auth-screen">
        <ShieldCheck />
        <p>Connecting to your private workspace…</p>
      </div>
    );
  if (!auth)
    return (
      <div className="auth-screen">
        <div className="auth-brand">
          <span className="logo">
            <Layers3 />
          </span>
          MosaicGuard
        </div>
        <div className="auth-card">
          <Badge tone="teal">PRIVATE BY DESIGN</Badge>
          <h1>
            {setup ? "Your data. A clearer release decision." : "Welcome back."}
          </h1>
          <p>
            {setup
              ? "Create the owner account for this self-hosted installation. Your source data stays in your deployment."
              : "Sign in to continue your dataset release review."}
          </p>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setError("");
              setBusy(true);
              try {
                const r = await api(
                  "/auth/" + (setup ? "setup" : "login"),
                  "POST",
                  { username, password },
                );
                csrf = r.csrf;
                setAuth(true);
                setPassword("");
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <Field label="Username">
              <input
                autoComplete="username"
                required
                minLength={3}
                maxLength={64}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </Field>
            <Field
              label="Password"
              hint={
                setup ? "At least 12 characters. Store it securely." : undefined
              }
            >
              <input
                type="password"
                autoComplete={setup ? "new-password" : "current-password"}
                required
                minLength={12}
                maxLength={256}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <button className="primary wide" disabled={busy}>
              {setup ? "Create owner account" : "Sign in"}
              <ArrowRight size={17} />
            </button>
          </form>
          <div className="auth-footer">
            <LockKeyhole size={14} /> Encrypted storage · No telemetry · Local
            processing
          </div>
        </div>
        <small>Scoped evidence for responsible data sharing.</small>
      </div>
    );
  const datasets = state?.datasets || [],
    scenarios = state?.scenarios || [],
    audits = state?.audits || [],
    branches = state?.branches || [];
  const currentScenario = scenarios
    .filter((s: O) => !branches.some((b: O) => b.scenario === s.id))
    .at(-1);
  const latest = audits.at(-1);
  const stage = datasets.length
    ? currentScenario
      ? audits.length
        ? branches.length
          ? 5
          : 4
        : 3
      : 2
    : 0;
  return (
    <div className="shell">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setPage(0);
          }}
        >
          <span className="logo">
            <Layers3 size={21} />
          </span>
          MosaicGuard
        </a>
        <div className="sidebar-label">YOUR WORKSPACE</div>
        <select
          aria-label="Current workspace"
          className="workspace-select"
          value={wid}
          onChange={(e) => choose(e.target.value)}
        >
          <option value="">Choose a workspace</option>
          {ws
            .filter((w) => !w.deleting)
            .map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
        </select>
        <button className="new-workspace" onClick={() => setCreating(true)}>
          <Plus size={15} />
          New workspace
        </button>
        <nav aria-label="Main navigation">
          {pages.map((name, i) => {
            const Icon = icons[i];
            return (
              <button
                key={name}
                aria-label={name}
                className={page === i ? "active" : ""}
                onClick={() => setPage(i)}
              >
                <Icon size={18} />
                {name}
                {i === 3 && audits.length > 0 && (
                  <span className="nav-count">{audits.length}</span>
                )}
              </button>
            );
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="private-note">
            <LockKeyhole size={17} />
            <div>
              <strong>Private installation</strong>
              <small>Your data stays here</small>
            </div>
          </div>
          <button
            onClick={() =>
              act(async () => {
                await api("/auth/logout", "POST", {});
                setAuth(false);
                setState(null);
              })
            }
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div>
            Workspaces <ChevronRight size={14} />
            <strong>{state?.workspace.name || "Your workspaces"}</strong>
          </div>
          <div className="top-right">
            <span
              className={
                "status-dot " +
                (health.graph === "ready" ? "online" : "offline")
              }
            />
            <span>
              {health.graph === "ready"
                ? "FalkorDB connected"
                : "Graph unavailable"}
            </span>
            <button
              className="icon-btn"
              aria-label="Open review assistant"
              onClick={() => setShowAssistant(!showAssistant)}
            >
              <HelpCircle size={19} />
            </button>
            <span className="avatar">O</span>
          </div>
        </header>
        <main>
          {creating && (
            <section className="panel inline-form">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  act(() => create(newName));
                }}
              >
                <Field label="Workspace name">
                  <input
                    autoFocus
                    required
                    maxLength={120}
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="e.g. Programme evaluation"
                  />
                </Field>
                <button className="primary" disabled={busy}>
                  Create workspace
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => setCreating(false)}
                >
                  Cancel
                </button>
              </form>
            </section>
          )}
          {error && (
            <div className="message error" role="alert">
              <AlertTriangle size={18} />
              <span>{error}</span>
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <div className="message success" role="status">
              <Check size={18} />
              <span>{notice}</span>
              <button aria-label="Dismiss notice" onClick={() => setNotice("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {health.graph !== "ready" && (
            <div className="message warning">
              <AlertTriangle size={18} />
              FalkorDB is unavailable. Start the graph service with Docker
              Compose to run audits and graph mutations.
            </div>
          )}
          {!wid ? (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">RELEASE WITH CONTEXT</div>
                  <h1>A clearer view of what your data could reveal.</h1>
                  <p>
                    Inspect linkage exposure, compare practical changes, and
                    prepare an evidence-based release.
                  </p>
                </div>
              </div>
              <div className="welcome-grid">
                <section className="panel welcome-card">
                  <div className="large-icon">
                    <Upload />
                  </div>
                  <h2>Use my CSVs</h2>
                  <p>
                    Create a private workspace for the data you’re preparing to
                    share. You decide what information is in scope.
                  </p>
                  <button className="primary" onClick={() => setCreating(true)}>
                    Create a workspace
                    <ArrowRight size={17} />
                  </button>
                </section>
                <section className="panel welcome-card">
                  <div className="large-icon violet">
                    <Network />
                  </div>
                  <h2>Explore a synthetic example</h2>
                  <p>
                    Follow five fictional training datasets through real
                    imports, confirmed mappings, and release review.
                  </p>
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={example}
                  >
                    Explore example
                    <ArrowUpRight size={17} />
                  </button>
                </section>
              </div>
              {ws.length > 0 && (
                <section className="panel">
                  <h2>Your workspaces</h2>
                  {ws
                    .filter((w) => !w.deleting)
                    .map((w) => (
                      <button
                        className="workspace-row"
                        key={w.id}
                        onClick={() => choose(w.id)}
                      >
                        <Layers3 size={19} />
                        <strong>{w.name}</strong>
                        <ArrowRight size={17} />
                      </button>
                    ))}
                </section>
              )}
            </>
          ) : !state ? (
            <div className="empty">Loading workspace…</div>
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">PRIVATE DATA REVIEW</div>
                  <h1>
                    {page === 0
                      ? "A thoughtful release starts here."
                      : pages[page]}
                  </h1>
                  <p>
                    {
                      [
                        "Understand what sharing could reveal, and make the trade-offs visible.",
                        "Immutable source versions. Reviewed meaning. Clear provenance.",
                        "Define who can see what, and which relationships are meaningful.",
                        "Evidence under your assumptions, with coverage in view.",
                        "Test changes against the same release model and analytical goals.",
                        "Review an inspected artifact, then record releases deliberately.",
                        "Manage data custody, assistant privacy, and workspace lifecycle.",
                      ][page]
                    }
                  </p>
                </div>
                {page === 0 && (
                  <button className="primary" onClick={() => setPage(1)}>
                    <Plus size={17} />
                    Import a CSV
                  </button>
                )}
              </div>
              <div className="workflow" aria-label="Release review progress">
                {steps.map((step, i) => (
                  <button
                    key={step}
                    className={
                      i < stage ? "done" : i === stage ? "current" : ""
                    }
                    onClick={() => setPage([1, 1, 2, 3, 4, 5][i])}
                  >
                    <span>{i < stage ? <Check size={13} /> : i + 1}</span>
                    {step}
                    {i < 5 && <ChevronRight className="step-arrow" size={14} />}
                  </button>
                ))}
              </div>
              {page === 0 && (
                <>
                  <section className="hero-panel">
                    <div>
                      <Badge tone="teal">YOUR NEXT STEP</Badge>
                      <h2>
                        {!datasets.length
                          ? "Bring your release into focus."
                          : !currentScenario
                            ? "Give your data a release context."
                            : !audits.length
                              ? "Your scenario is ready for a closer look."
                              : "Turn evidence into a release decision."}
                      </h2>
                      <p>
                        {!datasets.length
                          ? "Import the candidate you intend to share and any authorised reference information. Originals stay immutable."
                          : !currentScenario
                            ? "Choose the audience, confirm meaningful joins, and name the statistics you need to preserve."
                            : "Review candidate matches and incomplete coverage, then compare changes without overwriting your source."}
                      </p>
                      <button
                        className="primary"
                        onClick={() =>
                          setPage(
                            !datasets.length ? 1 : !currentScenario ? 2 : 3,
                          )
                        }
                      >
                        {!datasets.length
                          ? "Import your first CSV"
                          : !currentScenario
                            ? "Define a scenario"
                            : "Review the audit"}
                        <ArrowRight size={17} />
                      </button>
                    </div>
                    <div className="hero-visual" aria-hidden="true">
                      <span className="visual-node one">
                        <FileSpreadsheet size={25} />
                      </span>
                      <span className="visual-node two">
                        <Database size={23} />
                      </span>
                      <span className="visual-node center">
                        <ShieldCheck size={38} />
                      </span>
                      <span className="visual-node three">
                        <GitBranch size={24} />
                      </span>
                      <span className="visual-label">
                        Context → Evidence → Decision
                      </span>
                    </div>
                  </section>
                  <div className="stats-grid">
                    <Stat
                      label="Dataset versions"
                      value={datasets.length}
                      sub={`${datasets.reduce((a: number, d: O) => a + d.rows, 0).toLocaleString()} imported records`}
                      icon={<Database size={20} />}
                    />
                    <Stat
                      label="Scenario snapshots"
                      value={scenarios.length}
                      sub="Explicit audience & assumptions"
                      icon={<GitBranch size={20} />}
                    />
                    <Stat
                      label="Completed audits"
                      value={audits.length}
                      sub={latest ? latest.status : "Ready when you are"}
                      icon={<ScanLine size={20} />}
                    />
                    <Stat
                      label="Tested repair branches"
                      value={branches.length}
                      sub="Measured risk & utility separately"
                      icon={<SlidersHorizontal size={20} />}
                    />
                  </div>
                  <div className="two-col">
                    <section className="panel">
                      <div className="section-heading">
                        <h2>Datasets in this workspace</h2>
                        <button className="text-btn" onClick={() => setPage(1)}>
                          View all
                          <ArrowUpRight size={14} />
                        </button>
                      </div>
                      {!datasets.length ? (
                        <Empty title="A fresh starting point">
                          Your imported CSVs will appear here.
                        </Empty>
                      ) : (
                        datasets.slice(-5).map((d: O) => (
                          <div className="dataset-row" key={d.id}>
                            <span className="file-icon">
                              <FileSpreadsheet size={19} />
                            </span>
                            <div>
                              <strong>{d.name}</strong>
                              <small>
                                {d.rows.toLocaleString()} records ·{" "}
                                {d.columns.length} columns
                              </small>
                            </div>
                            <Badge>{d.role}</Badge>
                          </div>
                        ))
                      )}
                    </section>
                    <section className="panel principle">
                      <span className="small-icon">
                        <ShieldCheck size={22} />
                      </span>
                      <h2>Evidence, with its boundaries.</h2>
                      <p>
                        A unique candidate is a reason to inspect the
                        assumptions. It is not proof that a person has been
                        identified.
                      </p>
                      <ul>
                        <li>Only confirmed mappings influence findings</li>
                        <li>Missing coverage stays visible</li>
                        <li>Risk and analytical utility stay separate</li>
                      </ul>
                      <button
                        className="text-btn"
                        onClick={() => {
                          setShowAssistant(true);
                          api(path("/assistant"), "POST", {
                            task: "scope",
                            external: false,
                          })
                            .then((r) => setAssistant(r.answer))
                            .catch((e) => setError(e.message));
                        }}
                      >
                        Understand the review model
                        <ArrowRight size={15} />
                      </button>
                    </section>
                  </div>
                </>
              )}
              {page === 1 && (
                <Datasets state={state} path={path} act={act} busy={busy} />
              )}
              {page === 2 && (
                <Scenarios
                  key={wid}
                  state={state}
                  path={path}
                  act={act}
                  busy={busy}
                  go={() => setPage(3)}
                />
              )}
              {page === 3 && (
                <Audits
                  state={state}
                  path={path}
                  act={act}
                  busy={busy}
                  graphReady={health.graph === "ready"}
                  goRepair={() => setPage(4)}
                />
              )}
              {page === 4 && (
                <Repairs
                  state={state}
                  path={path}
                  act={act}
                  busy={busy}
                  graphReady={health.graph === "ready"}
                  goExport={() => setPage(5)}
                />
              )}
              {page === 5 && (
                <Releases state={state} path={path} act={act} busy={busy} />
              )}
              {page === 6 && (
                <SettingsView
                  state={state}
                  path={path}
                  act={act}
                  busy={busy}
                  afterDelete={() => {
                    choose("");
                    setState(null);
                  }}
                />
              )}
              {state.jobs.some((j: O) =>
                [
                  "queued",
                  "running",
                  "interrupted",
                  "failed",
                  "cancelled",
                ].includes(j.state),
              ) && (
                <section className="panel jobs-panel">
                  <div className="section-heading">
                    <h2>Background activity</h2>
                    <Clock size={17} />
                  </div>
                  {state.jobs
                    .filter((j: O) => j.state !== "complete")
                    .slice(0, 6)
                    .map((j: O) => (
                      <div className="job-row" key={j.id}>
                        <div>
                          <strong>{j.kind.replace("_", " ")}</strong>
                          <small>
                            {j.stage}
                            {j.error ? " · " + j.error : ""}
                          </small>
                        </div>
                        <Badge
                          tone={j.state === "failed" ? "amber" : "neutral"}
                        >
                          {j.state}
                        </Badge>
                        {["queued", "running"].includes(j.state) ? (
                          <button
                            className="secondary compact"
                            onClick={() =>
                              act(() =>
                                api(
                                  path("/jobs/" + j.id + "/cancel"),
                                  "POST",
                                  {},
                                ),
                              )
                            }
                          >
                            Cancel
                          </button>
                        ) : (
                          <button
                            className="secondary compact"
                            onClick={() =>
                              act(() =>
                                api(
                                  path("/jobs/" + j.id + "/retry"),
                                  "POST",
                                  {},
                                ),
                              )
                            }
                          >
                            Retry
                          </button>
                        )}
                      </div>
                    ))}
                </section>
              )}
            </>
          )}
          <footer>
            <span>
              <LockKeyhole size={13} />
              Processed in your deployment
            </span>
            <span>MosaicGuard · Scoped evidence, considered decisions</span>
          </footer>
        </main>
      </div>
      {showAssistant && (
        <aside className="assistant-panel">
          <div className="section-heading">
            <h2>Review assistant</h2>
            <button
              className="icon-btn"
              aria-label="Close assistant"
              onClick={() => setShowAssistant(false)}
            >
              <X size={19} />
            </button>
          </div>
          <Badge tone="teal">BUILT-IN RULES-BASED GUIDANCE</Badge>
          <p>Get help with the review workflow. This guidance runs locally.</p>
          {(["next_step", "scope", "repairs"] as const).map((t) => (
            <button
              key={t}
              className="assistant-question"
              disabled={!wid || busy}
              onClick={() =>
                act(async () => {
                  const r = await api(path("/assistant"), "POST", {
                    task: t,
                    external: false,
                  });
                  setAssistant(r.answer);
                })
              }
            >
              {t === "next_step"
                ? "What should I do next?"
                : t === "scope"
                  ? "What do these findings mean?"
                  : "How should I compare repairs?"}
              <ArrowRight size={15} />
            </button>
          ))}
          {assistant && <div className="assistant-answer">{assistant}</div>}
          <small>
            External-model mode is optional. Review payloads and enable it in
            Settings.
          </small>
        </aside>
      )}
    </div>
  );
}
function Stat({
  label,
  value,
  sub,
  icon,
}: {
  label: string;
  value: number;
  sub: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="panel stat">
      <div>
        <span>{label}</span>
        {icon}
      </div>
      <strong>{value}</strong>
      <small>{sub}</small>
    </div>
  );
}

const initialParse = {
  encoding: "utf-8-sig",
  delimiter: ",",
  quotechar: '"',
  header: true,
  null_tokens: [] as string[],
  skip_bad_rows: false,
};
function Datasets({
  state,
  path,
  act,
  busy,
}: {
  state: O;
  path: (p: string) => string;
  act: any;
  busy: boolean;
}) {
  const [upload, setUpload] = useState<O | null>(null),
    [parse, setParse] = useState<O>(initialParse),
    [preview, setPreview] = useState<O | null>(null),
    [columns, setColumns] = useState<O[]>([]),
    [role, setRole] = useState("candidate"),
    [unit, setUnit] = useState("unknown"),
    [nulls, setNulls] = useState(""),
    [selected, setSelected] = useState(""),
    [table, setTable] = useState<O | null>(null),
    [offset, setOffset] = useState(0),
    [revealed, setRevealed] = useState(false),
    [filter, setFilter] = useState(""),
    [filterCol, setFilterCol] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  async function loadPreview(id: string, cfg: O) {
    const p = await api(path("/uploads/" + id + "/preview"), "POST", cfg);
    setPreview(p);
    setColumns(
      p.columns.map((c: O) => ({
        id: c.id,
        name: c.name,
        type: c.type,
        date_format: c.type === "date" ? "%Y-%m-%d" : null,
        meaning: c.meaning,
        identifier: c.identifier,
        sensitive: c.sensitive,
      })),
    );
    return p;
  }
  async function send(file: File) {
    await act(async () => {
      const f = new FormData();
      f.append("file", file);
      const u = await api(path("/uploads"), "POST", f);
      setUpload(u);
      setPreview(null);
      setParse({ ...initialParse });
      await loadPreview(u.id, initialParse);
    });
  }
  async function loadTable(did: string, reveal = false, next = 0) {
    const ds = state.datasets.find((d: O) => d.id === did);
    const p = await api(path("/datasets/" + did + "/preview"), "POST", {
      offset: next,
      limit: 20,
      reveal_columns: reveal ? ds.columns.map((c: O) => c.id) : [],
      filter_column: filterCol || null,
      filter_value: filter,
    });
    setTable(p);
    setOffset(next);
    setRevealed(reveal);
    setSelected(did);
  }
  function colChange(i: number, key: string, value: any) {
    setColumns((cs) =>
      cs.map((c, n) => (n === i ? { ...c, [key]: value } : c)),
    );
  }
  return (
    <>
      <section className="panel">
        <div className="section-heading">
          <h2>Import a CSV</h2>
          <Badge>Up to 1,000 records · 2 MB · 50 columns</Badge>
        </div>
        <div
          className="dropzone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files[0]) send(e.dataTransfer.files[0]);
          }}
        >
          <span className="large-icon">
            <Upload size={24} />
          </span>
          <h3>Drop a CSV here to begin</h3>
          <p>
            Original bytes are encrypted and preserved. Parsing and meaning are
            reviewed before import.
          </p>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.tsv,text/csv,text/tab-separated-values"
            aria-label="Choose CSV file"
            onChange={(e) => {
              if (e.target.files?.[0]) send(e.target.files[0]);
              e.target.value = "";
            }}
          />
          <button
            className="secondary"
            disabled={busy}
            onClick={() => fileRef.current?.click()}
          >
            Choose a file
          </button>
        </div>
        {state.uploads.length > 0 && (
          <div className="pending">
            <strong>Pending import reviews</strong>
            {state.uploads.map((u: O) => (
              <div key={u.id}>
                <button
                  className="text-btn"
                  onClick={() => {
                    setUpload(u);
                    setPreview(null);
                    act(() => loadPreview(u.id, parse));
                  }}
                >
                  {u.name}
                  <ArrowRight size={14} />
                </button>
                <button
                  aria-label={"Delete pending " + u.name}
                  className="icon-btn danger"
                  onClick={() =>
                    act(async () => {
                      await api(path("/uploads/" + u.id), "DELETE");
                      if (upload?.id === u.id) {
                        setUpload(null);
                        setPreview(null);
                      }
                    })
                  }
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
      {upload && (
        <section className="panel import-review">
          <div className="section-heading">
            <div>
              <div className="eyebrow">IMPORT REVIEW</div>
              <h2>{upload.name}</h2>
            </div>
            <button
              className="icon-btn"
              aria-label="Close import review"
              onClick={() => {
                setUpload(null);
                setPreview(null);
              }}
            >
              <X size={18} />
            </button>
          </div>
          <div className="form-grid">
            <Field label="Encoding">
              <select
                value={parse.encoding}
                onChange={(e) =>
                  setParse({ ...parse, encoding: e.target.value })
                }
              >
                <option value="utf-8-sig">UTF-8 / BOM</option>
                <option value="cp1252">Windows-1252</option>
                <option value="latin-1">Latin-1</option>
              </select>
            </Field>
            <Field label="Delimiter">
              <select
                value={parse.delimiter}
                onChange={(e) =>
                  setParse({ ...parse, delimiter: e.target.value })
                }
              >
                <option value=",">Comma</option>
                <option value=";">Semicolon</option>
                <option value={"\t"}>Tab</option>
                <option value="|">Pipe</option>
              </select>
            </Field>
            <Field label="Quote character">
              <input
                maxLength={1}
                value={parse.quotechar}
                onChange={(e) =>
                  setParse({ ...parse, quotechar: e.target.value })
                }
              />
            </Field>
            <Field
              label="Null markers"
              hint="Comma-separated; NA stays literal unless listed."
            >
              <input
                value={nulls}
                onChange={(e) => {
                  setNulls(e.target.value);
                  setParse({
                    ...parse,
                    null_tokens: e.target.value
                      ? e.target.value.split(",")
                      : [],
                  });
                }}
                placeholder="Optional, e.g. NULL"
              />
            </Field>
          </div>
          <div className="checks">
            <label>
              <input
                type="checkbox"
                checked={parse.header}
                onChange={(e) =>
                  setParse({ ...parse, header: e.target.checked })
                }
              />
              First record is a header
            </label>
            <label>
              <input
                type="checkbox"
                checked={parse.skip_bad_rows}
                onChange={(e) =>
                  setParse({ ...parse, skip_bad_rows: e.target.checked })
                }
              />
              Explicitly exclude ragged records
            </label>
          </div>
          <div className="actions">
            <button
              className="secondary"
              disabled={busy}
              onClick={() => act(() => loadPreview(upload.id, parse))}
            >
              <RefreshCw size={15} />
              Update parsing preview
            </button>
            {preview && (
              <button
                className="text-btn"
                onClick={() =>
                  act(async () => {
                    const p = await api(
                      path("/uploads/" + upload.id + "/reveal"),
                      "POST",
                      parse,
                    );
                    setPreview({ ...preview, rows: p.rows, masked: false });
                  })
                }
              >
                Reveal local sample values
              </button>
            )}
          </div>
          {preview && (
            <>
              <p className="muted">
                {preview.imported_rows} usable records · {preview.excluded}{" "}
                explicitly excluded · preview of at most 10 logical records
              </p>
              {preview.warnings.map((w: string) => (
                <p className="warning" key={w}>
                  {w}
                </p>
              ))}
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      {preview.columns.map((c: O) => (
                        <th key={c.id}>{c.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.rows.map((r: any[], i: number) => (
                      <tr key={i}>
                        {r.map((v: any, j: number) => (
                          <td key={j}>{v ?? <em>Missing</em>}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <h3>Describe the columns</h3>
              <p className="muted">
                Review type suggestions. Text preserves leading-zero
                identifiers. Dates require an explicit format. Mark identifiers
                and sensitive fields deliberately.
              </p>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Reviewed type</th>
                      <th>Date format</th>
                      <th>Declared meaning</th>
                      <th>Identifier</th>
                      <th>Sensitive</th>
                    </tr>
                  </thead>
                  <tbody>
                    {columns.map((c, i) => (
                      <tr key={c.id}>
                        <td>
                          <strong>{c.name}</strong>
                        </td>
                        <td>
                          <select
                            aria-label={c.name + " type"}
                            value={c.type}
                            onChange={(e) =>
                              colChange(i, "type", e.target.value)
                            }
                          >
                            <option value="text">Text / identifier</option>
                            <option value="number">Numeric</option>
                            <option value="date">Date</option>
                          </select>
                        </td>
                        <td>
                          {c.type === "date" ? (
                            <select
                              aria-label={c.name + " date format"}
                              value={c.date_format || ""}
                              onChange={(e) =>
                                colChange(i, "date_format", e.target.value)
                              }
                            >
                              <option value="">Choose format</option>
                              <option value="%Y-%m-%d">YYYY-MM-DD</option>
                              <option value="%d/%m/%Y">DD/MM/YYYY</option>
                              <option value="%m/%d/%Y">MM/DD/YYYY</option>
                            </select>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td>
                          <input
                            aria-label={c.name + " meaning"}
                            value={c.meaning}
                            maxLength={200}
                            onChange={(e) =>
                              colChange(i, "meaning", e.target.value)
                            }
                            placeholder="What does this describe?"
                          />
                        </td>
                        <td>
                          <input
                            type="checkbox"
                            aria-label={c.name + " identifier"}
                            checked={c.identifier}
                            onChange={(e) =>
                              colChange(i, "identifier", e.target.checked)
                            }
                          />
                        </td>
                        <td>
                          <input
                            type="checkbox"
                            aria-label={c.name + " sensitive"}
                            checked={c.sensitive}
                            onChange={(e) =>
                              colChange(i, "sensitive", e.target.checked)
                            }
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="form-grid">
                <Field
                  label="Dataset role"
                  hint="Internal-only data never enters attacker linkage."
                >
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                  >
                    <option value="candidate">Candidate to share</option>
                    <option value="reference">Authorised reference</option>
                    <option value="available">
                      Other audience-available export
                    </option>
                    <option value="internal">Internal only</option>
                  </select>
                </Field>
                <Field label="One row represents">
                  <select
                    value={unit}
                    onChange={(e) => setUnit(e.target.value)}
                  >
                    {[
                      "unknown",
                      "person",
                      "household",
                      "organisation",
                      "event",
                    ].map((x) => (
                      <option key={x}>{x}</option>
                    ))}
                  </select>
                </Field>
              </div>
              <button
                className="primary"
                disabled={busy}
                onClick={() =>
                  act(async () => {
                    await api(
                      path("/uploads/" + upload.id + "/confirm"),
                      "POST",
                      { parse, columns, role, row_unit: unit },
                    );
                    setUpload(null);
                    setPreview(null);
                  }, "Import queued. The version appears after successful validation.")
                }
              >
                <Check size={16} />
                Confirm and import
              </button>
            </>
          )}
        </section>
      )}
      <section className="panel">
        <div className="section-heading">
          <h2>Dataset versions</h2>
          <span className="muted">{state.datasets.length} versions</span>
        </div>
        {!state.datasets.length ? (
          <Empty title="No dataset versions yet">
            Import and confirm a CSV to create the first immutable version.
          </Empty>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Dataset</th>
                  <th>Role</th>
                  <th>Row unit</th>
                  <th>Records</th>
                  <th>Version</th>
                  <th>Review</th>
                </tr>
              </thead>
              <tbody>
                {state.datasets.map((d: O) => (
                  <tr key={d.id}>
                    <td>
                      <strong>{d.name}</strong>
                      <small>
                        {d.columns.length} columns · {d.excluded} excluded
                      </small>
                    </td>
                    <td>
                      <Badge>{d.role}</Badge>
                    </td>
                    <td>{d.row_unit}</td>
                    <td>{d.rows.toLocaleString()}</td>
                    <td>
                      <code>{d.id.slice(0, 8)}</code>
                      {d.parent && <Badge tone="violet">repair branch</Badge>}
                    </td>
                    <td>
                      <button
                        className="text-btn"
                        onClick={() => act(() => loadTable(d.id))}
                      >
                        Inspect
                        <ArrowRight size={14} />
                      </button>
                      <button
                        aria-label={"Delete dataset " + d.name}
                        className="icon-btn danger"
                        onClick={() =>
                          act(() => api(path("/datasets/" + d.id), "DELETE"))
                        }
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      {table && (
        <section className="panel">
          <div className="section-heading">
            <h2>
              Record review ·{" "}
              {state.datasets.find((d: O) => d.id === selected)?.name}
            </h2>
            <button
              className="text-btn"
              onClick={() => act(() => loadTable(selected, !revealed, offset))}
            >
              {revealed ? "Mask values" : "Deliberately reveal local values"}
            </button>
          </div>
          <div className="actions">
            <select
              aria-label="Filter column"
              value={filterCol}
              onChange={(e) => setFilterCol(e.target.value)}
            >
              <option value="">All records</option>
              {table.columns.map((c: O) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <input
              aria-label="Filter value"
              placeholder="Filter value"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
            <button
              className="secondary"
              onClick={() => act(() => loadTable(selected, revealed, 0))}
            >
              Apply filter
            </button>
          </div>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Logical record</th>
                  {table.columns.map((c: O) => (
                    <th key={c.id}>{c.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((r: O) => (
                  <tr key={r.record}>
                    <td>{r.record}</td>
                    {r.values.map((v: any, i: number) => (
                      <td key={i}>{v ?? <em>Missing</em>}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination">
            <span>
              {offset + 1}–{Math.min(offset + 20, table.total)} of {table.total}
            </span>
            <button
              className="secondary compact"
              disabled={offset === 0}
              onClick={() =>
                act(() => loadTable(selected, revealed, offset - 20))
              }
            >
              Previous
            </button>
            <button
              className="secondary compact"
              disabled={offset + 20 >= table.total}
              onClick={() =>
                act(() => loadTable(selected, revealed, offset + 20))
              }
            >
              Next
            </button>
          </div>
        </section>
      )}
    </>
  );
}

function Multi({
  options,
  value,
  onChange,
  label,
}: {
  options: O[];
  value: string[];
  onChange: (v: string[]) => void;
  label: string;
}) {
  return (
    <fieldset className="multi">
      <legend>{label}</legend>
      {options.map((o) => (
        <label key={o.id}>
          <input
            type="checkbox"
            checked={value.includes(o.id)}
            onChange={(e) =>
              onChange(
                e.target.checked
                  ? [...value, o.id]
                  : value.filter((x) => x !== o.id),
              )
            }
          />
          <span>{o.name}</span>
          {o.role && <Badge>{o.role}</Badge>}
        </label>
      ))}
    </fieldset>
  );
}
function Scenarios({
  state,
  path,
  act,
  busy,
  go,
}: {
  state: O;
  path: (p: string) => string;
  act: any;
  busy: boolean;
  go: () => void;
}) {
  const ds = state.datasets,
    [name, setName] = useState("Release review"),
    [audience, setAudience] = useState("Research partners"),
    [purpose, setPurpose] = useState("Share programme feedback for analysis"),
    [candidates, setCandidates] = useState<string[]>([]),
    [available, setAvailable] = useState<string[]>([]),
    [rules, setRules] = useState<O[]>([]),
    [qi, setQi] = useState<string[]>([]),
    [protectedCols, setProtected] = useState<string[]>([]),
    [utility, setUtility] = useState<O[]>([]),
    [anchor, setAnchor] = useState(""),
    [anchorCols, setAnchorCols] = useState<string[]>([]),
    [anchorReason, setAnchorReason] = useState(""),
    [threshold, setThreshold] = useState(5),
    [referenceCoverage, setReferenceCoverage] = useState(
      "Unknown completeness; supplied reference records only.",
    ),
    [profile, setProfile] = useState<O | null>(null);
  const [src, setSrc] = useState(""),
    [dst, setDst] = useState(""),
    [srcCols, setSrcCols] = useState<string[]>([]),
    [dstCols, setDstCols] = useState<string[]>([]),
    [meaning, setMeaning] = useState(""),
    [context, setContext] = useState("Same training cohort and review period"),
    [subject, setSubject] = useState("person"),
    [predicate, setPredicate] = useState("exact"),
    [trim, setTrim] = useState(false),
    [fold, setFold] = useState(false),
    [nfc, setNfc] = useState(false),
    [confirm, setConfirm] = useState(false);
  const [suggestions, setSuggestions] = useState<O[]>([]),
    [bundlePaths, setBundlePaths] = useState<string[]>([]),
    [bundleContext, setBundleContext] = useState(""),
    [bundleConfirmed, setBundleConfirmed] = useState(false),
    [uGrain, setUGrain] = useState("month");
  useEffect(() => {
    api(path("/mapping-suggestions"))
      .then(setSuggestions)
      .catch(() => {});
  }, []);
  const [uOp, setUOp] = useState("count"),
    [uGroup, setUGroup] = useState(""),
    [uVal, setUVal] = useState(""),
    [uDrift, setUDrift] = useState(0.1),
    [minRetention, setMinRetention] = useState(1);
  const candidate = ds.find((d: O) => d.id === candidates[0]);
  const eligible = ds.filter((d: O) =>
    [...candidates, ...available].includes(d.id),
  );
  function rule() {
    return {
      id: crypto.randomUUID().replaceAll("-", ""),
      source: src,
      target: dst,
      source_columns: srcCols,
      target_columns: dstCols,
      meaning,
      subject,
      context,
      predicate,
      trim,
      casefold: fold,
      unicode_nfc: nfc,
      confirmed: confirm,
      revision: 1,
    };
  }
  const possiblePaths: O[] = [];
  function walk(current: string, chain: O[], seen: string[]) {
    if (chain.length >= 3 || possiblePaths.length >= 100) return;
    for (const r of rules) {
      if (r.source !== current || seen.includes(r.target)) continue;
      const next = [...chain, r];
      possiblePaths.push({
        id: JSON.stringify(next.map((x) => x.id)),
        name: [
          ds.find((d: O) => d.id === candidates[0])?.name,
          ...next.map((x) => ds.find((d: O) => d.id === x.target)?.name),
        ].join(" → "),
      });
      walk(r.target, next, [...seen, r.target]);
    }
  }
  if (candidates[0]) walk(candidates[0], [], [candidates[0]]);
  function reset() {
    setSrcCols([]);
    setDstCols([]);
    setMeaning("");
    setConfirm(false);
    setProfile(null);
  }
  return (
    <>
      {!ds.length ? (
        <section className="panel">
          <Empty title="Import your datasets first">
            Candidate and reference roles become available after import review.
          </Empty>
        </section>
      ) : (
        <>
          <section className="panel">
            <div className="section-heading">
              <h2>1. Describe the release</h2>
              <Badge>Immutable snapshot</Badge>
            </div>
            <div className="form-grid">
              <Field label="Scenario name">
                <input
                  value={name}
                  maxLength={120}
                  onChange={(e) => setName(e.target.value)}
                />
              </Field>
              <Field label="Intended audience">
                <input
                  value={audience}
                  maxLength={300}
                  onChange={(e) => setAudience(e.target.value)}
                />
              </Field>
            </div>
            <Field label="Purpose">
              <input
                value={purpose}
                maxLength={500}
                onChange={(e) => setPurpose(e.target.value)}
              />
            </Field>
            <div className="two-col">
              <Multi
                label="Candidate versions to share"
                options={ds.filter((d: O) => d.role === "candidate")}
                value={candidates}
                onChange={(v) => {
                  setCandidates(v);
                  setQi([]);
                  setUtility([]);
                  setProtected([]);
                }}
              />
              <Multi
                label="Information available to this audience"
                options={ds.filter(
                  (d: O) => d.role !== "internal" && !candidates.includes(d.id),
                )}
                value={available}
                onChange={setAvailable}
              />
            </div>
            <p className="callout">
              <LockKeyhole size={17} />
              Internal-only data is excluded. Alternative drafts are included
              only if selected. Recorded releases for this audience remain part
              of the history model.
            </p>
            <Field label="Reference coverage and limitations">
              <textarea
                value={referenceCoverage}
                maxLength={500}
                onChange={(e) => setReferenceCoverage(e.target.value)}
              />
            </Field>
          </section>
          <section className="panel">
            <h2>2. Confirm meaningful relationships</h2>
            {suggestions.filter(
              (x) =>
                [...candidates, ...available].includes(x.source) &&
                [...candidates, ...available].includes(x.target),
            ).length > 0 && (
              <details>
                <summary>Review mapping suggestions</summary>
                <p>
                  Suggestions use matching header spelling and reviewed types.
                  They are not confirmed semantic equivalence.
                </p>
                {suggestions
                  .filter(
                    (x) =>
                      [...candidates, ...available].includes(x.source) &&
                      [...candidates, ...available].includes(x.target),
                  )
                  .slice(0, 12)
                  .map((x, i) => (
                    <div className="rule-row" key={i}>
                      <div>
                        <strong>
                          {ds.find((d: O) => d.id === x.source)?.name} →{" "}
                          {ds.find((d: O) => d.id === x.target)?.name}
                        </strong>
                        <small>{x.reason}</small>
                      </div>
                      <button
                        className="secondary compact"
                        onClick={() => {
                          setSrc(x.source);
                          setDst(x.target);
                          setSrcCols([x.source_column]);
                          setDstCols([x.target_column]);
                          setMeaning("");
                          setConfirm(false);
                        }}
                      >
                        Review suggestion
                      </button>
                    </div>
                  ))}
              </details>
            )}
            <p className="muted">
              Matching headers do not establish matching meaning. Select
              composite components in corresponding order; every component must
              match. Nulls never form identifier keys.
            </p>
            <div className="form-grid">
              <Field label="Source version">
                <select
                  value={src}
                  onChange={(e) => {
                    setSrc(e.target.value);
                    setSrcCols([]);
                  }}
                >
                  <option value="">Choose source</option>
                  {eligible.map((d: O) => (
                    <option value={d.id} key={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Destination version">
                <select
                  value={dst}
                  onChange={(e) => {
                    setDst(e.target.value);
                    setDstCols([]);
                  }}
                >
                  <option value="">Choose destination</option>
                  {eligible
                    .filter((d: O) => d.id !== src)
                    .map((d: O) => (
                      <option value={d.id} key={d.id}>
                        {d.name}
                      </option>
                    ))}
                </select>
              </Field>
            </div>
            <div className="two-col">
              <Multi
                label="Source components (selection order)"
                options={ds.find((d: O) => d.id === src)?.columns || []}
                value={srcCols}
                onChange={setSrcCols}
              />
              <Multi
                label="Destination components (matching order)"
                options={ds.find((d: O) => d.id === dst)?.columns || []}
                value={dstCols}
                onChange={setDstCols}
              />
            </div>
            <small>
              Component pairing:{" "}
              {srcCols
                .map(
                  (c, i) =>
                    (ds
                      .find((d: O) => d.id === src)
                      ?.columns.find((x: O) => x.id === c)?.name || "?") +
                    " → " +
                    (ds
                      .find((d: O) => d.id === dst)
                      ?.columns.find((x: O) => x.id === dstCols[i])?.name ||
                      "?"),
                )
                .join(" · ") || "Select corresponding columns"}
            </small>
            <div className="form-grid">
              <Field label="Intended meaning">
                <input
                  placeholder="e.g. Feedback and attendance refer to the same participant context"
                  maxLength={200}
                  value={meaning}
                  onChange={(e) => setMeaning(e.target.value)}
                />
              </Field>
              <Field label="Subject unit">
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                >
                  {["person", "household", "organisation", "event"].map((x) => (
                    <option key={x}>{x}</option>
                  ))}
                </select>
              </Field>
              <Field label="Time / cohort context">
                <input
                  value={context}
                  maxLength={200}
                  onChange={(e) => setContext(e.target.value)}
                />
              </Field>
              <Field
                label="Predicate"
                hint="Typed compatibility supports reviewed date/numeric intervals after generalisation."
              >
                <select
                  value={predicate}
                  onChange={(e) => setPredicate(e.target.value)}
                >
                  <option value="exact">Exact / composite exact</option>
                  <option value="compatible">
                    Typed-compatible / composite
                  </option>
                </select>
              </Field>
            </div>
            <div className="checks">
              <label>
                <input
                  type="checkbox"
                  checked={trim}
                  onChange={(e) => setTrim(e.target.checked)}
                />
                Trim whitespace
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={fold}
                  onChange={(e) => setFold(e.target.checked)}
                />
                Case fold
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={nfc}
                  onChange={(e) => setNfc(e.target.checked)}
                />
                Unicode NFC
              </label>
            </div>
            <label className="confirm-check">
              <input
                type="checkbox"
                checked={confirm}
                onChange={(e) => setConfirm(e.target.checked)}
              />
              I confirm the subject, component meanings, and time/cohort
              assumptions for this rule.
            </label>
            <div className="actions">
              <button
                className="secondary"
                disabled={
                  busy ||
                  !src ||
                  !dst ||
                  !srcCols.length ||
                  srcCols.length !== dstCols.length ||
                  meaning.length < 3
                }
                onClick={() =>
                  act(async () =>
                    setProfile(
                      await api(path("/rule-profile"), "POST", rule()),
                    ),
                  )
                }
              >
                Profile fan-out
              </button>
              <button
                className="primary"
                disabled={
                  !confirm ||
                  !src ||
                  !dst ||
                  !srcCols.length ||
                  srcCols.length !== dstCols.length ||
                  meaning.length < 3
                }
                onClick={() => {
                  setRules([...rules, rule()]);
                  reset();
                }}
              >
                <Plus size={16} />
                Add confirmed rule
              </button>
            </div>
            {profile && (
              <div className="callout">
                <ScanLine size={17} />
                <div>
                  {profile.fanout.toLocaleString()} possible record pairs · up
                  to {profile.max_candidates ?? "unbounded"} candidates per
                  source · {profile.missing} source records missing components
                  {profile.reason && <p>{profile.reason}</p>}
                </div>
              </div>
            )}
            {rules.map((r, i) => (
              <div className="rule-row" key={r.id}>
                <Badge tone="teal">Rule {i + 1}</Badge>
                <div>
                  <strong>
                    {ds.find((d: O) => d.id === r.source)?.name} →{" "}
                    {ds.find((d: O) => d.id === r.target)?.name}
                  </strong>
                  <small>
                    {r.meaning} · {r.source_columns.length} conjunctive
                    component(s) · {r.predicate}
                  </small>
                </div>
                <button
                  className="icon-btn danger"
                  aria-label={"Remove rule " + (i + 1)}
                  onClick={() => setRules(rules.filter((x) => x.id !== r.id))}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </section>
          <section className="panel">
            <h2>3. Define diagnostics and analytical requirements</h2>
            {candidate ? (
              <>
                <Multi
                  label={
                    "Within-file quasi-identifier combination · " +
                    candidate.name
                  }
                  options={candidate.columns}
                  value={qi}
                  onChange={setQi}
                />
                <Multi
                  label="Protected columns (cannot be transformed or removed)"
                  options={candidate.columns}
                  value={protectedCols}
                  onChange={setProtected}
                />
                <div className="form-grid">
                  <Field label="Analytical goal">
                    <select
                      value={uOp}
                      onChange={(e) => setUOp(e.target.value)}
                    >
                      <option value="count">Counts by category</option>
                      <option value="mean">Numeric mean by group</option>
                      <option value="median">Numeric median by group</option>
                      <option value="time_count">Counts by time period</option>
                    </select>
                  </Field>
                  <Field label="Group / date column">
                    <select
                      value={uGroup}
                      onChange={(e) => setUGroup(e.target.value)}
                    >
                      <option value="">All records</option>
                      {candidate.columns.map((c: O) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  </Field>
                  {["mean", "median"].includes(uOp) && (
                    <Field label="Numeric value">
                      <select
                        value={uVal}
                        onChange={(e) => setUVal(e.target.value)}
                      >
                        <option value="">Choose value</option>
                        {candidate.columns
                          .filter((c: O) => c.type === "number")
                          .map((c: O) => (
                            <option key={c.id} value={c.id}>
                              {c.name}
                            </option>
                          ))}
                      </select>
                    </Field>
                  )}
                  {uOp === "time_count" && (
                    <Field label="Time granularity">
                      <select
                        value={uGrain}
                        onChange={(e) => setUGrain(e.target.value)}
                      >
                        <option value="month">Month</option>
                        <option value="quarter">Quarter</option>
                        <option value="year">Year</option>
                      </select>
                    </Field>
                  )}
                  <Field label="Maximum relative drift">
                    <input
                      type="number"
                      min="0"
                      max="10"
                      step="0.01"
                      value={uDrift}
                      onChange={(e) => setUDrift(Number(e.target.value))}
                    />
                  </Field>
                </div>
                <button
                  className="secondary"
                  disabled={["mean", "median"].includes(uOp) && !uVal}
                  onClick={() =>
                    setUtility([
                      ...utility,
                      {
                        dataset: candidate.id,
                        operation: uOp,
                        group: uGroup || null,
                        value: ["mean", "median"].includes(uOp) ? uVal : null,
                        granularity: uGrain,
                        max_relative_drift: uDrift,
                      },
                    ])
                  }
                >
                  Add analytical requirement
                </button>
                {utility.map((u, i) => (
                  <div className="rule-row" key={i}>
                    <strong>
                      {u.operation} by{" "}
                      {candidate.columns.find((c: O) => c.id === u.group)
                        ?.name || "all records"}{" "}
                      · max drift {u.max_relative_drift}
                    </strong>
                    <button
                      className="icon-btn"
                      aria-label={"Remove analytical requirement " + (i + 1)}
                      onClick={() =>
                        setUtility(utility.filter((_, n) => n !== i))
                      }
                    >
                      <X size={15} />
                    </button>
                  </div>
                ))}
              </>
            ) : (
              <p className="muted">
                Choose a candidate version above to configure diagnostics and
                analytical goals.
              </p>
            )}
            <div className="form-grid">
              <Field label="Minimum retained-row proportion">
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={minRetention}
                  onChange={(e) => setMinRetention(Number(e.target.value))}
                />
              </Field>
              <Field
                label="Candidate review threshold"
                hint="A review preference; it does not establish a safe release."
              >
                <input
                  type="number"
                  min="2"
                  max="100"
                  value={threshold}
                  onChange={(e) => setThreshold(Number(e.target.value))}
                />
              </Field>
            </div>
            <details>
              <summary>Optional: confirmed identity anchor</summary>
              <p>
                Without a defensible entity key, counts describe reference
                records. A name alone cannot establish an identity anchor.
              </p>
              <Field label="Anchor reference version">
                <select
                  value={anchor}
                  onChange={(e) => {
                    setAnchor(e.target.value);
                    setAnchorCols([]);
                  }}
                >
                  <option value="">No identity anchor</option>
                  {eligible.map((d: O) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </Field>
              {anchor && (
                <>
                  <Multi
                    label="Entity-key components"
                    options={ds.find((d: O) => d.id === anchor)?.columns || []}
                    value={anchorCols}
                    onChange={setAnchorCols}
                  />
                  <Field label="Why is this a defensible entity key?">
                    <textarea
                      value={anchorReason}
                      maxLength={300}
                      onChange={(e) => setAnchorReason(e.target.value)}
                    />
                  </Field>
                </>
              )}
            </details>
            <details>
              <summary>Optional: explicitly combine evidence paths</summary>
              <p>
                Independent paths are never intersected by default. Only combine
                confirmed paths when every predicate concerns the same subject,
                cohort and time and ends at the same reference version. Disjoint
                candidate sets are reported as contradictory evidence.
              </p>
              <Multi
                label="Same-subject knowledge-bundle paths"
                options={possiblePaths}
                value={bundlePaths}
                onChange={setBundlePaths}
              />
              <Field label="Why do these paths describe the same subject and context?">
                <textarea
                  value={bundleContext}
                  maxLength={300}
                  onChange={(e) => setBundleContext(e.target.value)}
                />
              </Field>
              <label className="confirm-check">
                <input
                  type="checkbox"
                  checked={bundleConfirmed}
                  onChange={(e) => setBundleConfirmed(e.target.checked)}
                />
                I confirm this evidence conjunction, subject, cohort and time.
              </label>
            </details>
            <div className="actions">
              <button
                className="primary"
                disabled={
                  busy ||
                  !candidates.length ||
                  !name ||
                  audience.length < 3 ||
                  purpose.length < 3 ||
                  (!!anchor && (!anchorCols.length || anchorReason.length < 10))
                }
                onClick={() =>
                  act(async () => {
                    await api(path("/scenarios"), "POST", {
                      name,
                      audience,
                      purpose,
                      candidates,
                      available,
                      rules,
                      anchors: anchor
                        ? [
                            {
                              dataset: anchor,
                              columns: anchorCols,
                              justification: anchorReason,
                            },
                          ]
                        : [],
                      quasi_identifiers: qi.length
                        ? [{ dataset: candidates[0], columns: qi }]
                        : [],
                      utility,
                      protected: protectedCols,
                      min_retention: minRetention,
                      threshold,
                      max_depth: 3,
                      reference_coverage: referenceCoverage,
                      bundles: bundlePaths.length
                        ? [
                            {
                              source: candidates[0],
                              paths: bundlePaths.map((p) => JSON.parse(p)),
                              same_subject_context: bundleContext,
                              confirmed: bundleConfirmed,
                            },
                          ]
                        : [],
                    });
                    go();
                  }, "Scenario snapshot saved. Review its scope and run an audit.")
                }
              >
                <Check size={16} />
                Save scenario snapshot
              </button>
            </div>
          </section>
        </>
      )}
      <section className="panel">
        <h2>Saved scenario snapshots</h2>
        {!state.scenarios.length ? (
          <p className="muted">
            Your explicit release model will be preserved here.
          </p>
        ) : (
          state.scenarios.map((s: O) => (
            <div className="rule-row" key={s.id}>
              <div>
                <strong>{s.name}</strong>
                <small>
                  {s.audience} · {s.candidates.length} candidates ·{" "}
                  {s.available.length} available versions · {s.rules.length}{" "}
                  rules
                </small>
              </div>
              <Badge
                tone={
                  s.workspace_revision === state.workspace.revision
                    ? "teal"
                    : "amber"
                }
              >
                {s.workspace_revision === state.workspace.revision
                  ? "current"
                  : "stale"}
              </Badge>
              <button
                className="secondary compact"
                onClick={() => {
                  setName(s.name + " · revised");
                  setAudience(s.audience);
                  setPurpose(s.purpose);
                  setCandidates(s.candidates);
                  setAvailable(s.available);
                  setRules(s.rules.filter((r: O) => !r._historical));
                  setQi(s.quasi_identifiers[0]?.columns || []);
                  setProtected(s.protected);
                  setUtility(s.utility);
                  setThreshold(s.threshold);
                  setReferenceCoverage(s.reference_coverage);
                  setMinRetention(s.min_retention);
                  setAnchor(s.anchors[0]?.dataset || "");
                  setAnchorCols(s.anchors[0]?.columns || []);
                  setAnchorReason(s.anchors[0]?.justification || "");
                  setBundlePaths(
                    (s.bundles[0]?.paths || []).map((p: string[]) =>
                      JSON.stringify(p),
                    ),
                  );
                  setBundleContext(s.bundles[0]?.same_subject_context || "");
                  setBundleConfirmed(s.bundles[0]?.confirmed || false);
                }}
              >
                Revise this scope
              </button>
            </div>
          ))
        )}
      </section>
    </>
  );
}

function Audits({
  state,
  path,
  act,
  busy,
  graphReady,
  goRepair,
}: {
  state: O;
  path: (p: string) => string;
  act: any;
  busy: boolean;
  graphReady: boolean;
  goRepair: () => void;
}) {
  const [selected, setSelected] = useState(""),
    [opened, setOpened] = useState(""),
    [before, setBefore] = useState(""),
    [after, setAfter] = useState(""),
    [comparison, setComparison] = useState<O | null>(null);
  const a =
      state.audits.find((x: O) => x.id === selected) || state.audits.at(-1),
    scenario = a ? state.scenarios.find((s: O) => s.id === a.scenario) : null;
  const ds = (id: string) =>
    state.datasets.find((d: O) => d.id === id)?.name || id.slice(0, 8);
  return (
    <>
      <section className="panel">
        <div className="section-heading">
          <h2>Run a scoped audit</h2>
          <Badge>All in-limit records</Badge>
        </div>
        {!state.scenarios.length ? (
          <Empty title="Define a release scenario first">
            Audit findings depend on an explicit audience, version selection and
            confirmed rules.
          </Empty>
        ) : (
          <div className="scenario-actions">
            {state.scenarios
              .filter(
                (s: O) => !state.branches.some((b: O) => b.scenario === s.id),
              )
              .map((s: O) => (
                <div className="rule-row" key={s.id}>
                  <div>
                    <strong>{s.name}</strong>
                    <small>
                      {s.audience} · depth {s.max_depth} ·{" "}
                      {s.rules.filter((r: O) => r.confirmed).length} confirmed
                      rules
                    </small>
                  </div>
                  <Badge
                    tone={
                      s.workspace_revision === state.workspace.revision
                        ? "teal"
                        : "amber"
                    }
                  >
                    {s.workspace_revision === state.workspace.revision
                      ? "current"
                      : "stale"}
                  </Badge>
                  <button
                    className="primary compact"
                    disabled={
                      busy ||
                      !graphReady ||
                      s.workspace_revision !== state.workspace.revision
                    }
                    onClick={() =>
                      act(
                        () => api(path("/audits"), "POST", { scenario: s.id }),
                        "Audit queued. Progress appears in background activity.",
                      )
                    }
                  >
                    <ScanLine size={15} />
                    Run audit
                  </button>
                </div>
              ))}
          </div>
        )}
      </section>
      {a && (
        <>
          <div className="section-heading">
            <h2>Audit results</h2>
            <select
              aria-label="Select audit"
              value={a.id}
              onChange={(e) => {
                setSelected(e.target.value);
                setOpened("");
              }}
            >
              {state.audits.map((x: O) => (
                <option key={x.id} value={x.id}>
                  {state.scenarios.find((s: O) => s.id === x.scenario)?.name} ·{" "}
                  {x.id.slice(0, 8)}
                </option>
              ))}
            </select>
          </div>
          <div className="message warning">
            <AlertTriangle size={18} />
            <div>
              <strong>Detected linkage exposure is scoped evidence.</strong> A
              single candidate is not proof of identity. Counts describe{" "}
              {a.findings.find((f: O) => f.kind === "linkage")?.unit ||
                "records"}
              .
            </div>
          </div>
          <div className="stats-grid">
            <Stat
              label="Candidate records"
              value={a.summary.candidate_rows}
              sub="Full source denominator"
              icon={<Database size={20} />}
            />
            <Stat
              label="Single-candidate path records"
              value={a.summary.single_candidate_path_records}
              sub="Record/path pairs; paths may overlap"
              icon={<ScanLine size={20} />}
            />
            <Stat
              label="Assessed path records"
              value={a.summary.assessed_path_records}
              sub="Across eligible rule chains"
              icon={<Check size={20} />}
            />
            <Stat
              label="Unassessed path records"
              value={a.summary.unassessed_path_records}
              sub="Missing, blocked or incomplete"
              icon={<AlertTriangle size={20} />}
            />
          </div>
          <section className="panel">
            <div className="section-heading">
              <h2>Findings and evidence</h2>
              <Badge tone={a.status === "partial" ? "amber" : "teal"}>
                {a.status}
                {a.workspace_revision !== state.workspace.revision
                  ? " · stale"
                  : ""}
              </Badge>
            </div>
            <p className="muted">
              Audience: {scenario?.audience} · Purpose: {scenario?.purpose} ·{" "}
              {a.elapsed_seconds}s
            </p>
            {!a.findings.length && (
              <Empty title="No findings detected within this scope">
                Review the analysis coverage and unresolved assumptions below.
              </Empty>
            )}
            {a.findings.map((f: O) => (
              <article className="finding" key={f.id}>
                <button
                  className="finding-heading"
                  aria-expanded={opened === f.id}
                  onClick={() => setOpened(opened === f.id ? "" : f.id)}
                >
                  <span
                    className={
                      "finding-icon " +
                      (f.severity === "high" ? "amber" : "teal")
                    }
                  >
                    <ScanLine size={19} />
                  </span>
                  <div>
                    <strong>
                      {f.kind === "linkage"
                        ? `${f.single_candidate_rows} single-candidate record/path pairs`
                        : f.kind === "within_file"
                          ? `${f.single_record_rows} records in classes of size one`
                          : f.kind === "knowledge_bundle"
                            ? "Explicit knowledge-bundle conjunction"
                            : "Direct identifier columns remain"}
                    </strong>
                    <small>
                      {ds(f.source)}
                      {f.target ? " → " + ds(f.target) : ""} ·{" "}
                      {f.kind.replaceAll("_", " ")}
                    </small>
                  </div>
                  <Badge tone={f.severity === "high" ? "amber" : "neutral"}>
                    {f.severity}
                  </Badge>
                  <ChevronRight size={17} />
                </button>
                {opened === f.id && (
                  <div className="finding-body">
                    <p>{f.explanation}</p>
                    {f.historical && (
                      <p className="callout warning">
                        Historical release exposure: changing the current
                        candidate cannot retract this already released version.
                      </p>
                    )}
                    {f.kind === "linkage" && (
                      <>
                        <div className="evidence-chain">
                          <span>{ds(f.source)}</span>
                          {f.rules.map((rid: string) => (
                            <React.Fragment key={rid}>
                              <ArrowRight size={17} />
                              <span>
                                {scenario?.rules.find((r: O) => r.id === rid)
                                  ?.meaning || rid.slice(0, 8)}
                              </span>
                            </React.Fragment>
                          ))}
                          <ArrowRight size={17} />
                          <span>{ds(f.target)}</span>
                        </div>
                        <p>
                          <strong>{f.unit}</strong> · {f.assessed_rows} assessed
                          · {f.unassessed_rows} unassessed · {f.no_match_rows}{" "}
                          no match · {f.status}
                        </p>
                        <div className="table-scroll">
                          <table>
                            <thead>
                              <tr>
                                <th>Source logical record</th>
                                <th>Candidates</th>
                                <th>Interpretation</th>
                                <th>Masked endpoint references</th>
                              </tr>
                            </thead>
                            <tbody>
                              {f.records.slice(0, 100).map((r: O) => (
                                <tr key={r.record}>
                                  <td>Record {r.record}</td>
                                  <td>{r.candidate_count}</td>
                                  <td>{r.label}</td>
                                  <td>
                                    {r.endpoint_records
                                      .map(
                                        (n: number) => "Reference record " + n,
                                      )
                                      .join(", ") || "—"}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        {f.records.length > 100 && (
                          <p className="muted">
                            First 100 assessed records shown. The aggregate
                            includes every assessed record.
                          </p>
                        )}
                        <button
                          className="text-btn"
                          onClick={() =>
                            act(
                              () =>
                                api(
                                  path("/audits/" + a.id + "/evidence/" + f.id),
                                ),
                              "Graph evidence retrieved for this exact audit projection.",
                            )
                          }
                        >
                          Verify stored graph evidence
                          <ArrowUpRight size={14} />
                        </button>
                      </>
                    )}
                    {f.kind === "within_file" && (
                      <>
                        <p>
                          Class size → record count:{" "}
                          {Object.entries(f.record_class_histogram)
                            .map(([k, v]) => `${k} → ${v}`)
                            .join(" · ")}
                        </p>
                        <p>
                          {f.assessed_rows} assessed records ·{" "}
                          {f.unassessed_rows} unassessed
                        </p>
                        {f.homogeneity.map((h: O) => (
                          <p key={h.column}>
                            {h.single_value_classes} of {h.assessed_classes}{" "}
                            assessed classes contain one distinct nonmissing
                            sensitive value.
                          </p>
                        ))}
                      </>
                    )}
                    {f.kind === "direct_identifiers" && (
                      <p>
                        {f.columns
                          .map(
                            (cid: string) =>
                              state.datasets
                                .find((d: O) => d.id === f.source)
                                ?.columns.find((c: O) => c.id === cid)?.name,
                          )
                          .join(", ")}{" "}
                        · {f.affected_rows} affected records
                      </p>
                    )}
                  </div>
                )}
              </article>
            ))}
            <div className="actions">
              <button className="primary" onClick={goRepair}>
                Compare repair options
                <ArrowRight size={16} />
              </button>
              <button
                className="text-btn danger"
                onClick={() =>
                  act(() => api(path("/audits/" + a.id), "DELETE"))
                }
              >
                Delete this audit
              </button>
            </div>
          </section>
          <section className="panel">
            <h2>Analysis coverage</h2>
            <p>{a.assumptions.reference_coverage}</p>
            {a.summary.historical_single_candidate_path_records > 0 && (
              <p className="warning">
                {a.summary.historical_single_candidate_path_records}{" "}
                single-candidate path records remain in historical releases,
                separate from the current candidate.
              </p>
            )}
            <p className="muted">
              At most {a.assumptions.max_depth} approved joins per path.
              Candidate threshold {a.assumptions.threshold} is a review
              preference.
            </p>
            {a.coverage.length ? (
              a.coverage.map((c: O, i: number) => (
                <div className="coverage-note" key={i}>
                  <AlertTriangle size={16} />
                  <div>
                    {c.reason || "Rule assessment has missing components."}
                    {c.missing !== undefined && (
                      <small>
                        {c.missing} source records missing required components
                      </small>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p>
                No additional coverage gaps detected within the configured
                search bounds.
              </p>
            )}
          </section>
        </>
      )}
      {state.audits.length > 1 && (
        <section className="panel">
          <h2>Before / after adding an available export</h2>
          <p className="muted">
            Only compatible scopes can isolate the impact of adding information.
            Changed candidate versions require a repair comparison.
          </p>
          <div className="actions">
            <select
              aria-label="Before audit"
              value={before}
              onChange={(e) => setBefore(e.target.value)}
            >
              <option value="">Before audit</option>
              {state.audits.map((a: O) => (
                <option key={a.id} value={a.id}>
                  {state.scenarios.find((s: O) => s.id === a.scenario)?.name} ·{" "}
                  {a.id.slice(0, 8)}
                </option>
              ))}
            </select>
            <select
              aria-label="After audit"
              value={after}
              onChange={(e) => setAfter(e.target.value)}
            >
              <option value="">After audit</option>
              {state.audits.map((a: O) => (
                <option key={a.id} value={a.id}>
                  {state.scenarios.find((s: O) => s.id === a.scenario)?.name} ·{" "}
                  {a.id.slice(0, 8)}
                </option>
              ))}
            </select>
            <button
              className="secondary"
              disabled={!before || !after || before === after}
              onClick={() =>
                act(async () =>
                  setComparison(
                    await api(path("/comparisons"), "POST", { before, after }),
                  ),
                )
              }
            >
              Compare addition
            </button>
          </div>
          {comparison && (
            <div>
              {comparison.changes.length ? (
                comparison.changes.map((c: O, i: number) => (
                  <p key={i}>
                    {c.new_path ? "New path" : "Changed path"} from{" "}
                    {ds(c.source)} · single-candidate record delta{" "}
                    {c.single_candidate_record_delta}
                  </p>
                ))
              ) : (
                <p>
                  No new or changed single-candidate path findings within these
                  scopes.
                </p>
              )}
            </div>
          )}
        </section>
      )}
    </>
  );
}

function Repairs({
  state,
  path,
  act,
  busy,
  graphReady,
  goExport,
}: {
  state: O;
  path: (p: string) => string;
  act: any;
  busy: boolean;
  graphReady: boolean;
  goExport: () => void;
}) {
  const eligible = state.scenarios.filter(
    (s: O) => !state.branches.some((b: O) => b.scenario === s.id),
  );
  const [sid, setSid] = useState(""),
    [did, setDid] = useState(""),
    [cid, setCid] = useState(""),
    [kind, setKind] = useState("drop"),
    [width, setWidth] = useState(10),
    [name, setName] = useState("Repair option"),
    [recipe, setRecipe] = useState<O[]>([]);
  const scenario = eligible.find((s: O) => s.id === sid) || eligible.at(-1),
    candidate = state.datasets.find(
      (d: O) => d.id === (did || scenario?.candidates[0]),
    );
  const baseline = state.audits
    .filter((a: O) => a.scenario === scenario?.id)
    .at(-1);
  return (
    <>
      <section className="panel">
        <h2>Test a repair branch</h2>
        <p className="muted">
          Originals and audience references remain immutable. Each recipe
          rebuilds the candidate projection and reruns every eligible path. Try
          competing options.
        </p>
        {!scenario ? (
          <Empty title="Save a scenario and run an audit first">
            Repairs need a fixed audience, references, mappings, and analytical
            requirements.
          </Empty>
        ) : (
          <>
            <div className="form-grid">
              <Field label="Base scenario">
                <select
                  value={scenario.id}
                  onChange={(e) => {
                    setSid(e.target.value);
                    setDid("");
                    setCid("");
                    setRecipe([]);
                  }}
                >
                  {eligible.map((s: O) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Branch name">
                <input
                  value={name}
                  maxLength={120}
                  onChange={(e) => setName(e.target.value)}
                />
              </Field>
              <Field label="Candidate version">
                <select
                  value={candidate?.id || ""}
                  onChange={(e) => {
                    setDid(e.target.value);
                    setCid("");
                  }}
                >
                  {scenario.candidates.map((id: string) => (
                    <option key={id} value={id}>
                      {state.datasets.find((d: O) => d.id === id)?.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Column">
                <select value={cid} onChange={(e) => setCid(e.target.value)}>
                  <option value="">Choose a column</option>
                  {candidate?.columns.map((c: O) => (
                    <option
                      key={c.id}
                      value={c.id}
                      disabled={scenario.protected.includes(c.id)}
                    >
                      {c.name}
                      {scenario.protected.includes(c.id) ? " · protected" : ""}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Transformation">
                <select value={kind} onChange={(e) => setKind(e.target.value)}>
                  <option value="drop">Remove column</option>
                  <option value="suppress">
                    Suppress selected column values
                  </option>
                  <option value="rare_suppress">
                    Suppress rare values in column
                  </option>
                  <option value="numeric_bucket">Numeric intervals</option>
                  <option value="date_month">Dates to month intervals</option>
                  <option value="date_quarter">
                    Dates to quarter intervals
                  </option>
                  <option value="date_year">Dates to year intervals</option>
                </select>
              </Field>
              {kind === "numeric_bucket" && (
                <Field label="Numeric bucket width">
                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={width}
                    onChange={(e) => setWidth(Number(e.target.value))}
                  />
                </Field>
              )}
            </div>
            <button
              className="secondary"
              disabled={!cid || !candidate}
              onClick={() => {
                setRecipe([
                  ...recipe,
                  {
                    dataset: candidate.id,
                    column: cid,
                    kind,
                    width,
                    rare_threshold: scenario.threshold,
                  },
                ]);
                setCid("");
              }}
            >
              <Plus size={15} />
              Add to recipe
            </button>
            {recipe.map((r, i) => (
              <div className="rule-row" key={i}>
                <strong>
                  {r.kind.replaceAll("_", " ")} ·{" "}
                  {
                    state.datasets
                      .find((d: O) => d.id === r.dataset)
                      ?.columns.find((c: O) => c.id === r.column)?.name
                  }
                </strong>
                <button
                  className="icon-btn danger"
                  aria-label={"Remove transformation " + (i + 1)}
                  onClick={() => setRecipe(recipe.filter((_, n) => n !== i))}
                >
                  <X size={16} />
                </button>
              </div>
            ))}
            <div className="actions">
              <button
                className="primary"
                disabled={
                  busy ||
                  !graphReady ||
                  !recipe.length ||
                  !name ||
                  scenario.workspace_revision !== state.workspace.revision
                }
                onClick={() =>
                  act(async () => {
                    await api(path("/repairs"), "POST", {
                      scenario: scenario.id,
                      name,
                      recipe,
                    });
                    setRecipe([]);
                  }, "Repair evaluation queued. Its results will appear when the full re-audit finishes.")
                }
              >
                <ScanLine size={16} />
                Evaluate full repair
              </button>
            </div>
            {scenario.workspace_revision !== state.workspace.revision && (
              <p className="warning">
                This scenario is stale. Save a current snapshot before
                evaluating a repair.
              </p>
            )}
            {!baseline && (
              <p className="muted">
                Run the baseline audit for a direct before/after comparison.
              </p>
            )}
          </>
        )}
      </section>
      <div className="section-heading">
        <h2>Measured alternatives</h2>
        <Badge>Risk and utility are separate</Badge>
      </div>
      {!state.branches.length ? (
        <section className="panel">
          <Empty title="No repair branches tested yet">
            Build two recipes to compare their actual exposure, coverage, and
            analytical drift.
          </Empty>
        </section>
      ) : (
        <div className="repair-grid">
          {state.branches.map((b: O) => {
            const a = state.audits.find((a: O) => a.id === b.audit),
              base = state.audits
                .filter((a: O) => a.scenario === b.base_scenario)
                .at(-1);
            return (
              <section className="panel repair-card" key={b.id}>
                <div className="section-heading">
                  <Badge tone="violet">TESTED BRANCH</Badge>
                  <button
                    aria-label={"Delete branch " + b.name}
                    className="icon-btn danger"
                    onClick={() =>
                      act(() => api(path("/branches/" + b.id), "DELETE"))
                    }
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                <h2>{b.name}</h2>
                <div className="comparison-value">
                  <strong>
                    {a?.summary.single_candidate_path_records ?? "—"}
                  </strong>
                  <span>
                    single-candidate path records
                    {base && (
                      <small>
                        Baseline: {base.summary.single_candidate_path_records}
                      </small>
                    )}
                  </span>
                </div>
                <div className="metric-line">
                  <span>Assessed path records</span>
                  <strong>{a?.summary.assessed_path_records}</strong>
                </div>
                <div className="metric-line">
                  <span>Unassessed path records</span>
                  <strong>{a?.summary.unassessed_path_records}</strong>
                </div>
                <div className="metric-line">
                  <span>Analytical constraints</span>
                  <Badge
                    tone={b.utility.status === "satisfied" ? "teal" : "amber"}
                  >
                    {b.utility.status}
                  </Badge>
                </div>
                {b.utility.retention.map((r: O) => (
                  <div key={r.dataset}>
                    <div className="metric-line">
                      <span>Row retention</span>
                      <strong>
                        {(r.retention * 100).toFixed(1)}% ({r.retained_rows}/
                        {r.original_rows})
                      </strong>
                    </div>
                    <div className="metric-line">
                      <span>Missing cells before → after</span>
                      <strong>
                        {r.missing_cells_before} → {r.missing_cells_after}
                      </strong>
                    </div>
                  </div>
                ))}
                <p className="muted">{b.utility.population_note}</p>
                <details>
                  <summary>Analytical measurements and recipe</summary>
                  {b.recipe.map((r: O, i: number) => (
                    <p key={i}>
                      {r.kind.replaceAll("_", " ")} · column{" "}
                      {
                        state.datasets
                          .find((d: O) => d.id === r.dataset)
                          ?.columns.find((c: O) => c.id === r.column)?.name
                      }
                    </p>
                  ))}
                  {b.utility.metrics.map((m: O, i: number) => (
                    <div key={i}>
                      <h4>
                        {m.definition.operation} · {m.status}
                      </h4>
                      {m.unavailable_reason && (
                        <p className="warning">{m.unavailable_reason}</p>
                      )}
                      <div className="table-scroll">
                        <table>
                          <thead>
                            <tr>
                              <th>Group</th>
                              <th>Original</th>
                              <th>Repaired</th>
                              <th>Abs. change</th>
                              <th>Rel. change</th>
                            </tr>
                          </thead>
                          <tbody>
                            {m.groups.map((g: O, j: number) => (
                              <tr key={j}>
                                <td>{g.group}</td>
                                <td>{g.original ?? "Unavailable"}</td>
                                <td>{g.repaired ?? "Unavailable"}</td>
                                <td>{g.absolute_change ?? "Undefined"}</td>
                                <td>
                                  {g.relative_change === null
                                    ? "Undefined"
                                    : (g.relative_change * 100).toFixed(2) +
                                      "%"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </details>
                {b.utility.status === "violated" && (
                  <p className="callout warning">
                    No tested satisfaction of your analytical requirements for
                    this branch. Reject it or review the conflict explicitly.
                  </p>
                )}
                <button className="secondary wide" onClick={goExport}>
                  Review export options
                  <ArrowRight size={16} />
                </button>
              </section>
            );
          })}
        </div>
      )}
    </>
  );
}

function Releases({
  state,
  path,
  act,
  busy,
}: {
  state: O;
  path: (p: string) => string;
  act: any;
  busy: boolean;
}) {
  const [aid, setAid] = useState(""),
    [ack, setAck] = useState(false),
    [override, setOverride] = useState(false),
    [releasePackage, setReleasePackage] = useState(""),
    [audience, setAudience] = useState(""),
    [date, setDate] = useState(new Date().toLocaleDateString("en-CA"));
  const audit =
      state.audits.find((a: O) => a.id === aid) || state.audits.at(-1),
    branch = state.branches.find((b: O) => b.audit === audit?.id),
    scenario = state.scenarios.find((s: O) => s.id === audit?.scenario);
  return (
    <>
      <section className="panel">
        <div className="section-heading">
          <h2>Review and build a release package</h2>
          <Package size={21} />
        </div>
        {!audit ? (
          <Empty title="An inspected candidate comes first">
            Complete an audit or repair evaluation before creating a package.
          </Empty>
        ) : (
          <>
            <Field label="Inspected audit / branch">
              <select
                value={audit.id}
                onChange={(e) => {
                  setAid(e.target.value);
                  setAck(false);
                  setOverride(false);
                }}
              >
                {state.audits.map((a: O) => (
                  <option key={a.id} value={a.id}>
                    {state.scenarios.find((s: O) => s.id === a.scenario)?.name}{" "}
                    · {a.id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </Field>
            <div className="review-summary">
              <div>
                <small>Release scope</small>
                <strong>{scenario?.audience}</strong>
              </div>
              <div>
                <small>Coverage</small>
                <strong>{audit.status}</strong>
              </div>
              <div>
                <small>Single-candidate path records</small>
                <strong>{audit.summary.single_candidate_path_records}</strong>
              </div>
              <div>
                <small>Analytical requirements</small>
                <strong>
                  {branch?.utility.status || "Unmodified baseline"}
                </strong>
              </div>
            </div>
            <p className="muted">
              Includes transformed CSVs, a human-readable report,
              machine-readable findings, recipe, schema, scenario, utility and
              file digests. Confidential row examples and private lineage stay
              out.
            </p>
            <p className="callout">
              Spreadsheet formula protection uses reversible transport escaping.
              The reopened semantic data is checked against the audited branch;
              escaping receives no privacy credit.
            </p>
            <label className="confirm-check">
              <input
                type="checkbox"
                checked={ack}
                onChange={(e) => setAck(e.target.checked)}
              />
              I reviewed residual findings, assumptions, unassessed records and
              coverage limits.
            </label>
            {branch?.utility.status === "violated" && (
              <label className="confirm-check warning">
                <input
                  type="checkbox"
                  checked={override}
                  onChange={(e) => setOverride(e.target.checked)}
                />
                I explicitly accept that this branch violates the configured
                analytical requirements.
              </label>
            )}
            <button
              className="primary"
              disabled={
                busy ||
                !ack ||
                (branch?.utility.status === "violated" && !override) ||
                audit.workspace_revision !== state.workspace.revision
              }
              onClick={() =>
                act(
                  () =>
                    api(path("/packages"), "POST", {
                      audit: audit.id,
                      acknowledge_limits: ack,
                      accept_utility_violation: override,
                    }),
                  "Verified release package created. Downloading does not publish or record a release.",
                )
              }
            >
              <Package size={16} />
              Build verified package
            </button>
            {audit.workspace_revision !== state.workspace.revision && (
              <p className="warning">
                This audit is stale. A current scenario and audit are required
                for a new export.
              </p>
            )}
          </>
        )}
      </section>
      <section className="panel">
        <h2>Inspected packages</h2>
        {!state.packages.length ? (
          <p className="muted">
            Packages remain encrypted and require your authenticated session to
            download.
          </p>
        ) : (
          state.packages.map((p: O) => (
            <div className="package-row" key={p.id}>
              <span className="file-icon">
                <Package size={22} />
              </span>
              <div>
                <strong>Release package · {p.id.slice(0, 8)}</strong>
                <small>
                  SHA-256 {p.digest.slice(0, 20)}… ·{" "}
                  {p.workspace_revision !== state.workspace.revision
                    ? "Historical scope; a newer workspace revision exists"
                    : "Current reviewed scope"}
                </small>
              </div>
              <a
                className="secondary compact"
                href={"/api" + path("/packages/" + p.id + "/download")}
              >
                <Download size={15} />
                Download ZIP
              </a>
              <button
                className="text-btn"
                onClick={() => {
                  setReleasePackage(p.id);
                  setAudience(
                    state.scenarios.find((s: O) => s.id === p.scenario)
                      ?.audience || "",
                  );
                }}
              >
                Record as released
              </button>
            </div>
          ))
        )}
      </section>
      {releasePackage && (
        <section className="panel">
          <h2>Record a release deliberately</h2>
          <p>
            This records local release history. It does not publish a file or
            send anything externally. The audience may retain earlier releases
            after local changes.
          </p>
          <div className="form-grid">
            <Field label="Release audience">
              <input
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
              />
            </Field>
            <Field label="Release date">
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </Field>
          </div>
          <button
            className="primary"
            disabled={busy}
            onClick={() =>
              act(async () => {
                await api(path("/releases"), "POST", {
                  package: releasePackage,
                  audience,
                  date,
                });
                setReleasePackage("");
              }, "Release history recorded. Save a new scenario to include this history in subsequent reviews.")
            }
          >
            Record release
          </button>
        </section>
      )}
      <section className="panel">
        <h2>Release history</h2>
        {!state.releases.length ? (
          <Empty title="No recorded releases">
            A download is an artifact. Record a release only when you choose to
            share it.
          </Empty>
        ) : (
          state.releases.map((r: O) => (
            <div className="rule-row" key={r.id}>
              <span className="small-icon">
                <Clock size={19} />
              </span>
              <div>
                <strong>{r.audience}</strong>
                <small>
                  {r.date} · {r.datasets.length} released versions · package{" "}
                  {r.package.slice(0, 8)}
                </small>
              </div>
              <Badge>Recorded locally</Badge>
            </div>
          ))
        )}
      </section>
    </>
  );
}

function SettingsView({
  state,
  path,
  act,
  busy,
  afterDelete,
}: {
  state: O;
  path: (p: string) => string;
  act: any;
  busy: boolean;
  afterDelete: () => void;
}) {
  const [confirm, setConfirm] = useState(""),
    [policy, setPolicy] = useState<O | null>(null),
    [answer, setAnswer] = useState("");
  useEffect(() => {
    api(path("/assistant/policy"))
      .then(setPolicy)
      .catch(() => {});
  }, []);
  return (
    <>
      <section className="panel">
        <h2>Data custody</h2>
        <div className="settings-grid">
          <div>
            <LockKeyhole />
            <h3>Encrypted artifact vault</h3>
            <p>
              Originals, derived data, exports and metadata payloads use your
              deployment key. Keep the key outside Git and back it up
              separately.
            </p>
          </div>
          <div>
            <Database />
            <h3>Sensitive graph topology</h3>
            <p>
              Workspace-scoped HMAC keys protect value matching. Tokens and
              relationships still need restricted access; tokenisation is not
              anonymisation.
            </p>
          </div>
        </div>
        <p className="muted">
          Deletion removes accessible application artifacts and graph
          projections. It cannot retract exported copies, operator backups or
          filesystem remnants.
        </p>
      </section>
      <section className="panel">
        <h2>Optional external-model assistant</h2>
        <p>
          Core review runs without a model. External mode sends selected
          aggregates to OpenAI only after you enable it for this workspace.
          Aggregates can still be sensitive.
        </p>
        {policy && (
          <>
            <Badge tone={policy.enabled ? "amber" : "teal"}>
              {policy.enabled ? "Enabled by workspace owner" : "Off by default"}
            </Badge>
            <p>{policy.policy}</p>
            <p>
              Provider: {policy.provider} · Model:{" "}
              {policy.initial_request.model} · Tool budget: {policy.tool_budget}{" "}
              · Server credential:{" "}
              {policy.configured ? "configured" : "not configured"}
            </p>
            <details>
              <summary>Review exact initial outbound request</summary>
              <pre>{JSON.stringify(policy.initial_request, null, 2)}</pre>
            </details>
            <div className="actions">
              <button
                className="secondary"
                disabled={busy || (!policy.configured && !policy.enabled)}
                onClick={() =>
                  act(async () => {
                    await api(path("/assistant/consent"), "POST", {
                      enabled: !policy.enabled,
                      preview_digest: policy.preview_digest,
                    });
                    setPolicy(await api(path("/assistant/policy")));
                  }, "Assistant privacy preference saved.")
                }
              >
                {policy.enabled
                  ? "Disable external mode"
                  : "Enable reviewed external mode"}
              </button>
              <button
                className="secondary"
                disabled={!policy.enabled || busy}
                onClick={() =>
                  act(async () => {
                    const r = await api(path("/assistant"), "POST", {
                      task: "scope",
                      external: true,
                    });
                    setAnswer(r.answer);
                    setPolicy(await api(path("/assistant/policy")));
                  }, "External assistant request completed.")
                }
              >
                Ask model to explain scope
              </button>
            </div>
            {answer && <p className="assistant-answer">{answer}</p>}
            <details>
              <summary>Inspect sanitized request history</summary>
              <pre>{JSON.stringify(policy.history, null, 2)}</pre>
            </details>
          </>
        )}
      </section>
      <section className="panel danger-panel">
        <h2>Delete this workspace</h2>
        <p>
          Cancel related jobs and remove graph projections, encrypted files,
          results and local history. Downloads are blocked as soon as deletion
          begins. Operator backups and exported copies are outside this action.
        </p>
        <Field label={"Type “" + state.workspace.name + "” to delete"}>
          <input value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </Field>
        <button
          className="danger-button"
          disabled={busy || confirm !== state.workspace.name}
          onClick={() =>
            act(async () => {
              await api("/w/" + state.workspace.id, "DELETE");
              afterDelete();
            }, "Workspace deletion queued. Its artifacts are now inaccessible.")
          }
        >
          <Trash2 size={16} />
          Delete workspace and local data
        </button>
      </section>
    </>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
