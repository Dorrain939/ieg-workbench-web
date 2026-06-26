import { loadSkillRegistry, loadSkillEntry } from "./skill-loader.js";
import { createPlatformContext } from "./platform-context.js";
import { APP_CONFIG } from "./app-config.js";

export async function startPlatform({ registryUrl, legacyAdapter, loadScript }) {
  const context = createPlatformContext(APP_CONFIG);
  window.IEG_PLATFORM = context;

  const registry = await loadSkillRegistry(registryUrl);
  context.skills.registry = registry;

  for (const skill of registry) {
    await loadSkillEntry(skill, context);
  }

  await loadScript(legacyAdapter);
  window.dispatchEvent(new CustomEvent("ieg-platform-ready", { detail: context }));
}
