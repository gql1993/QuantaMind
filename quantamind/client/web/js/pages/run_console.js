(function () {
  const state = {
    items: [],
    selectedRunId: null,
    shortcuts: [],
    pollTimer: null,
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

  function setConsoleHint(message, tone) {
    const el = document.getElementById("rc-hint");
    if (!el) return;
    el.style.color =
      tone === "danger" ? "var(--danger)" : tone === "warn" ? "var(--warn)" : "var(--muted)";
    const text = message || "";
    if (window.withGatewayModeLabel) {
      el.textContent = window.withGatewayModeLabel(text, "run_console");
      return;
    }
    el.textContent = text;
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

  function getStateBadge(stateValue) {
    const value = String(stateValue || "queued");
    const map = {
      queued: "pending",
      running: "running",
      completed: "completed",
      failed: "failed",
      cancelled: "pending",
    };
    return '<span class="badge ' + (map[value] || "pending") + '">' + escapeHtml(value) + "</span>";
  }

  function getSelectedRunItem() {
    return state.items.find((item) => item.run && item.run.run_id === state.selectedRunId) || null;
  }

  function renderRuns() {
    const body = document.getElementById("rc-runs-tb");
    if (!body) return;
    if (!state.items.length) {
      body.innerHTML =
        '<tr><td colspan="8" class="rc-empty">暂无 Run 记录。可先在右上角启动一个 Shortcut 后台任务。</td></tr>';
      return;
    }
    body.innerHTML = state.items
      .map((item) => {
        const run = item.run || {};
        const selected = run.run_id === state.selectedRunId ? "selected" : "";
        return (
          '<tr class="rc-run-row ' +
          selected +
          '" data-run-id="' +
          escapeHtml(run.run_id) +
          '">' +
          "<td>" +
          '<span class="rc-mono">' +
          escapeHtml(run.run_id || "—") +
          "</span>" +
          "</td>" +
          "<td>" +
          escapeHtml(run.run_type || "—") +
          "</td>" +
          "<td>" +
          getStateBadge(run.state) +
          "</td>" +
          "<td>" +
          escapeHtml(run.stage || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(run.owner_agent || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(String(item.event_count ?? 0)) +
          "/" +
          escapeHtml(String(item.artifact_count ?? 0)) +
          "</td>" +
          "<td>" +
          escapeHtml(formatTime(run.updated_at)) +
          "</td>" +
          '<td><button class="btn rc-view-run-btn" data-run-id="' +
          escapeHtml(run.run_id) +
          '">查看</button></td>' +
          "</tr>"
        );
      })
      .join("");
  }

  function renderRunSummary(item) {
    const empty = document.getElementById("rc-detail-empty");
    const detail = document.getElementById("rc-detail-content");
    if (!empty || !detail) return;
    if (!item || !item.run) {
      empty.style.display = "";
      detail.style.display = "none";
      return;
    }
    empty.style.display = "none";
    detail.style.display = "";
    const run = item.run;
    document.getElementById("rc-run-title").textContent = run.run_id || "—";
    document.getElementById("rc-run-main-meta").innerHTML =
      '<span class="rc-pill">' +
      escapeHtml(run.run_type || "—") +
      "</span>" +
      '<span class="rc-pill">' +
      escapeHtml(run.origin || "manual") +
      "</span>" +
      '<span class="rc-pill">' +
      escapeHtml(run.owner_agent || "unknown") +
      "</span>" +
      '<span class="rc-pill">' +
      escapeHtml(run.stage || "queued") +
      "</span>" +
      '<span class="rc-pill">' +
      escapeHtml(run.state || "queued") +
      "</span>";
    document.getElementById("rc-run-status-message").textContent = run.status_message || "—";
    document.getElementById("rc-run-times").textContent =
      "创建: " +
      formatTime(run.created_at) +
      " | 更新: " +
      formatTime(run.updated_at) +
      " | 完成: " +
      formatTime(run.completed_at);
  }

  function renderEvents(events) {
    const list = document.getElementById("rc-events");
    if (!list) return;
    if (!events || !events.length) {
      list.innerHTML = '<div class="rc-empty">暂无事件。</div>';
      return;
    }
    list.innerHTML = events
      .map((event) => {
        const payload = event.payload ? JSON.stringify(event.payload, null, 2) : "";
        return (
          '<div class="rc-event-item">' +
          '<div class="rc-event-head">' +
          '<span class="rc-event-type">' +
          escapeHtml(event.event_type || "event") +
          "</span>" +
          '<span class="rc-event-time">' +
          escapeHtml(formatTime(event.timestamp)) +
          "</span>" +
          "</div>" +
          (payload ? '<pre class="rc-pre">' + escapeHtml(payload) + "</pre>" : "") +
          "</div>"
        );
      })
      .join("");
  }

  function renderSnapshot(snapshot) {
    const el = document.getElementById("rc-snapshot");
    if (!el) return;
    if (!snapshot) {
      el.textContent = "暂无 snapshot。";
      return;
    }
    el.textContent = JSON.stringify(snapshot, null, 2);
  }

  function renderArtifacts(items) {
    const body = document.getElementById("rc-artifacts-tb");
    if (!body) return;
    if (!items || !items.length) {
      body.innerHTML = '<tr><td colspan="5" class="rc-empty">暂无产物。</td></tr>';
      return;
    }
    body.innerHTML = items
      .map((artifact) => {
        return (
          "<tr>" +
          '<td class="rc-mono">' +
          escapeHtml(artifact.artifact_id || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(artifact.artifact_type || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(artifact.title || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(formatTime(artifact.created_at)) +
          "</td>" +
          '<td><button class="btn rc-view-artifact-btn" data-artifact-id="' +
          escapeHtml(artifact.artifact_id) +
          '">预览</button> <button class="btn rc-open-artifact-viewer-btn" data-artifact-id="' +
          escapeHtml(artifact.artifact_id) +
          '">在 Viewer 打开</button></td>' +
          "</tr>"
        );
      })
      .join("");
  }

  async function loadArtifactView(artifactId) {
    const preview = document.getElementById("rc-artifact-preview");
    if (!preview || !artifactId) return;
    preview.textContent = "加载中...";
    try {
      const data = await fetchJson("/api/v2/artifacts/" + encodeURIComponent(artifactId) + "/view");
      preview.textContent = data.content || "(empty)";
    } catch (error) {
      preview.textContent = "加载失败: " + error.message;
    }
  }

  async function loadRunDetails() {
    const runId = state.selectedRunId;
    if (!runId) {
      renderRunSummary(null);
      renderEvents([]);
      renderSnapshot(null);
      renderArtifacts([]);
      return;
    }
    const selected = getSelectedRunItem();
    renderRunSummary(selected);
    try {
      const [eventsData, snapshotData, artifactsData] = await Promise.all([
        fetchJson("/api/v2/runs/" + encodeURIComponent(runId) + "/events"),
        fetchJson("/api/v2/runs/" + encodeURIComponent(runId) + "/snapshot").catch(() => ({ snapshot: null })),
        fetchJson("/api/v2/runs/" + encodeURIComponent(runId) + "/artifacts"),
      ]);
      renderEvents(eventsData.items || []);
      renderSnapshot(snapshotData.snapshot || null);
      const artifacts = artifactsData.items || [];
      renderArtifacts(artifacts);
      if (artifacts.length) {
        loadArtifactView(artifacts[0].artifact_id);
      } else {
        const preview = document.getElementById("rc-artifact-preview");
        if (preview) preview.textContent = "暂无可预览 artifact。";
      }
    } catch (error) {
      setConsoleHint("详情加载失败: " + error.message, "danger");
    }
  }

  async function loadConsoleRuns() {
    const filter = document.getElementById("rc-state-filter");
    const stateValue = filter ? filter.value : "";
    const query = stateValue ? "?state=" + encodeURIComponent(stateValue) : "";
    setConsoleHint("正在加载 Run 列表...");
    try {
      let data;
      try {
        data = await fetchJson("/api/v2/console/runs" + query);
      } catch (error) {
        const message = String(error && error.message ? error.message : "");
        // Backward compatible fallback for older gateway builds that do not expose /console/runs.
        if (message !== "Not Found") throw error;
        const runsData = await fetchJson("/api/v2/runs" + query);
        const fallbackRuns = Array.isArray(runsData.runs) ? runsData.runs : [];
        const normalizedRuns = stateValue
          ? fallbackRuns.filter((run) => String(run?.state || "").toLowerCase() === String(stateValue).toLowerCase())
          : fallbackRuns;
        data = {
          items: normalizedRuns.map((run) => ({
            run,
            event_count: 0,
            latest_event: null,
            artifact_count: Array.isArray(run?.artifacts) ? run.artifacts.length : 0,
          })),
        };
        setConsoleHint("当前网关未提供 /console/runs，已回退兼容模式。", "warn");
      }
      state.items = data.items || [];
      if (!state.selectedRunId || !state.items.some((item) => item.run?.run_id === state.selectedRunId)) {
        state.selectedRunId = state.items[0]?.run?.run_id || null;
      }
      renderRuns();
      await loadRunDetails();
      const suffix = stateValue ? "（过滤: " + stateValue + "）" : "";
      setConsoleHint("已加载 " + state.items.length + " 条 Run " + suffix);
    } catch (error) {
      state.items = [];
      renderRuns();
      renderRunSummary(null);
      renderEvents([]);
      renderSnapshot(null);
      renderArtifacts([]);
      setConsoleHint("Run 列表加载失败: " + error.message, "danger");
    }
  }

  function renderShortcuts() {
    const wrap = document.getElementById("rc-shortcuts");
    if (!wrap) return;
    if (!state.shortcuts.length) {
      wrap.innerHTML = '<div class="rc-empty">暂无可用 shortcuts。</div>';
      return;
    }
    wrap.innerHTML = state.shortcuts
      .map((item) => {
        const triggerText = Array.isArray(item.triggers) ? item.triggers.slice(0, 2).join(" / ") : "";
        return (
          '<div class="rc-shortcut-item">' +
          '<div class="rc-shortcut-name">' +
          escapeHtml(item.name || "") +
          "</div>" +
          '<div class="rc-shortcut-desc">' +
          escapeHtml(item.description || "—") +
          "</div>" +
          '<div class="rc-shortcut-meta">' +
          escapeHtml(item.run_type || "—") +
          (triggerText ? " | " + escapeHtml(triggerText) : "") +
          "</div>" +
          '<button class="btn btn-primary rc-shortcut-run-btn" data-shortcut="' +
          escapeHtml(item.name || "") +
          '">后台执行</button>' +
          "</div>"
        );
      })
      .join("");
  }

  async function loadShortcuts() {
    try {
      const data = await fetchJson("/api/v2/shortcuts");
      state.shortcuts = data.items || [];
      renderShortcuts();
    } catch (error) {
      state.shortcuts = [];
      renderShortcuts();
      setConsoleHint("Shortcuts 加载失败: " + error.message, "warn");
    }
  }

  async function runShortcutInBackground(name) {
    if (!name) return;
    try {
      try {
        await fetchJson("/api/v2/tasks/shortcuts/" + encodeURIComponent(name), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ force: false, origin: "run_console" }),
        });
      } catch (error) {
        const message = String(error && error.message ? error.message : "");
        // Fallback for gateway builds without background shortcut task endpoint.
        if (message !== "Not Found") throw error;
        await fetchJson("/api/v2/shortcuts/" + encodeURIComponent(name), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ force: false, origin: "run_console:fallback" }),
        });
        setConsoleHint("当前网关未提供后台任务接口，已切换为立即执行模式。", "warn");
      }
      if (window.showToast) window.showToast("已提交后台任务: " + name, "ok");
      setTimeout(() => {
        if (!window.isPageActive || window.isPageActive("run-console")) loadConsoleRuns();
      }, 400);
    } catch (error) {
      if (window.showToast) window.showToast("提交失败: " + error.message, "danger");
    }
  }

  function schedulePolling() {
    if (state.pollTimer) {
      clearInterval(state.pollTimer);
      state.pollTimer = null;
    }
    state.pollTimer = setInterval(() => {
      const auto = document.getElementById("rc-auto-refresh");
      if (auto && !auto.checked) return;
      if (window.isPageActive && !window.isPageActive("run-console")) return;
      loadConsoleRuns();
    }, 5000);
  }

  function bindEvents() {
    const refreshBtn = document.getElementById("rc-refresh");
    if (refreshBtn) refreshBtn.addEventListener("click", () => loadConsoleRuns());
    const stateFilter = document.getElementById("rc-state-filter");
    if (stateFilter) stateFilter.addEventListener("change", () => loadConsoleRuns());

    const runTable = document.getElementById("rc-runs-tb");
    if (runTable) {
      runTable.addEventListener("click", (event) => {
        const btn = event.target.closest(".rc-view-run-btn");
        const row = event.target.closest(".rc-run-row");
        const runId = (btn && btn.dataset.runId) || (row && row.dataset.runId);
        if (!runId) return;
        state.selectedRunId = runId;
        renderRuns();
        loadRunDetails();
      });
    }

    const artifactTable = document.getElementById("rc-artifacts-tb");
    if (artifactTable) {
      artifactTable.addEventListener("click", (event) => {
        const btn = event.target.closest(".rc-view-artifact-btn");
        const openBtn = event.target.closest(".rc-open-artifact-viewer-btn");
        if (btn && btn.dataset.artifactId) {
          loadArtifactView(btn.dataset.artifactId);
          return;
        }
        if (openBtn && openBtn.dataset.artifactId && window.openArtifactInViewer) {
          window.openArtifactInViewer(openBtn.dataset.artifactId);
        }
      });
    }

    const shortcutWrap = document.getElementById("rc-shortcuts");
    if (shortcutWrap) {
      shortcutWrap.addEventListener("click", (event) => {
        const btn = event.target.closest(".rc-shortcut-run-btn");
        if (!btn || !btn.dataset.shortcut) return;
        runShortcutInBackground(btn.dataset.shortcut);
      });
    }
  }

  let initialized = false;
  async function loadRunConsole() {
    if (window.probeGatewayCapabilities) await window.probeGatewayCapabilities();
    if (!initialized) {
      bindEvents();
      schedulePolling();
      initialized = true;
    }
    await Promise.all([loadShortcuts(), loadConsoleRuns()]);
  }

  async function openRunInConsole(runId) {
    if (!runId) return;
    if (window.goToPage) window.goToPage("run-console");
    await loadRunConsole();
    state.selectedRunId = runId;
    renderRuns();
    await loadRunDetails();
  }

  window.addEventListener("quantamind:pagechange", (event) => {
    if (event.detail && event.detail.page === "run-console") loadRunConsole();
  });

  if (!window.isPageActive || window.isPageActive("run-console")) loadRunConsole();

  window.loadRunConsole = loadRunConsole;
  window.openRunInConsole = openRunInConsole;
})();
