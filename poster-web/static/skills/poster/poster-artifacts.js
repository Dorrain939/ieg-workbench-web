export function artifactDownloadUrl(artifact, file) {
  return artifact && artifact.path ? `/api/projects/${artifact.project_id || ""}/artifacts/${artifact.id}/${file}` : "";
}
