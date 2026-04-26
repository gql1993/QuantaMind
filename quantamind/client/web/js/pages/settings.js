(function () {
  const providerDefaults = {
    ollama: { api_base: "http://localhost:11434", model: "qwen2.5:7b" },
    deepseek: { api_base: "https://api.deepseek.com/v1", model: "deepseek-chat" },
    qwen: { api_base: "https://dashscope.aliyuncs.com/compatible-mode/v1", model: "qwen-plus" },
    openai: { api_base: "https://api.openai.com/v1", model: "gpt-4o-mini" },
    kimi: { api_base: "https://api.moonshot.cn/v1", model: "moonshot-v1-8k" },
    zhipu: { api_base: "https://open.bigmodel.cn/api/paas/v4", model: "glm-4-flash" },
    yi: { api_base: "https://api.lingyiwanwu.com/v1", model: "yi-lightning" },
  };

  async function loadLLMConfig() {
    try {
      const response = await fetch(BASE + "/api/v1/config/llm");
      const data = await response.json();
      document.getElementById("llm-provider").value = data.provider || "ollama";
      document.getElementById("llm-base").value = data.api_base || "";
      document.getElementById("llm-model").value = data.model || "";
      document.getElementById("llm-status").textContent =
        "当前：" + data.provider + " / " + data.model + " / Key: " + data.api_key;
    } catch (error) {
      console.error(error);
    }
  }

  async function saveLLMConfig() {
    const body = {
      provider: document.getElementById("llm-provider").value,
      api_base: document.getElementById("llm-base").value.trim(),
      model: document.getElementById("llm-model").value.trim(),
    };
    const key = document.getElementById("llm-key").value.trim();
    if (key) body.api_key = key;
    try {
      const response = await fetch(BASE + "/api/v1/config/llm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      document.getElementById("llm-status").textContent =
        "已保存并生效：" + data.provider + " / " + data.model;
      document.getElementById("llm-status").style.color = "var(--ok)";
      await loadLLMConfig();
    } catch (error) {
      document.getElementById("llm-status").textContent = "保存失败: " + error.message;
      document.getElementById("llm-status").style.color = "var(--danger)";
    }
  }

  function saveGatewayAddress() {
    const value = document.getElementById("set-gw").value.trim();
    if (value) {
      localStorage.setItem("quantamind_gw", value);
      location.reload();
    }
  }

  async function reprobeGatewayCapabilities() {
    const statusEl = document.getElementById("set-capability-status");
    if (statusEl) {
      statusEl.textContent = "探测中...";
      statusEl.style.color = "var(--muted)";
    }
    try {
      let capabilities = null;
      if (window.probeGatewayCapabilities) {
        capabilities = await window.probeGatewayCapabilities(true);
      }
      const mode = capabilities?.mode || "unknown";
      const modeText = mode === "native" ? "原生" : mode === "compat" ? "兼容" : "未知";
      if (statusEl) {
        statusEl.textContent = "已更新：当前模式 " + modeText;
        statusEl.style.color = mode === "native" ? "var(--ok)" : mode === "compat" ? "var(--warn)" : "var(--muted)";
      }
      if (window.showToast) window.showToast("能力探测已刷新：" + modeText, "info");
    } catch (error) {
      if (statusEl) {
        statusEl.textContent = "探测失败：" + error.message;
        statusEl.style.color = "var(--danger)";
      }
      if (window.showToast) window.showToast("能力探测失败: " + error.message, "danger");
    }
  }

  async function loadDatabaseConfigs() {
    try {
      const response = await fetch(BASE + "/api/v1/config/databases");
      const data = await response.json();
      document.getElementById("db-config-json").value = JSON.stringify(data.configs || {}, null, 2);
    } catch (error) {
      document.getElementById("db-save-status").textContent = "加载失败：" + error.message;
      document.getElementById("db-save-status").style.color = "var(--danger)";
    }
  }

  async function testDatabaseConfigs() {
    const out = document.getElementById("db-test-status");
    out.textContent = "检测中...";
    try {
      const response = await fetch(BASE + "/api/v1/config/databases/status");
      const data = await response.json();
      const statuses = data.statuses || {};
      const lines = Object.entries(statuses).map(([key, value]) => {
        const ok = value.connected;
        return `${ok ? "[已连接]" : "[未连接]"} ${value.label || key} - ${value.detail || ""}`;
      });
      out.innerHTML = lines.join("<br>");
      out.style.color = "var(--muted)";
    } catch (error) {
      out.textContent = "检测失败：" + error.message;
      out.style.color = "var(--danger)";
    }
  }

  async function saveDatabaseConfigs() {
    const statusEl = document.getElementById("db-save-status");
    try {
      const parsed = JSON.parse(document.getElementById("db-config-json").value || "{}");
      const response = await fetch(BASE + "/api/v1/config/databases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ configs: parsed }),
      });
      const data = await response.json();
      document.getElementById("db-config-json").value = JSON.stringify(data.configs || parsed, null, 2);
      statusEl.textContent = "数据库连接配置已保存";
      statusEl.style.color = "var(--ok)";
      await testDatabaseConfigs();
    } catch (error) {
      statusEl.textContent = "保存失败：" + error.message;
      statusEl.style.color = "var(--danger)";
    }
  }

  document.getElementById("llm-provider").addEventListener("change", function () {
    const defaults = providerDefaults[this.value] || {};
    document.getElementById("llm-base").value = defaults.api_base || "";
    document.getElementById("llm-model").value = defaults.model || "";
  });
  document.getElementById("llm-save").addEventListener("click", saveLLMConfig);

  document.getElementById("set-gw").value = BASE;
  document.getElementById("set-save").addEventListener("click", saveGatewayAddress);
  document.getElementById("set-probe-capability")?.addEventListener("click", reprobeGatewayCapabilities);

  async function loadIntelConfig() {
    const hint = document.getElementById("intel-webhook-hint");
    const nextEl = document.getElementById("intel-next-run");
    const statusEl = document.getElementById("intel-status");
    try {
      const response = await fetch(BASE + "/api/v1/config/intel", { cache: "no-store" });
      const data = await response.json();
      document.getElementById("intel-schedule-hour").value = String(data.intel_schedule_hour ?? 9);
      document.getElementById("intel-schedule-minute").value = String(data.intel_schedule_minute ?? 0);
      document.getElementById("intel-feishu-webhook").value = "";
      if (hint) {
        hint.textContent = data.intel_feishu_webhook_configured
          ? "已保存 Webhook：" + (data.intel_feishu_webhook_preview || "（已配置）") + " — 留空保存则不变更；填写新地址可替换。"
          : "尚未配置 Webhook，推送将被跳过。请粘贴飞书群机器人的 Webhook 完整地址。";
      }
      if (nextEl) {
        nextEl.textContent = data.next_intel_run
          ? "预计下次定时执行（UTC 时间戳）：" + data.next_intel_run
          : "下次执行时间将在心跳调度初始化后显示；请保存配置并刷新页面。";
      }
      if (statusEl) statusEl.textContent = "";
    } catch (error) {
      if (hint) hint.textContent = "加载失败：" + error.message;
    }
  }

  async function saveIntelConfig() {
    const statusEl = document.getElementById("intel-status");
    const wh = document.getElementById("intel-feishu-webhook").value.trim();
    const hour = parseInt(document.getElementById("intel-schedule-hour").value, 10);
    const minute = parseInt(document.getElementById("intel-schedule-minute").value, 10);
    const body = {
      intel_schedule_hour: Number.isFinite(hour) ? Math.max(0, Math.min(23, hour)) : 9,
      intel_schedule_minute: Number.isFinite(minute) ? Math.max(0, Math.min(59, minute)) : 0,
    };
    if (wh) body.intel_feishu_webhook = wh;
    try {
      statusEl.textContent = "保存中…";
      statusEl.style.color = "var(--muted)";
      const response = await fetch(BASE + "/api/v1/config/intel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "保存失败");
      statusEl.textContent = "已保存。飞书：" + (data.intel_feishu_webhook_configured ? "已配置" : "未配置");
      statusEl.style.color = "var(--ok)";
      document.getElementById("intel-feishu-webhook").value = "";
      await loadIntelConfig();
    } catch (error) {
      statusEl.textContent = "保存失败：" + error.message;
      statusEl.style.color = "var(--danger)";
    }
  }

  document.getElementById("intel-save").addEventListener("click", saveIntelConfig);

  document.getElementById("db-load").addEventListener("click", loadDatabaseConfigs);
  document.getElementById("db-test").addEventListener("click", testDatabaseConfigs);
  document
    .getElementById("db-recover-store")
    .addEventListener("click", () => window.recoverStateStore("db-save-status"));
  document
    .getElementById("dbg-recover-store")
    .addEventListener("click", () => window.recoverStateStore("dbg-recover-status"));
  document.getElementById("db-save").addEventListener("click", saveDatabaseConfigs);

  let settingsLoaded = false;
  async function loadSettingsPage() {
    if (settingsLoaded) return;
    settingsLoaded = true;
    if (window.probeGatewayCapabilities) await window.probeGatewayCapabilities();
    const statusEl = document.getElementById("set-capability-status");
    if (statusEl && window.getGatewayCapabilities) {
      const mode = window.getGatewayCapabilities()?.mode || "unknown";
      const modeText = mode === "native" ? "原生" : mode === "compat" ? "兼容" : "未知";
      statusEl.textContent = "当前模式：" + modeText;
      statusEl.style.color = mode === "native" ? "var(--ok)" : mode === "compat" ? "var(--warn)" : "var(--muted)";
    }
    await loadLLMConfig();
    await loadIntelConfig();
    await loadDatabaseConfigs();
  }
  window.addEventListener("quantamind:pagechange", (event) => {
    if (event.detail && event.detail.page === "settings") loadSettingsPage();
  });
  if (!window.isPageActive || window.isPageActive("settings")) loadSettingsPage();

  window.loadLLMConfig = loadLLMConfig;
  window.loadIntelConfig = loadIntelConfig;
  window.loadDatabaseConfigs = loadDatabaseConfigs;
  window.loadSettingsPage = loadSettingsPage;
  window.testDatabaseConfigs = testDatabaseConfigs;
  window.reprobeGatewayCapabilities = reprobeGatewayCapabilities;
})();
