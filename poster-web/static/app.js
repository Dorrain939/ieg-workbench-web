(async function bootPlatform() {
  const BOOT_VERSION = "20260626-restore-full-ui-1";

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.defer = true;
      s.onload = resolve;
      s.onerror = () => reject(new Error(`无法加载脚本：${src}`));
      document.head.appendChild(s);
    });
  }

  try {
    window.IEG_PLATFORM_BOOT = {
      version: BOOT_VERSION,
      mode: "full-ui-with-isolated-editor",
      legacyAdapterLoaded: true,
      startedAt: new Date().toISOString(),
    };

    await loadScript(`/static/editor-core/poster-editor-isolated.js?v=${BOOT_VERSION}`);
    const shell = await import(`/static/app-shell/main.js?v=${BOOT_VERSION}`);
    await shell.startPlatform({
      registryUrl: "/static/skills/registry.json",
      legacyAdapter: `/static/app-shell/legacy-app-adapter.js?v=${BOOT_VERSION}`,
      loadScript,
    });
  } catch (err) {
    console.error("[IEG Platform] 启动失败", err);
    const root = document.getElementById("app") || document.body;
    root.innerHTML = `<div style="padding:24px;font:14px/1.7 -apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif;color:#991b1b;background:#fff5f5;border:1px solid #fecaca;border-radius:12px;margin:24px;">平台启动失败：${String(err && err.message || err)}</div>`;
  }
})();
