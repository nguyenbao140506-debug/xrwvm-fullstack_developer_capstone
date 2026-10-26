const API_PREFIX = "/djangoapp";

async function readResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : {};
  if (!response.ok) {
    const validation = data.errors ? Object.values(data.errors).flat().join(" ") : "";
    throw new Error(validation || data.detail || data.message || ("Request failed (" + response.status + ")."));
  }
  return data;
}

export async function getCsrfToken() {
  const response = await fetch(API_PREFIX + "/csrf", {
    method: "GET",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  const data = await readResponse(response);
  return data.csrfToken;
}

export async function apiRequest(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = { Accept: "application/json", ...(options.headers || {}) };
  const init = { ...options, method, headers, credentials: "include" };
  if (options.body && typeof options.body !== "string") {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.body);
  }
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers["X-CSRFToken"] = await getCsrfToken();
  }
  return readResponse(await fetch(API_PREFIX + "/" + path, init));
}

export const apiGet = (path) => apiRequest(path);
export const apiPost = (path, body = {}) => apiRequest(path, { method: "POST", body });
