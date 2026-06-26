export function applyEditorCommand(editor, command, value) {
  if (!editor) return false;
  const chain = editor.chain().focus();
  if (command === "bold") return chain.toggleBold().run();
  if (command === "italic") return chain.toggleItalic().run();
  if (command === "underline") return chain.toggleUnderline().run();
  if (command === "color") return chain.setColor(value).run();
  if (command === "highlight") return chain.setHighlight({ color: value }).run();
  if (command === "align") return chain.setTextAlign(value).run();
  return false;
}
