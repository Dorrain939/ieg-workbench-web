export function clamp(value, min, max) {
  return Math.max(min, Math.min(max, Number(value)));
}

export function safeArray(value) {
  return Array.isArray(value) ? value : [];
}
