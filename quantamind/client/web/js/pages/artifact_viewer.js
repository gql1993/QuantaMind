(function () {
  const state = {
    artifacts: [],
    selectedArtifactId: null,
    selectedArtifact: null,
    selectedView: null,
  };

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  }

  function setHint(text, tone) {
    const el = document.getElementById("av-hint");
    if (!el) return;
    el.style.color =
      tone === "danger" ? "var(--danger)" : tone === "warn" ? "var(--warn)" : "var(--muted)";
    const hint = text || "";
    if (window.withGatewayModeLabel) {
      el.textContent = window.withGatewayModeLabel(hint, "artifact_viewer");
      return;
    }
    el.textContent = hint;
  }

  async function fetchJson(path, options) {
    const response = await fetch(BASE + path, options);
    let payload = {};
    try {
      payload = await response.json();
    } catch (_) {
      payload = {};
    }
    if (!response.ok) {
      throw new Error(payload.detail || ("Request failed: " + response.status));
    }
    return payload;
  }

  function filteredArtifacts() {
    const typeFilter = document.getElementById("av-type-filter")?.value || "";
    const keyword = (document.getElementById("av-keyword")?.value || "").trim().toLowerCase();
    return state.artifacts.filter((item) => {
      if (typeFilter && item.artifact_type !== typeFilter) return false;
      if (!keyword) return true;
      const text = [item.artifact_id, item.run_id, item.title, item.summary, item.artifact_type]
        .join(" ")
        .toLowerCase();
      return text.includes(keyword);
    });
  }

  function renderList() {
    const body = document.getElementById("av-tb");
    if (!body) return;
    const rows = filteredArtifacts();
    if (!rows.length) {
      body.innerHTML = '<tr><td colspan="7" class="av-empty">暂无 artifact 记录。</td></tr>';
      return;
    }
    body.innerHTML = rows
      .map((item) => {
        const selected = item.artifact_id === state.selectedArtifactId ? "selected" : "";
        return (
          '<tr class="av-row ' +
          selected +
          '" data-artifact-id="' +
          escapeHtml(item.artifact_id) +
          '">' +
          '<td class="av-mono">' +
          escapeHtml(item.artifact_id) +
          "</td>" +
          '<td class="av-mono">' +
          escapeHtml(item.run_id || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(item.artifact_type || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(item.title || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(item.summary || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(formatTime(item.created_at)) +
          "</td>" +
          '<td><button class="btn av-view-btn" data-artifact-id="' +
          escapeHtml(item.artifact_id) +
          '">查看</button></td>' +
          "</tr>"
        );
      })
      .join("");
  }

  function renderTypePanel(artifact) {
    const panel = document.getElementById("av-type-panel");
    if (!panel) return;
    if (!artifact) {
      panel.innerHTML = '<div class="av-empty">请选择 artifact 查看类型化摘要。</div>';
      return;
    }
    const payload = artifact.payload || {};
    const type = artifact.artifact_type || "generic_artifact";
    if (type === "coordination_report") {
      const route = payload.route_result || {};
      const merged = payload.merged || {};
      panel.innerHTML =
        '<div class="av-card">' +
        '<div class="av-card-title">Coordination 摘要</div>' +
        '<div class="av-grid">' +
        "<div><span>mode</span><b>" +
        escapeHtml(route.mode || "—") +
        "</b></div>" +
        "<div><span>reason</span><b>" +
        escapeHtml(route.reason || "—") +
        "</b></div>" +
        "<div><span>merged count</span><b>" +
        escapeHtml(String(merged.count ?? "—")) +
        "</b></div>" +
        "<div><span>summary</span><b>" +
        escapeHtml(merged.summary || artifact.summary || "—") +
        "</b></div>" +
        "</div></div>";
      return;
    }
    if (type === "intel_report") {
      const report = payload.report || {};
      panel.innerHTML =
        '<div class="av-card">' +
        '<div class="av-card-title">Intel 报告摘要</div>' +
        '<div class="av-grid">' +
        "<div><span>report_id</span><b>" +
        escapeHtml(report.report_id || "—") +
        "</b></div>" +
        "<div><span>status</span><b>" +
        escapeHtml(payload.status || "—") +
        "</b></div>" +
        "<div><span>shortcut</span><b>" +
        escapeHtml(payload.shortcut || "—") +
        "</b></div>" +
        "<div><span>summary</span><b>" +
        escapeHtml(artifact.summary || "—") +
        "</b></div>" +
        "</div></div>";
      return;
    }
    if (type === "db_health_report" || type === "system_diagnosis") {
      panel.innerHTML =
        '<div class="av-card">' +
        '<div class="av-card-title">诊断类产物摘要</div>' +
        '<div class="av-grid">' +
        "<div><span>type</span><b>" +
        escapeHtml(type) +
        "</b></div>" +
        "<div><span>shortcut</span><b>" +
        escapeHtml(payload.shortcut || "—") +
        "</b></div>" +
        "<div><span>status</span><b>" +
        escapeHtml(payload.status || "—") +
        "</b></div>" +
        "<div><span>summary</span><b>" +
        escapeHtml(artifact.summary || "—") +
        "</b></div>" +
        "</div></div>";
      return;
    }
    panel.innerHTML =
      '<div class="av-card">' +
      '<div class="av-card-title">通用产物摘要</div>' +
      '<div class="av-grid">' +
      "<div><span>type</span><b>" +
      escapeHtml(type) +
      "</b></div>" +
      "<div><span>run</span><b>" +
      escapeHtml(artifact.run_id || "—") +
      "</b></div>" +
      "<div><span>title</span><b>" +
      escapeHtml(artifact.title || "—") +
      "</b></div>" +
      "<div><span>summary</span><b>" +
      escapeHtml(artifact.summary || "—") +
      "</b></div>" +
      "</div></div>";
  }

  function renderDetail() {
    const empty = document.getElementById("av-detail-empty");
    const detail = document.getElementById("av-detail");
    if (!empty || !detail) return;
    if (!state.selectedArtifact) {
      empty.style.display = "";
      detail.style.display = "none";
      renderTypePanel(null);
      return;
    }
    empty.style.display = "none";
    detail.style.display = "";
    const artifact = state.selectedArtifact;
    document.getElementById("av-detail-id").textContent = artifact.artifact_id || "—";
    document.getElementById("av-detail-meta").innerHTML =
      '<span class="av-pill">' +
      escapeHtml(artifact.artifact_type || "—") +
      "</span>" +
      '<span class="av-pill">' +
      escapeHtml(artifact.run_id || "—") +
      "</span>" +
      '<span class="av-pill">' +
      escapeHtml(formatTime(artifact.created_at)) +
      "</span>";
    document.getElementById("av-detail-title").textContent = artifact.title || "—";
    document.getElementById("av-detail-summary").textContent = artifact.summary || "—";
    document.getElementById("av-detail-payload").textContent = JSON.stringify(artifact.payload || {}, null, 2);
    document.getElementById("av-detail-rendered").textContent = state.selectedView?.content || "—";
    renderTypePanel(artifact);
  }

  async function loadArtifacts() {
    const runId = (document.getElementById("av-run-id")?.value || "").trim();
    const query = runId ? "?run_id=" + encodeURIComponent(runId) : "";
    setHint("正在加载 artifacts...");
    try {
      const data = await fetchJson("/api/v2/artifacts" + query);
      state.artifacts = data.items || [];
      if (!state.selectedArtifactId || !state.artifacts.some((item) => item.artifact_id === state.selectedArtifactId)) {
        state.selectedArtifactId = state.artifacts[0]?.artifact_id || null;
      }
      renderList();
      await loadSelectedArtifact();
      setHint("已加载 " + state.artifacts.length + " 条 artifacts。");
    } catch (error) {
      state.artifacts = [];
      state.selectedArtifactId = null;
      state.selectedArtifact = null;
      state.selectedView = null;
      renderList();
      renderDetail();
      setHint("加载失败: " + error.message, "danger");
    }
  }

  async function loadSelectedArtifact() {
    if (!state.selectedArtifactId) {
      state.selectedArtifact = null;
      state.selectedView = null;
      renderDetail();
      return;
    }
    try {
      const detail = await fetchJson("/api/v2/artifacts/" + encodeURIComponent(state.selectedArtifactId));
      let view;
      try {
        view = await fetchJson("/api/v2/artifacts/" + encodeURIComponent(state.selectedArtifactId) + "/view");
      } catch (error) {
        const message = String(error && error.message ? error.message : "");
        // Fallback for gateway builds without typed render endpoint.
        if (message !== "Not Found") throw error;
        view = {
          artifact_id: detail.artifact_id,
          render_type: "text",
          content: JSON.stringify(detail.payload || {}, null, 2),
        };
        setHint("当前网关未提供 /view 接口，已使用 payload 文本预览。", "warn");
      }
      state.selectedArtifact = detail;
      state.selectedView = view;
      renderDetail();
    } catch (error) {
      state.selectedArtifact = null;
      state.selectedView = null;
      renderDetail();
      setHint("artifact 详情加载失败: " + error.message, "danger");
    }
  }

  function bindEvents() {
    document.getElementById("av-refresh")?.addEventListener("click", () => loadArtifacts());
    document.getElementById("av-run-id")?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") loadArtifacts();
    });
    document.getElementById("av-type-filter")?.addEventListener("change", () => {
      renderList();
      const rows = filteredArtifacts();
      if (!rows.some((item) => item.artifact_id === state.selectedArtifactId)) {
        state.selectedArtifactId = rows[0]?.artifact_id || null;
      }
      loadSelectedArtifact();
    });
    document.getElementById("av-keyword")?.addEventListener("input", () => {
      renderList();
      const rows = filteredArtifacts();
      if (!rows.some((item) => item.artifact_id === state.selectedArtifactId)) {
        state.selectedArtifactId = rows[0]?.artifact_id || null;
      }
      loadSelectedArtifact();
    });
    document.getElementById("av-tb")?.addEventListener("click", (event) => {
      const btn = event.target.closest(".av-view-btn");
      const row = event.target.closest(".av-row");
      const artifactId = (btn && btn.dataset.artifactId) || (row && row.dataset.artifactId);
      if (!artifactId) return;
      state.selectedArtifactId = artifactId;
      renderList();
      loadSelectedArtifact();
    });
    document.getElementById("av-goto-run-btn")?.addEventListener("click", () => {
      const runId = state.selectedArtifact?.run_id;
      if (!runId) return;
      if (window.openRunInConsole) window.openRunInConsole(runId);
      else if (window.goToPage) window.goToPage("run-console");
    });
  }

  let initialized = false;
  async function loadArtifactViewerPage() {
    if (window.probeGatewayCapabilities) await window.probeGatewayCapabilities();
    if (!initialized) {
      bindEvents();
      initialized = true;
    }
    await loadArtifacts();
  }

  async function openArtifactInViewer(artifactId) {
    if (!artifactId) return;
    if (window.goToPage) window.goToPage("artifact-viewer");
    await loadArtifactViewerPage();
    state.selectedArtifactId = artifactId;
    renderList();
    await loadSelectedArtifact();
  }

  window.addEventListener("quantamind:pagechange", (event) => {
    if (event.detail && event.detail.page === "artifact-viewer") loadArtifactViewerPage();
  });

  if (!window.isPageActive || window.isPageActive("artifact-viewer")) loadArtifactViewerPage();

  window.loadArtifactViewerPage = loadArtifactViewerPage;
  window.openArtifactInViewer = openArtifactInViewer;
})();
