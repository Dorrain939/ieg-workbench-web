export function createRouter() {
  return {
    go(hash) {
      window.location.hash = hash || "";
    },
    current() {
      return window.location.hash || "";
    },
  };
}
