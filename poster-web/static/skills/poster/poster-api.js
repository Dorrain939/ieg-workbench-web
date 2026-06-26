import { apiFetch } from "../../shared/api-client.js";

export const listPosterProjects = (projectId) => apiFetch(`/api/projects/${projectId}/function-projects/poster_brief`);
export const savePosterProject = (projectId, itemId, payload) => apiFetch(`/api/projects/${projectId}/function-projects/poster_brief/${itemId}`, {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
export const runPosterSkill = (payload) => apiFetch("/api/skills/poster_render/run", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});
