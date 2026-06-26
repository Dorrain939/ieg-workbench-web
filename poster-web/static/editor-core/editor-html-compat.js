export function legacyHtmlToEditorJson(html = "", fallbackText = "") {
  const text = fallbackText || String(html).replace(/<br\s*\/?>/gi, "\n").replace(/<[^>]+>/g, "");
  return {
    type: "doc",
    content: String(text || "").split(/\n+/).filter(Boolean).map(line => ({
      type: "paragraph",
      content: [{ type: "text", text: line }],
    })),
  };
}
