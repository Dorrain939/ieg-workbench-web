export async function apiFetch(path, options = {}) {
  const res = await fetch(path, options);
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    const message = data && (data.detail || data.error) ? (data.detail || data.error) : `HTTP ${res.status}`;
    throw new Error(message);
  }
  return data;
}
