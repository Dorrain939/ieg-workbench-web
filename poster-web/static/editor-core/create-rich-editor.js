import { createPosterImageNode } from "./image-node.js";

export async function createRichEditor({ element, content, extensions = [], onUpdate } = {}) {
  const T = await (window.TIPTAP_READY || Promise.resolve(window.TIPTAP));
  if (!T || !T.Editor) throw new Error("TipTap runtime 未加载");
  return new T.Editor({
    element,
    extensions: [
      T.StarterKit,
      T.Underline,
      T.TextStyle,
      T.Color.configure({ types: ["textStyle"] }),
      T.Highlight.configure({ multicolor: true }),
      T.TextAlign.configure({ types: ["heading", "paragraph"] }),
      createPosterImageNode(T),
      ...extensions,
    ],
    content: content || { type: "doc", content: [{ type: "paragraph" }] },
    onUpdate,
  });
}
