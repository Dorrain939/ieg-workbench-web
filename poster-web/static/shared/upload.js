export async function uploadFile(file, { sessionId = "default", assetType = "module_content_image", assetLabel = "" } = {}) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("session_id", sessionId);
  fd.append("asset_type", assetType);
  fd.append("asset_label", assetLabel);
  const res = await fetch("/api/upload", { method: "POST", body: fd });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || data.detail || `HTTP ${res.status}`);
  return data;
}
