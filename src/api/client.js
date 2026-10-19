const API_BASE_URL = "http://localhost:8080";
export async function executeTask(taskStr) {
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
      body: JSON.stringify({ task: taskStr.trim() }),
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
    const message =
      typeof payload.detail === "string"
        ? payload.detail
        : typeof payload.error === "string"
          ? payload.error
          : `Task execution failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload;
}
