(function () {
  var BASE = localStorage.getItem("quantamind_gw") || location.origin;
  window.BASE = BASE;
  window.curSession = window.curSession || null;
  window._degradedToastShown = false;
  window.resetDegradedToast = function () {
    window._degradedToastShown = false;
  };
  var gatewayCapabilities = {
    loaded: false,
    mode: "unknown",
    available: {},
    missing: [],
    source: "",
    error: "",
    probedAt: "",
  };
  var gatewayCapabilityPromise = null;

  var GATEWAY_CAPABILITY_PATHS = {
    console_runs: { path: "/api/v2/console/runs", method: "get" },
    task_shortcut_bg: { path: "/api/v2/tasks/shortcuts/{shortcut_name}", method: "post" },
    tasks_center: { path: "/api/v2/tasks", method: "get" },
    approvals_list: { path: "/api/v2/approvals", method: "get" },
    approvals_create: { path: "/api/v2/approvals", method: "post" },
    approvals_approve: { path: "/api/v2/approvals/{approval_id}/approve", method: "post" },
    approvals_reject: { path: "/api/v2/approvals/{approval_id}/reject", method: "post" },
    artifact_view: { path: "/api/v2/artifacts/{artifact_id}/view", method: "get" },
  };
  var GATEWAY_CAPABILITY_GROUPS = {
    run_console: ["console_runs"],
    shortcut_background: ["task_shortcut_bg"],
    task_center: ["tasks_center"],
    approvals: ["approvals_list", "approvals_create", "approvals_approve", "approvals_reject"],
    artifact_viewer: ["artifact_view"],
  };

  function showToast(msg, type, duration) {
    const toastType = type || "info";
    const toastDuration = duration || 3000;
    const toast = document.createElement("div");
    toast.className = "toast " + toastType;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity .3s";
      setTimeout(() => toast.remove(), 300);
    }, toastDuration);
  }

  function isPageActive(pageName) {
    const page = document.getElementById("page-" + pageName);
    return !!(page && page.classList.contains("active") && !document.hidden);
  }

  function goToPage(pageName) {
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
    const nav = document.querySelector('[data-page="' + pageName + '"]');
    if (nav) nav.classList.add("active");
    document.querySelectorAll(".page").forEach((page) => page.classList.remove("active"));
    const pg = document.getElementById("page-" + pageName);
    if (pg) pg.classList.add("active");

    const loaders = {
      overview: () => window.refreshDash && window.refreshDash(),
      tasks: () => window.loadTasks && window.loadTasks(),
      "run-console": () => window.loadRunConsole && window.loadRunConsole(),
      approvals: () => window.loadApprovalsPage && window.loadApprovalsPage(),
      "task-center": () => window.loadTaskCenterPage && window.loadTaskCenterPage(),
      "artifact-viewer": () => window.loadArtifactViewerPage && window.loadArtifactViewerPage(),
      discovery: () => window.loadDiscoveries && window.loadDiscoveries(),
      agents: () => window.loadAgents && window.loadAgents(),
      sessions: () => window.loadSessions && window.loadSessions(),
      logs: () => window.loadLogs && window.loadLogs(),
      debug: () => window.loadDebug && window.loadDebug(),
      pipeline: () => {
        if (window.loadPipelineHistory) window.loadPipelineHistory();
        if (window.currentPipelineId && window.pollPipeline) window.pollPipeline();
      },
      datahub: () => window.loadDataHub && window.loadDataHub(),
      library: () => window.loadLibrary && window.loadLibrary(),
      "tool-detail": () => window.renderToolDetailPage && window.renderToolDetailPage(),
      "skill-detail": () => window.renderSkillDetailPage && window.renderSkillDetailPage(),
    };
    if (loaders[pageName]) loaders[pageName]();
    window.dispatchEvent(new CustomEvent("quantamind:pagechange", { detail: { page: pageName } }));
  }

  function showModal(title, content) {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML =
      '<div class="modal"><div class="modal-title"><span>' +
      title +
      '</span><span class="modal-close" title="关闭">&times;</span></div><div class="modal-body">' +
      content +
      "</div></div>";
    overlay.querySelector(".modal-close").addEventListener("click", () => overlay.remove());
    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) overlay.remove();
    });
    document.body.appendChild(overlay);
  }

  function scrollToNavGroup(groupName) {
    var groupId = null;
    if (groupName === "capability") groupId = "nav-group-capability";
    else if (groupName === "operations") groupId = "nav-group-operations";
    if (!groupId) return false;
    var el = document.getElementById(groupId);
    if (!el) return false;
    if (typeof el.scrollIntoView === "function") {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    return true;
  }

  function _resolveCapabilityFromOpenApi(openapi) {
    var paths = (openapi && openapi.paths) || {};
    var available = {};
    var missing = [];
    Object.keys(GATEWAY_CAPABILITY_PATHS).forEach(function (name) {
      var spec = GATEWAY_CAPABILITY_PATHS[name];
      var pathItem = paths[spec.path] || null;
      var ok = !!(pathItem && pathItem[spec.method]);
      available[name] = ok;
      if (!ok) missing.push(name);
    });
    var mode = missing.length === 0 ? "native" : "compat";
    return { available: available, missing: missing, mode: mode };
  }

  function _setTopbarGatewayCapability() {
    var el = document.getElementById("gw-capability-mode");
    if (!el) return;
    var mode = gatewayCapabilities.mode || "unknown";
    var badgeClass = "pending";
    var text = "能力模式：未知";
    if (mode === "native") {
      badgeClass = "completed";
      text = "能力模式：原生";
    } else if (mode === "compat") {
      badgeClass = "pending";
      text = "能力模式：兼容";
    }
    el.className = "badge " + badgeClass;
    el.textContent = text;
    var title = "探测来源: " + (gatewayCapabilities.source || "none");
    if (gatewayCapabilities.missing && gatewayCapabilities.missing.length) {
      title += " | 缺失: " + gatewayCapabilities.missing.join(", ");
    }
    if (gatewayCapabilities.error) {
      title += " | error: " + gatewayCapabilities.error;
    }
    el.title = title;
  }

  function _escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function showGatewayCapabilityDetails() {
    var cap = gatewayCapabilities || {};
    var rows = Object.keys(GATEWAY_CAPABILITY_PATHS).map(function (name) {
      var spec = GATEWAY_CAPABILITY_PATHS[name];
      var ok = cap.available && cap.available[name] === true;
      var status = ok ? "已支持" : "缺失";
      var color = ok ? "var(--ok)" : "var(--warn)";
      return (
        '<div class="modal-row">' +
        '<div class="modal-label">' +
        _escapeHtml(name) +
        "</div>" +
        '<div class="modal-val">' +
        '<div><span style="color:' +
        color +
        ';font-weight:600">' +
        _escapeHtml(status) +
        "</span></div>" +
        "<div>" +
        _escapeHtml((spec.method || "get").toUpperCase()) +
        " " +
        _escapeHtml(spec.path) +
        "</div>" +
        "</div>" +
        "</div>"
      );
    });
    var summary = cap.mode === "native" ? "原生" : cap.mode === "compat" ? "兼容" : "未知";
    var head =
      '<div style="font-size:.86rem;color:var(--muted);margin-bottom:10px">' +
      "模式：" +
      _escapeHtml(summary) +
      " · 来源：" +
      _escapeHtml(cap.source || "none") +
      (cap.probedAt ? " · 探测时间：" + _escapeHtml(cap.probedAt) : "") +
      "</div>";
    var warning = cap.error
      ? '<div style="font-size:.84rem;color:var(--danger);margin-bottom:10px">探测错误：' +
        _escapeHtml(cap.error) +
        "</div>"
      : "";
    showModal("网关能力探测详情", head + warning + rows.join(""));
  }

  async function probeGatewayCapabilities(force) {
    if (!force && gatewayCapabilityPromise) return gatewayCapabilityPromise;
    if (force) gatewayCapabilityPromise = null;
    gatewayCapabilityPromise = (async function () {
      var base = window.BASE || BASE || "";
      try {
        var response = await fetch(base + "/openapi.json");
        if (!response.ok) throw new Error("openapi http " + response.status);
        var payload = await response.json();
        var resolved = _resolveCapabilityFromOpenApi(payload);
        gatewayCapabilities = {
          loaded: true,
          mode: resolved.mode,
          available: resolved.available,
          missing: resolved.missing,
          source: "openapi",
          error: "",
          probedAt: new Date().toISOString(),
        };
      } catch (error) {
        gatewayCapabilities = {
          loaded: true,
          mode: "unknown",
          available: {},
          missing: Object.keys(GATEWAY_CAPABILITY_PATHS),
          source: "openapi",
          error: String((error && error.message) || error || "probe failed"),
          probedAt: new Date().toISOString(),
        };
      }
      _setTopbarGatewayCapability();
      window.dispatchEvent(
        new CustomEvent("quantamind:gateway-capabilities-ready", {
          detail: { capabilities: gatewayCapabilities },
        })
      );
      return gatewayCapabilities;
    })();
    return gatewayCapabilityPromise;
  }

  function getGatewayCapabilities() {
    return gatewayCapabilities;
  }

  function getGatewayFeatureMode(featureName) {
    var group = GATEWAY_CAPABILITY_GROUPS[featureName] || [];
    if (!group.length) return { mode: gatewayCapabilities.mode || "unknown", missing: [] };
    var missing = group.filter(function (name) {
      return gatewayCapabilities.available[name] !== true;
    });
    var mode = missing.length ? (gatewayCapabilities.mode === "unknown" ? "unknown" : "compat") : "native";
    return { mode: mode, missing: missing };
  }

  function withGatewayModeLabel(text, featureName) {
    var baseText = text || "";
    var status = getGatewayFeatureMode(featureName);
    var modeText = "未知";
    if (status.mode === "native") modeText = "原生";
    else if (status.mode === "compat") modeText = "兼容";
    return baseText + " | 模式：" + modeText;
  }

  function bindShell() {
    document.querySelectorAll(".nav-item").forEach((el) => {
      el.addEventListener("click", () => goToPage(el.dataset.page));
    });
    const logo = document.getElementById("logo-home");
    if (logo) logo.addEventListener("click", () => goToPage("overview"));
    document.addEventListener("click", (event) => {
      const card = event.target.closest(".clickable-card");
      if (card && card.dataset.goto) goToPage(card.dataset.goto);
    });
    window.addEventListener("hashchange", () => {
      if (window.applyAgentHashRoute) window.applyAgentHashRoute();
    });
    window.showToast = showToast;
    window.goToPage = goToPage;
    window.scrollToNavGroup = scrollToNavGroup;
    window.showModal = showModal;
    window.isPageActive = isPageActive;
    window.probeGatewayCapabilities = probeGatewayCapabilities;
    window.getGatewayCapabilities = getGatewayCapabilities;
    window.getGatewayFeatureMode = getGatewayFeatureMode;
    window.withGatewayModeLabel = withGatewayModeLabel;
    window.showGatewayCapabilityDetails = showGatewayCapabilityDetails;
    _setTopbarGatewayCapability();
    var capEl = document.getElementById("gw-capability-mode");
    if (capEl) {
      capEl.style.cursor = "pointer";
      capEl.addEventListener("click", function () {
        showGatewayCapabilityDetails();
      });
    }
    probeGatewayCapabilities();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindShell);
  } else {
    bindShell();
  }
})();
