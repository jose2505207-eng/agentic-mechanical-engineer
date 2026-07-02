"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { marked } from "marked";

const StlViewer = dynamic(() => import("../components/StlViewer"), { ssr: false });

const DEMO_PROMPT =
  "Design a mobile robot that can inspect manufacturing equipment for 8 hours.";

export default function Home() {
  const [prompt, setPrompt] = useState(DEMO_PROMPT);
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState([]);
  const [designId, setDesignId] = useState(null);
  const [artifacts, setArtifacts] = useState([]);
  const [reportHtml, setReportHtml] = useState("");
  const [tab, setTab] = useState("model");

  const pushLog = (text, cls) =>
    setLog((prev) => [...prev.filter((e) => e.cls !== "run"), { text, cls }]);

  async function runDesign() {
    setRunning(true);
    setDesignId(null);
    setArtifacts([]);
    setReportHtml("");
    setLog([{ text: "Running pipeline… (about a minute when an LLM provider is configured)", cls: "run" }]);
    try {
      const res = await fetch("/api/v1/designs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      if (!res.ok) throw new Error(`pipeline returned ${res.status}`);
      const data = await res.json();
      pushLog(`Pipeline complete — ${data.design_id}`, "ok");

      setDesignId(data.design_id);
      setArtifacts(data.manifest.artifacts);
      pushLog(`${data.manifest.artifacts.length} artifacts generated`, "ok");

      const rep = await fetch(`/api/v1/designs/${data.design_id}/report`);
      setReportHtml(marked.parse(await rep.text()));
      pushLog("Engineering report loaded", "ok");
      (data.manifest.notes || []).forEach((n) =>
        pushLog(n, /FAILED|CRITICAL|HIGH:/.test(n) ? "err" : "ok"));
    } catch (err) {
      pushLog(`Failed: ${err.message}. Is the backend running? (make api)`, "err");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Agentic Mechanical Engineer</h1>
        <p>
          Type one sentence. Get an engineering package — requirements,
          architecture, CAD, checks, risks, BOM, report.
        </p>
      </header>

      <div className="prompt-row">
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !running && runDesign()}
          placeholder="Describe the machine you need…"
        />
        <button onClick={runDesign} disabled={running || prompt.length < 10}>
          {running ? "Running…" : "Run design"}
        </button>
      </div>

      <div className="grid">
        <div>
          <div className="panel">
            <h2>Status</h2>
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
                    {a.name === "robot_chassis.stl" ? (
                      <a href={`/api/v1/designs/${designId}/model`}>{a.name}</a>
                    ) : (
                      <span>{a.name}</span>
                    )}
                    <span className="kind">{a.kind}</span>
                  </li>
                ))}
              </ul>
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
            (designId ? (
              <StlViewer url={`/api/v1/designs/${designId}/model`} />
            ) : (
              <div className="panel empty">Run a design to view its chassis here.</div>
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
