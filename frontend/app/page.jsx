"use client";

import { useRef, useState } from "react";
import dynamic from "next/dynamic";
import { marked } from "marked";

const StlViewer = dynamic(() => import("../components/StlViewer"), { ssr: false });

const DEMO_PROMPT =
  "Design a mobile robot that can inspect manufacturing equipment for 8 hours.";

const KIND_CLS = {
  stage: "ok",
  iteration: "run",
  iteration_ok: "ok",
  iteration_result: "err",
  iteration_failed: "err",
};

export default function Home() {
  const [prompt, setPrompt] = useState(DEMO_PROMPT);
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState([]);
  const [designId, setDesignId] = useState(null);
  const [artifacts, setArtifacts] = useState([]);
  const [reportHtml, setReportHtml] = useState("");
  const [provenance, setProvenance] = useState(null);
  const [tab, setTab] = useState("model");
  const pollRef = useRef(null);

  const pushLog = (text, cls) => setLog((prev) => [...prev, { text, cls }]);

  async function finishRun(id) {
    try {
      const man = await (await fetch(`/api/v1/designs/${id}`)).json();
      setArtifacts(man.artifacts);
      (man.notes || []).forEach((n) =>
        pushLog(n, /FAILED|CRITICAL|HIGH:|NOT converged/.test(n) ? "err" : "ok"));
      const rep = await fetch(`/api/v1/designs/${id}/report`);
      setReportHtml(marked.parse(await rep.text()));
      const prov = await fetch(`/api/v1/designs/${id}/artifacts/provenance.json`);
      if (prov.ok) setProvenance(await prov.json());
    } catch (err) {
      pushLog(`Failed loading results: ${err.message}`, "err");
    }
  }

  async function runDesign() {
    setRunning(true);
    setDesignId(null);
    setArtifacts([]);
    setReportHtml("");
    setProvenance(null);
    setLog([{ text: "Submitting design request…", cls: "run" }]);
    try {
      const res = await fetch("/api/v1/designs/async", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      if (!res.ok) throw new Error(`backend returned ${res.status}`);
      const { design_id } = await res.json();
      setDesignId(design_id);
      let seen = 0;

      pollRef.current = setInterval(async () => {
        try {
          const st = await fetch(`/api/v1/designs/${design_id}/status`);
          if (!st.ok) return;
          const status = await st.json();
          const events = status.events.slice(seen);
          seen = status.events.length;
          events.forEach((e) => pushLog(e.message, KIND_CLS[e.kind] || "ok"));
          if (status.state !== "running") {
            clearInterval(pollRef.current);
            if (status.state === "failed") {
              pushLog(`Pipeline failed: ${status.error}`, "err");
            } else {
              await finishRun(design_id);
            }
            setRunning(false);
          }
        } catch {
          /* transient poll failure — keep polling */
        }
      }, 1500);
    } catch (err) {
      pushLog(`Failed: ${err.message}. Is the backend running?`, "err");
      setRunning(false);
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Agentic Mechanical Engineer</h1>
        <p>
          Type one sentence. The AI designs it, simulates it, and iterates until
          the engineering checks pass — requirements, CAD, physics, risks, BOM, report.
        </p>
      </header>

      <div className="prompt-row">
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !running && runDesign()}
          placeholder="Describe the machine or part you need…"
        />
        <button onClick={runDesign} disabled={running || prompt.length < 10}>
          {running ? "Designing…" : "Run design"}
        </button>
      </div>

      <div className="grid">
        <div>
          <div className="panel">
            <h2>Live status</h2>
            {log.length === 0 ? (
              <div className="empty">Idle — run a design.</div>
            ) : (
              <ul className="status-log">
                {log.map((e, i) => (
                  <li key={i} className={e.cls}>{e.text}</li>
                ))}
              </ul>
            )}
          </div>

          <div className="panel">
            <h2>Artifacts</h2>
            {artifacts.length === 0 ? (
              <div className="empty">No artifacts yet.</div>
            ) : (
              <ul className="artifact-list">
                {artifacts.map((a) => (
                  <li key={a.name}>
                    <a href={`/api/v1/designs/${designId}/artifacts/${a.name}`}>
                      {a.name}
                    </a>
                    <span className="kind">{a.kind}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="panel">
            <h2>Provenance</h2>
            {!provenance ? (
              <div className="empty">Model/token ledger appears after a run.</div>
            ) : (
              <div>
                <table className="prov-table">
                  <thead>
                    <tr><th>Stage</th><th>Model</th><th>Tokens in/out</th></tr>
                  </thead>
                  <tbody>
                    {provenance.llm_calls.map((c, i) => (
                      <tr key={i}>
                        <td>{c.purpose}</td>
                        <td title={c.endpoint}>{c.provider}: {c.model.split("/").pop()}</td>
                        <td>{c.prompt_tokens ?? "?"} / {c.completion_tokens ?? "?"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="prov-note">
                  {provenance.totals.calls} LLM call(s),{" "}
                  {provenance.totals.prompt_tokens}/{provenance.totals.completion_tokens}{" "}
                  tokens. Deterministic stages: {provenance.deterministic_stages.join(", ")}.
                </p>
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="tabs">
            <button className={tab === "model" ? "active" : ""} onClick={() => setTab("model")}>
              3D Model
            </button>
            <button className={tab === "report" ? "active" : ""} onClick={() => setTab("report")}>
              Report
            </button>
          </div>

          {tab === "model" &&
            (designId && artifacts.some((a) => a.kind === "stl") ? (
              <StlViewer url={`/api/v1/designs/${designId}/model`} />
            ) : (
              <div className="panel empty">
                {running ? "Designing — the model appears when the run completes…"
                         : "Run a design to view it here."}
              </div>
            ))}

          {tab === "report" &&
            (reportHtml ? (
              <div className="panel report" dangerouslySetInnerHTML={{ __html: reportHtml }} />
            ) : (
              <div className="panel empty">The engineering report will appear here.</div>
            ))}
        </div>
      </div>

      <footer>
        Concept-level engineering output — not certified analysis. Review by a
        qualified engineer required before fabrication.
      </footer>
    </div>
  );
}
