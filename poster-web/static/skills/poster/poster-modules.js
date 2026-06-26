export function normalizePosterModule(module) {
  module.module_config = module.module_config || {};
  return module;
}
