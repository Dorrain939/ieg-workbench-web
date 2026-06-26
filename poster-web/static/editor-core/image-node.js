export function createPosterImageNode(T) {
  return T.Node.create({
    name: "posterImage",
    group: "block",
    atom: true,
    selectable: true,
    draggable: true,
    attrs: {
      src: { default: "" },
      path: { default: "" },
      alt: { default: "" },
      widthPct: { default: 0.55 },
      align: { default: "center" },
    },
    parseHTML() {
      return [{ tag: 'div[data-type="poster-image"]' }, { tag: "img[data-asset-path]" }];
    },
    renderHTML({ node }) {
      const a = node.attrs || {};
      return ["div", {
        "data-type": "poster-image",
        "data-asset-path": a.path || "",
        "data-width-pct": a.widthPct || 0.55,
        "data-align": a.align || "center",
        style: `width:${Math.round((Number(a.widthPct) || 0.55) * 100)}%;margin-left:${a.align === "left" ? "0" : "auto"};margin-right:${a.align === "right" ? "0" : "auto"}`,
      }, ["img", { src: a.src || "", alt: a.alt || "", "data-asset-path": a.path || "" }]];
    },
  });
}
