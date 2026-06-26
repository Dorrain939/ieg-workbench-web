import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../../static");
for (const file of [
  "app.js",
  "app-shell/main.js",
  "editor-core/index.js",
  "skills/registry.json",
  "skills/poster/index.js",
]) {
  if (!fs.existsSync(path.join(root, file))) {
    throw new Error(`missing ${file}`);
  }
}
JSON.parse(fs.readFileSync(path.join(root, "skills/registry.json"), "utf8"));
console.log("frontend smoke ok");
