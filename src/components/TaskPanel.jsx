import { useState } from "react";

const panelStyle = {
  display: "flex",
  flexDirection: "column",
  gap: 16,
  padding: 24,
  height: "100%",
  boxSizing: "border-box",
};

const textAreaStyle = {
  width: "100%",
  minHeight: 180,
  resize: "vertical",
  boxSizing: "border-box",
  padding: 14,
  border: "1px solid #334155",
  borderRadius: 10,
  background: "#0f172a",
  color: "#e2e8f0",
  font: "inherit",
  lineHeight: 1.5,
};

export default function TaskPanel({ state, onRunTask }) {
  const [task, setTask] = useState("");
  const isRunning = state === "running";
  const canRun = task.trim().length > 0 && !isRunning;

  async function handleSubmit(event) {
    event.preventDefault();
    if (!canRun) return;
    await onRunTask(task);
  }

  return (
    <form onSubmit={handleSubmit} style={panelStyle}>
      <div>
        <p
          style={{
            margin: "0 0 8px",
            color: "#38bdf8",
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          Coding agent
        </p>
        <h1 style={{ margin: 0, color: "#f8fafc", fontSize: 22 }}>
          What should we build?
        </h1>
      </div>

      <label
        htmlFor="task-prompt"
        style={{ color: "#cbd5e1", fontSize: 14, fontWeight: 600 }}
      >
        Task description
      </label>
      <textarea
        id="task-prompt"
        value={task}
        onChange={(event) => setTask(event.target.value)}
        placeholder="Describe the change you want the agent to make..."
        disabled={isRunning}
        required
        style={{
          ...textAreaStyle,
          opacity: isRunning ? 0.7 : 1,
        }}
      />

      <button
        type="submit"
        disabled={!canRun}
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 10,
          minHeight: 44,
          padding: "0 18px",
          border: 0,
          borderRadius: 10,
          background: canRun ? "#0284c7" : "#334155",
          color: canRun ? "#fff" : "#94a3b8",
          font: "inherit",
          fontWeight: 700,
          cursor: canRun ? "pointer" : "not-allowed",
        }}
      >
        {isRunning && (
          <span
            aria-hidden="true"
            className="agent-spinner"
            style={{
              width: 15,
              height: 15,
              border: "2px solid currentColor",
              borderRightColor: "transparent",
              borderRadius: "50%",
            }}
          />
        )}
        {isRunning ? "Running task..." : "Run Task"}
      </button>
      <p style={{ margin: 0, color: "#64748b", fontSize: 12 }}>
        The agent will inspect the workspace, make changes, and run tests.
      </p>
    </form>
  );
}
