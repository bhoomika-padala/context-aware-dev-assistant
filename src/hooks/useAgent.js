import { useCallback, useState } from "react";

import { executeTask } from "../api/client";

const initialResult = {
  executionTrace: [],
  testResults: null,
  summaryReport: "",
  finalAnswer: "",
  runId: null,
  memoryError: null,
};

export function useAgent() {
  const [state, setState] = useState("idle");
  const [result, setResult] = useState(initialResult);
  const [error, setError] = useState("");

  const runTask = useCallback(async (task, useMemory = true) => {
    setState("running");
    setResult(initialResult);
    setError("");

    try {
      const response = await executeTask(task, useMemory);
      setResult({
        executionTrace: Array.isArray(response.execution_trace)
          ? response.execution_trace
          : [],
        testResults: response.test_results ?? null,
        summaryReport:
          typeof response.summary_report === "string"
            ? response.summary_report
            : "",
        finalAnswer:
          typeof response.final_answer === "string"
            ? response.final_answer
            : "",
        runId: response.run_id ?? null,
        memoryError: response.memory_error ?? null,
      });
      setState("success");
      return response;
    } catch (caughtError) {
      const message =
        caughtError instanceof Error
          ? caughtError.message
          : "An unexpected error occurred while running the task.";
      setError(message);
      setState("error");
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState("idle");
    setResult(initialResult);
    setError("");
  }, []);

  return {
    state,
    ...result,
    error,
    runTask,
    reset,
  };
}
