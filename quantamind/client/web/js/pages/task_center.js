(function () {
  const state = {
    tasks: [],
    selectedTaskId: null,
    pollTimer: null,
    compatibilityMode: "native",
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
    const el = document.getElementById("tc-hint");
    if (!el) return;
    el.style.color =
      tone === "danger" ? "var(--danger)" : tone === "warn" ? "var(--warn)" : "var(--muted)";
    const hint = text || "";
    if (window.withGatewayModeLabel) {
      el.textContent = window.withGatewayModeLabel(hint, "task_center");
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

  function selectedTask() {
    return state.tasks.find((item) => item.task_id === state.selectedTaskId) || null;
  }

  function taskBadge(stateValue) {
    const value = String(stateValue || "queued");
    const cls =
      value === "running"
        ? "running"
        : value === "completed"
          ? "completed"
          : value === "failed" || value === "timeout"
            ? "failed"
            : "pending";
    return '<span class="badge ' + cls + '">' + escapeHtml(value) + "</span>";
  }

  function renderTable() {
    const body = document.getElementById("tc-tb");
    if (!body) return;
    if (!state.tasks.length) {
      body.innerHTML = '<tr><td colspan="10" class="tc-empty">暂无后台任务。</td></tr>';
      return;
    }
    body.innerHTML = state.tasks
      .map((task) => {
        const selected = task.task_id === state.selectedTaskId ? "selected" : "";
        const canCancel = !task._readonly && (task.state === "queued" || task.state === "running");
        const canRetry = !task._readonly && ["failed", "cancelled", "timeout"].includes(task.state);
        return (
          '<tr class="tc-row ' +
          selected +
          '" data-task-id="' +
          escapeHtml(task.task_id) +
          '">' +
          '<td class="tc-mono">' +
          escapeHtml(task.task_id) +
          "</td>" +
          "<td>" +
          escapeHtml(task.task_name || "—") +
          "</td>" +
          "<td>" +
          (task.run_id ? '<span class="tc-mono">' + escapeHtml(task.run_id) + "</span>" : "—") +
          "</td>" +
          "<td>" +
          taskBadge(task.state) +
          "</td>" +
          "<td>" +
          escapeHtml(String(task.attempt || 1)) +
          "/" +
          escapeHtml(String(task.max_retries || 0)) +
          "</td>" +
          "<td>" +
          escapeHtml(task.budget_seconds == null ? "—" : String(task.budget_seconds) + "s") +
          "</td>" +
          "<td>" +
          escapeHtml(formatTime(task.updated_at)) +
          "</td>" +
          "<td>" +
          (canCancel
            ? '<button class="btn tc-cancel-btn" data-task-id="' + escapeHtml(task.task_id) + '">取消</button>'
            : "—") +
          "</td>" +
          "<td>" +
          (canRetry
            ? '<button class="btn tc-retry-btn" data-task-id="' + escapeHtml(task.task_id) + '">重试</button>'
            : "—") +
          "</td>" +
          '<td><button class="btn tc-view-btn" data-task-id="' +
          escapeHtml(task.task_id) +
          '">查看</button></td>' +
          "</tr>"
        );
      })
      .join("");
  }

  function renderDetail() {
    const empty = document.getElementById("tc-detail-empty");
    const detail = document.getElementById("tc-detail");
    const task = selectedTask();
    if (!empty || !detail) return;
    if (!task) {
      empty.style.display = "";
      detail.style.display = "none";
      return;
    }
    empty.style.display = "none";
    detail.style.display = "";
    document.getElementById("tc-detail-id").textContent = task.task_id || "—";
    document.getElementById("tc-detail-name").textContent = task.task_name || "—";
    document.getElementById("tc-detail-state").innerHTML = taskBadge(task.state);
    document.getElementById("tc-detail-run").textContent = task.run_id || "—";
    document.getElementById("tc-detail-attempt").textContent =
      String(task.attempt || 1) + "/" + String(task.max_retries || 0);
    document.getElementById("tc-detail-budget").textContent =
      task.budget_seconds == null ? "—" : String(task.budget_seconds) + "s";
    document.getElementById("tc-detail-times").textContent =
      "创建: " +
      formatTime(task.created_at) +
      " | 启动: " +
      formatTime(task.started_at) +
      " | 完成: " +
      formatTime(task.completed_at) +
      " | 更新: " +
      formatTime(task.updated_at);
    document.getElementById("tc-detail-error").textContent = task.error || "—";
    document.getElementById("tc-detail-result").textContent =
      task.result == null ? "—" : JSON.stringify(task.result, null, 2);
    const gotoBtn = document.getElementById("tc-goto-run-btn");
    if (gotoBtn) gotoBtn.disabled = !task.run_id;
  }

  async function loadTasks() {
    const filter = document.getElementById("tc-state-filter");
    const stateValue = filter ? filter.value : "";
    const query = stateValue ? "?state=" + encodeURIComponent(stateValue) : "";
    setHint("正在加载后台任务...");
    try {
      let data;
      state.compatibilityMode = "native";
      try {
        data = await fetchJson("/api/v2/tasks" + query);
      } catch (error) {
        const message = String(error && error.message ? error.message : "");
        // Fallback for gateway builds without task center endpoint.
        if (message !== "Not Found") throw error;
        const runsData = await fetchJson("/api/v2/runs" + query);
        const runs = Array.isArray(runsData.runs) ? runsData.runs : [];
        data = {
          items: runs.map((run) => ({
            task_id: "compat-run-" + String(run.run_id || ""),
            task_name: "compat_from_run",
            run_id: run.run_id || null,
            state: run.state || "queued",
            attempt: 1,
            max_retries: 0,
            budget_seconds: null,
            created_at: run.created_at || null,
            started_at: null,
            completed_at: run.completed_at || null,
            updated_at: run.updated_at || run.created_at || null,
            error: null,
            result: {
              note: "fallback from /api/v2/runs",
              run_type: run.run_type || null,
              stage: run.stage || null,
              status_message: run.status_message || "",
            },
            _readonly: true,
          })),
        };
        state.compatibilityMode = "runs_fallback";
        setHint("当前网关未提供 Task Center 接口，已回退为 Run 兼容视图（只读）。", "warn");
      }
      state.tasks = data.items || [];
      if (!state.selectedTaskId || !state.tasks.some((item) => item.task_id === state.selectedTaskId)) {
        state.selectedTaskId = state.tasks[0]?.task_id || null;
      }
      renderTable();
      renderDetail();
      setHint("已加载 " + state.tasks.length + " 条任务。");
    } catch (error) {
      state.tasks = [];
      renderTable();
      renderDetail();
      setHint("加载失败: " + error.message, "danger");
    }
  }

  async function cancelTask(taskId) {
    const task = state.tasks.find((item) => item.task_id === taskId);
    if (task && task._readonly) {
      if (window.showToast) window.showToast("兼容视图不支持取消任务，请升级网关。", "warn");
      return;
    }
    try {
      await fetchJson("/api/v2/tasks/" + encodeURIComponent(taskId) + "/cancel", { method: "POST" });
      if (window.showToast) window.showToast("任务取消请求已提交", "ok");
      await loadTasks();
    } catch (error) {
      if (window.showToast) window.showToast("取消失败: " + error.message, "danger");
    }
  }

  async function retryTask(taskId) {
    const task = state.tasks.find((item) => item.task_id === taskId);
    if (task && task._readonly) {
      if (window.showToast) window.showToast("兼容视图不支持重试任务，请升级网关。", "warn");
      return;
    }
    try {
      const data = await fetchJson("/api/v2/tasks/" + encodeURIComponent(taskId) + "/retry", { method: "POST" });
      state.selectedTaskId = data.task?.task_id || state.selectedTaskId;
      if (window.showToast) window.showToast("已创建重试任务", "ok");
      await loadTasks();
    } catch (error) {
      if (window.showToast) window.showToast("重试失败: " + error.message, "danger");
    }
  }

  function bindEvents() {
    document.getElementById("tc-refresh")?.addEventListener("click", () => loadTasks());
    document.getElementById("tc-state-filter")?.addEventListener("change", () => loadTasks());
    document.getElementById("tc-tb")?.addEventListener("click", (event) => {
      const viewBtn = event.target.closest(".tc-view-btn");
      const cancelBtn = event.target.closest(".tc-cancel-btn");
      const retryBtn = event.target.closest(".tc-retry-btn");
      const row = event.target.closest(".tc-row");
      if (cancelBtn && cancelBtn.dataset.taskId) {
        cancelTask(cancelBtn.dataset.taskId);
        return;
      }
      if (retryBtn && retryBtn.dataset.taskId) {
        retryTask(retryBtn.dataset.taskId);
        return;
      }
      const taskId = (viewBtn && viewBtn.dataset.taskId) || (row && row.dataset.taskId);
      if (!taskId) return;
      state.selectedTaskId = taskId;
      renderTable();
      renderDetail();
    });
    document.getElementById("tc-goto-run-btn")?.addEventListener("click", () => {
      const task = selectedTask();
      if (!task || !task.run_id) return;
      if (window.openRunInConsole) window.openRunInConsole(task.run_id);
      else if (window.goToPage) window.goToPage("run-console");
    });
  }

  function schedulePolling() {
    if (state.pollTimer) {
      clearInterval(state.pollTimer);
      state.pollTimer = null;
    }
    state.pollTimer = setInterval(() => {
      const auto = document.getElementById("tc-auto-refresh");
      if (auto && !auto.checked) return;
      if (window.isPageActive && !window.isPageActive("task-center")) return;
      loadTasks();
    }, 4000);
  }

  let initialized = false;
  async function loadTaskCenterPage() {
    if (window.probeGatewayCapabilities) await window.probeGatewayCapabilities();
    if (!initialized) {
      bindEvents();
      schedulePolling();
      initialized = true;
    }
    await loadTasks();
  }

  window.addEventListener("quantamind:pagechange", (event) => {
    if (event.detail && event.detail.page === "task-center") loadTaskCenterPage();
  });

  if (!window.isPageActive || window.isPageActive("task-center")) loadTaskCenterPage();

  window.loadTaskCenterPage = loadTaskCenterPage;
})();
