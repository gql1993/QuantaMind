(function () {
  const state = {
    approvals: [],
    selectedApprovalId: null,
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
    const el = document.getElementById("ap-hint");
    if (!el) return;
    el.style.color =
      tone === "danger" ? "var(--danger)" : tone === "warn" ? "var(--warn)" : "var(--muted)";
    const hint = text || "";
    if (window.withGatewayModeLabel) {
      el.textContent = window.withGatewayModeLabel(hint, "approvals");
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

  function renderApprovalsTable() {
    const body = document.getElementById("ap-tb");
    if (!body) return;
    if (!state.approvals.length) {
      body.innerHTML = '<tr><td colspan="8" class="ap-empty">暂无审批请求。</td></tr>';
      return;
    }
    body.innerHTML = state.approvals
      .map((item) => {
        const selected = item.approval_id === state.selectedApprovalId ? "selected" : "";
        return (
          '<tr class="ap-row ' +
          selected +
          '" data-approval-id="' +
          escapeHtml(item.approval_id) +
          '">' +
          '<td class="ap-mono">' +
          escapeHtml(item.approval_id) +
          "</td>" +
          '<td class="ap-mono">' +
          escapeHtml(item.run_id) +
          "</td>" +
          "<td>" +
          escapeHtml(item.approval_type) +
          "</td>" +
          "<td><span class='badge " +
          (item.status === "pending" ? "pending" : item.status === "approved" ? "completed" : "failed") +
          "'>" +
          escapeHtml(item.status) +
          "</span></td>" +
          "<td>" +
          escapeHtml(item.summary || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(item.reviewer || "—") +
          "</td>" +
          "<td>" +
          escapeHtml(formatTime(item.created_at)) +
          "</td>" +
          '<td><button class="btn ap-view-btn" data-approval-id="' +
          escapeHtml(item.approval_id) +
          '">查看</button></td>' +
          "</tr>"
        );
      })
      .join("");
  }

  function selectedApproval() {
    return state.approvals.find((item) => item.approval_id === state.selectedApprovalId) || null;
  }

  function renderDetail() {
    const empty = document.getElementById("ap-detail-empty");
    const detail = document.getElementById("ap-detail");
    if (!empty || !detail) return;
    const item = selectedApproval();
    if (!item) {
      empty.style.display = "";
      detail.style.display = "none";
      return;
    }
    empty.style.display = "none";
    detail.style.display = "";
    document.getElementById("ap-detail-id").textContent = item.approval_id || "—";
    document.getElementById("ap-detail-run").textContent = item.run_id || "—";
    document.getElementById("ap-detail-type").textContent = item.approval_type || "—";
    document.getElementById("ap-detail-status").innerHTML =
      "<span class='badge " +
      (item.status === "pending" ? "pending" : item.status === "approved" ? "completed" : "failed") +
      "'>" +
      escapeHtml(item.status) +
      "</span>";
    document.getElementById("ap-detail-summary").textContent = item.summary || "—";
    document.getElementById("ap-detail-reviewer").textContent = item.reviewer || "—";
    document.getElementById("ap-detail-created").textContent = formatTime(item.created_at);
    document.getElementById("ap-detail-resolved").textContent = formatTime(item.resolved_at);
    document.getElementById("ap-detail-json").textContent = JSON.stringify(item.details || {}, null, 2);
    const actionWrap = document.getElementById("ap-detail-actions");
    if (actionWrap) actionWrap.style.display = item.status === "pending" ? "" : "none";
  }

  async function loadApprovals() {
    const filter = document.getElementById("ap-status-filter");
    const status = filter ? filter.value : "";
    const query = status ? "?status=" + encodeURIComponent(status) : "";
    setHint("正在加载审批列表...");
    try {
      const data = await fetchJson("/api/v2/approvals" + query);
      state.approvals = data.items || [];
      if (
        !state.selectedApprovalId ||
        !state.approvals.some((item) => item.approval_id === state.selectedApprovalId)
      ) {
        state.selectedApprovalId = state.approvals[0]?.approval_id || null;
      }
      renderApprovalsTable();
      renderDetail();
      setHint("已加载 " + state.approvals.length + " 条审批请求。");
    } catch (error) {
      const message = String(error && error.message ? error.message : "");
      state.approvals = [];
      renderApprovalsTable();
      renderDetail();
      if (message === "Not Found") {
        setHint("当前网关未提供 Approval Center 接口，请升级网关后使用。", "warn");
      } else {
        setHint("加载失败: " + message, "danger");
      }
    }
  }

  async function resolveApproval(action) {
    const item = selectedApproval();
    if (!item) return;
    const reviewer = (document.getElementById("ap-reviewer")?.value || "").trim() || "reviewer";
    const comment = (document.getElementById("ap-comment")?.value || "").trim();
    try {
      await fetchJson("/api/v2/approvals/" + encodeURIComponent(item.approval_id) + "/" + action, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewer, comment }),
      });
      if (window.showToast) window.showToast("审批已" + (action === "approve" ? "通过" : "拒绝"), "ok");
      await loadApprovals();
    } catch (error) {
      const message = String(error && error.message ? error.message : "");
      if (message === "Not Found") {
        if (window.showToast) window.showToast("当前网关未提供审批操作接口，请升级网关。", "warn");
      } else if (window.showToast) {
        window.showToast("审批失败: " + message, "danger");
      }
    }
  }

  async function createApproval() {
    const runId = (document.getElementById("ap-create-run-id")?.value || "").trim();
    const approvalType = document.getElementById("ap-create-type")?.value || "external_delivery";
    const summary = (document.getElementById("ap-create-summary")?.value || "").trim();
    if (!runId || !summary) {
      setHint("创建失败：run_id 和 summary 必填。", "warn");
      return;
    }
    const detailsRaw = (document.getElementById("ap-create-details")?.value || "").trim();
    let details = {};
    if (detailsRaw) {
      try {
        details = JSON.parse(detailsRaw);
      } catch (_) {
        setHint("details 需要是合法 JSON。", "warn");
        return;
      }
    }
    try {
      const response = await fetchJson("/api/v2/approvals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: runId,
          approval_type: approvalType,
          summary,
          details,
        }),
      });
      state.selectedApprovalId = response.approval?.approval_id || null;
      if (window.showToast) window.showToast("审批请求创建成功", "ok");
      await loadApprovals();
    } catch (error) {
      const message = String(error && error.message ? error.message : "");
      if (message === "Not Found") {
        setHint("当前网关未提供审批创建接口，请升级网关后重试。", "warn");
      } else {
        setHint("创建失败: " + message, "danger");
      }
    }
  }

  function bindEvents() {
    document.getElementById("ap-refresh")?.addEventListener("click", () => loadApprovals());
    document.getElementById("ap-status-filter")?.addEventListener("change", () => loadApprovals());
    document.getElementById("ap-create-btn")?.addEventListener("click", () => createApproval());
    document.getElementById("ap-approve-btn")?.addEventListener("click", () => resolveApproval("approve"));
    document.getElementById("ap-reject-btn")?.addEventListener("click", () => resolveApproval("reject"));
    document.getElementById("ap-goto-run-btn")?.addEventListener("click", () => {
      const item = selectedApproval();
      if (!item) return;
      if (window.openRunInConsole) {
        window.openRunInConsole(item.run_id);
      } else if (window.goToPage) {
        window.goToPage("run-console");
      }
    });
    document.getElementById("ap-tb")?.addEventListener("click", (event) => {
      const btn = event.target.closest(".ap-view-btn");
      const row = event.target.closest(".ap-row");
      const approvalId = (btn && btn.dataset.approvalId) || (row && row.dataset.approvalId);
      if (!approvalId) return;
      state.selectedApprovalId = approvalId;
      renderApprovalsTable();
      renderDetail();
    });
  }

  let initialized = false;
  async function loadApprovalsPage() {
    if (window.probeGatewayCapabilities) await window.probeGatewayCapabilities();
    if (!initialized) {
      bindEvents();
      initialized = true;
    }
    await loadApprovals();
  }

  window.addEventListener("quantamind:pagechange", (event) => {
    if (event.detail && event.detail.page === "approvals") loadApprovalsPage();
  });

  if (!window.isPageActive || window.isPageActive("approvals")) loadApprovalsPage();

  window.loadApprovalsPage = loadApprovalsPage;
})();
