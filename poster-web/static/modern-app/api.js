export async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: options.body instanceof FormData ? undefined : { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = { raw: text }; }
  if (!res.ok) {
    const msg = data?.detail || data?.error || data?.message || `HTTP ${res.status}`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
}

export const Projects = {
  list: () => api("/api/projects"),
  get: (pid) => api(`/api/projects/${encodeURIComponent(pid)}`),
  create: (payload) => api("/api/projects", { method: "POST", body: JSON.stringify(payload) }),
  update: (pid, payload) => api(`/api/projects/${encodeURIComponent(pid)}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (pid) => api(`/api/projects/${encodeURIComponent(pid)}`, { method: "DELETE" }),
};

export const Covers = {
  generate: (payload) => api("/api/covers/generate", { method: "POST", body: JSON.stringify(payload) }),
};

export const FunctionProjects = {
  list: (pid, functionId) => api(`/api/projects/${encodeURIComponent(pid)}/function-projects/${encodeURIComponent(functionId)}`),
  create: (pid, functionId, payload) => api(`/api/projects/${encodeURIComponent(pid)}/function-projects/${encodeURIComponent(functionId)}`, { method: "POST", body: JSON.stringify(payload) }),
  update: (pid, functionId, itemId, payload) => api(`/api/projects/${encodeURIComponent(pid)}/function-projects/${encodeURIComponent(functionId)}/${encodeURIComponent(itemId)}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (pid, functionId, itemId) => api(`/api/projects/${encodeURIComponent(pid)}/function-projects/${encodeURIComponent(functionId)}/${encodeURIComponent(itemId)}`, { method: "DELETE" }),
};

export async function uploadAsset(file, sessionId, assetType = "module_content_image", assetLabel = "正文内嵌图片") {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("session_id", sessionId || "default");
  fd.append("asset_type", assetType);
  fd.append("asset_label", assetLabel);
  return api("/api/upload", { method: "POST", body: fd });
}

export async function savePosterArtifact(pid, brief) {
  return api(`/api/projects/${encodeURIComponent(pid)}/save-as-artifact`, {
    method: "POST",
    body: JSON.stringify({ brief }),
  });
}

export function artifactFileUrl(pid, artifactId, name = "poster.png") {
  return `/api/projects/${encodeURIComponent(pid)}/artifacts/${encodeURIComponent(artifactId)}/file?name=${encodeURIComponent(name)}`;
}
