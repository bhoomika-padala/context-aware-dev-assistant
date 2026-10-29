const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

function responseError(payload, status) {
  if (typeof payload?.detail === "string") return payload.detail;
  if (Array.isArray(payload?.detail)) {
    return payload.detail
      .map((issue) => issue.msg)
      .filter((message) => typeof message === "string")
      .join("; ");
  }
  if (typeof payload?.error === "string") return payload.error;
  return `Task execution failed with status ${status}.`;
}

export async function executeTask(taskStr, useMemory = true ) {
  if (typeof taskStr !== "string" || !taskStr.trim()) {
    throw new TypeError("Task must be a non-empty string.");
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/execute`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
      task: taskStr.trim(),
      use_memory: useMemory,}),
    });
  } catch (error) {
    throw new Error("Could not connect to the coding agent API.", {
      cause: error,
    });
  }

  let payload;
  try {
    payload = await response.json();
  } catch (error) {
    throw new Error("The coding agent API returned an invalid response.", {
      cause: error,
    });
  }

  if (!response.ok) {
    throw new Error(responseError(payload, response.status));
  }

  if (!payload || typeof payload !== "object") {
    throw new Error("The coding agent API returned an invalid response.");
  }

  return payload;
}
