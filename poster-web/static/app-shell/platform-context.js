export function createPlatformContext(config) {
  const skillMap = new Map();
  return {
    config,
    skills: {
      registry: [],
      map: skillMap,
      register(skill) {
        if (skill && skill.id) skillMap.set(skill.id, skill);
      },
      get(id) {
        return skillMap.get(id);
      },
    },
    events: new EventTarget(),
  };
}
