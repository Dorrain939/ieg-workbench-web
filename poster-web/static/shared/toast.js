export function toast(message, type = "info") {
  window.dispatchEvent(new CustomEvent("ieg-toast", { detail: { message, type } }));
}
