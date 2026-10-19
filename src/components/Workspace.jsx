import { useAgent } from "../hooks/useAgent";
import ExecutionResults from "./ExecutionResults";
import TaskPanel from "./TaskPanel";

export default function Workspace() {
  const agent = useAgent();

  return (
    <main
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(270px, 340px) minmax(0, 1fr)",
        minHeight: "100vh",
        background: "#020617",
        color: "#e2e8f0",
        fontFamily:
          "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
      }}
    >
      <aside
        style={{
          borderRight: "1px solid #1e293b",
          background: "#0b1220",
        }}
      >
        <TaskPanel state={agent.state} onRunTask={agent.runTask} />
      </aside>

      <section
        aria-label="Task results"
        style={{
          minWidth: 0,
          padding: "32px clamp(20px, 5vw, 64px)",
        }}
      >
        <div style={{ width: "100%", maxWidth: 1000, margin: "0 auto" }}>
          <ExecutionResults
            state={agent.state}
            executionTrace={agent.executionTrace}
            testResults={agent.testResults}
            summaryReport={agent.summaryReport}
            finalAnswer={agent.finalAnswer}
            runId={agent.runId}
            error={agent.error}
          />
        </div>
      </section>

      <style>{`
        @keyframes agent-spin {
          to { transform: rotate(360deg); }
        }
        .agent-spinner {
          animation: agent-spin 0.8s linear infinite;
        }
        @media (max-width: 760px) {
          main {
            grid-template-columns: 1fr !important;
          }
          main aside {
            border-right: 0 !important;
            border-bottom: 1px solid #1e293b;
          }
        }
      `}</style>
    </main>
  );
}
