import * as posterApi from "./poster-api.js";

export function registerSkill(platform, descriptor) {
  const skill = {
    id: "poster",
    label: "海报生成",
    descriptor,
    api: posterApi,
    mount() {
      window.dispatchEvent(new CustomEvent("ieg-skill-open", { detail: { id: "poster" } }));
    },
  };
  platform.skills.register(skill);
  return skill;
}
