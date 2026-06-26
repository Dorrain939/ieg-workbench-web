export async function loadSkillRegistry(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Skill registry 加载失败：HTTP ${res.status}`);
  const registry = await res.json();
  if (!Array.isArray(registry)) throw new Error("Skill registry 必须是数组");
  return registry;
}

export async function loadSkillEntry(skill, context) {
  if (!skill || !skill.entry) return null;
  const mod = await import(`${skill.entry}?v=${context.config.version}`);
  if (typeof mod.registerSkill === "function") {
    return mod.registerSkill(context, skill);
  }
  return mod;
}
