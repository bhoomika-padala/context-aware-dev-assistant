import ReactMarkdown from "react-markdown";

const cardStyle = {
  padding: 22,
  border: "1px solid #1e293b",
  borderRadius: 14,
  background: "#111c2e",
};

function formatValue(value) {
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function TestResults({ results }) {
  if (results == null) return null;

  const entries = Array.isArray(results)
    ? results
    : Array.isArray(results.runs)
      ? results.runs
      : Array.isArray(results.details)
      ? results.details
      : null;
  const passed = results.passed ?? results.passed_count;
  const failed = results.failed ?? results.failed_count;
  const errors = results.errors ?? 0;

  return (
    <section aria-labelledby="test-results-title" style={cardStyle}>
      <h2
        id="test-results-title"
        style={{ margin: "0 0 14px", color: "#f8fafc", fontSize: 18 }}
      >
        Test results
      </h2>
      {(passed != null || failed != null) && (
        <p style={{ margin: "0 0 12px", color: "#cbd5e1" }}>
          <span style={{ color: "#4ade80" }}>Passed: {passed ?? 0}</span>
          {"  ·  "}
          <span style={{ color: failed ? "#f87171" : "#94a3b8" }}>
            Failed: {failed ?? 0}
          </span>
          {"  ·  "}
          <span style={{ color: errors ? "#fbbf24" : "#94a3b8" }}>
            Errors: {errors}
          </span>
          {results.total != null && `  ·  Total: ${results.total}`}
        </p>
      )}
      {entries ? (
        <ul
          style={{
            display: "grid",
            gap: 8,
            margin: 0,
            padding: 0,
            listStyle: "none",
          }}
        >
          {entries.map((entry, index) => {
            const passedTest =
              entry.status === "passed" ||
              entry.exit_code === 0 ||
              entry.passed === true ||
              entry.success === true;
            const failedTest =
              entry.status === "failed" ||
              (typeof entry.exit_code === "number" && entry.exit_code !== 0) ||
              entry.failed > 0 ||
              entry.errors > 0;
            const label = passedTest ? "PASS" : failedTest ? "FAIL" : "INFO";
            return (
              <li
                key={`${entry.name ?? entry.test ?? "test"}-${index}`}
                style={{ color: "#cbd5e1", fontSize: 14 }}
              >
                <span
                  style={{
                    marginRight: 9,
                    color: passedTest
                      ? "#4ade80"
                      : failedTest
                        ? "#f87171"
                        : "#7dd3fc",
                  }}
                >
                  {label}
                </span>
                {entry.name ??
                  entry.test ??
                  `${entry.target ?? "Test run"}: ${entry.summary ?? formatValue(entry)}`}
              </li>
            );
          })}
        </ul>
      ) : (
        <pre
          style={{
            margin: 0,
            overflowX: "auto",
            color: "#cbd5e1",
            fontSize: 13,
          }}
        >
          {formatValue(results)}
        </pre>
      )}
    </section>
  );
}

export default function ExecutionResults({
  state,
  executionTrace,
  testResults,
  summaryReport,
  finalAnswer,
  runId,
  memoryError,
  error,
}) {
  if (state === "idle") {
    return (
      <div
        style={{
          display: "grid",
          minHeight: 300,
          placeItems: "center",
          color: "#64748b",
          textAlign: "center",
        }}
      >
        <p>Your task results will appear here.</p>
      </div>
    );
  }

  if (state === "running") {
    return (
      <div role="status" style={{ color: "#cbd5e1" }}>
        The agent is working on your task...
      </div>
    );
  }

  if (state === "error") {
    return (
      <div
        role="alert"
        style={{
          ...cardStyle,
          borderColor: "#7f1d1d",
          color: "#fecaca",
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: 18 }}>Task failed</h2>
        <p style={{ marginBottom: 0 }}>{error || "An unexpected error occurred."}</p>
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <section
        aria-labelledby="summary-title"
        style={{
          ...cardStyle,
          borderColor: "#075985",
          background: "linear-gradient(135deg, #10263c, #111c2e)",
        }}
      >
        <h2
          id="summary-title"
          style={{ margin: "0 0 14px", color: "#7dd3fc", fontSize: 20 }}
        >
          Summary report
        </h2>
        {summaryReport ? (
          <div
            style={{
              color: "#e2e8f0",
              lineHeight: 1.7,
              overflowWrap: "anywhere",
            }}
          >
            <ReactMarkdown>{summaryReport}</ReactMarkdown>
          </div>
        ) : (
          <p style={{ margin: 0, color: "#94a3b8" }}>
            No summary report was returned.
          </p>
        )}
        {finalAnswer && (
          <p
            style={{
              margin: "16px 0 0",
              paddingTop: 14,
              borderTop: "1px solid #334155",
              color: "#cbd5e1",
            }}
          >
            {finalAnswer}
          </p>
        )}
        {runId && (
          <p style={{ margin: "12px 0 0", color: "#64748b", fontSize: 12 }}>
            Run ID: <code>{runId}</code>
          </p>
        )}
      </section>

      <TestResults results={testResults} />
      {memoryError && (
        <p role="status" style={{ margin: 0, color: "#fbbf24" }}>
          {memoryError}
        </p>
      )}

      <details style={cardStyle}>
        <summary
          style={{
            color: "#cbd5e1",
            cursor: "pointer",
            fontSize: 15,
            fontWeight: 700,
          }}
        >
          Execution trace ({executionTrace.length} steps)
        </summary>
        <pre
          style={{
            maxHeight: 360,
            margin: "16px 0 0",
            padding: 16,
            overflow: "auto",
            borderRadius: 10,
            background: "#020617",
            color: "#a5f3fc",
            fontFamily:
              "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            fontSize: 12,
            lineHeight: 1.6,
          }}
        >
          {JSON.stringify(executionTrace, null, 2)}
        </pre>
      </details>
    </div>
  );
}
