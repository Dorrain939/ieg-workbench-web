export function serializeEditorJson(editor) {
  return {
    editor_json: editor.getJSON(),
    content_html: editor.getHTML(),
    content: editor.getText("\n"),
  };
}

export function plainTextFromEditorJson(json) {
  const out = [];
  function walk(node) {
    if (!node || typeof node !== "object") return;
    if (node.type === "text") out.push(node.text || "");
    if (node.type === "hardBreak") out.push("\n");
    if (node.type === "posterImage" || node.type === "image") out.push("[图片]");
    (node.content || []).forEach(walk);
    if (node.type === "paragraph") out.push("\n");
  }
  walk(json);
  return out.join("").replace(/\n{3,}/g, "\n\n").trim();
}
