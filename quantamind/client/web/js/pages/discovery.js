(function () {
  let discType = "";
  let discCategory = "";
  let discOnlyUnhandled = false;
  let discSort = "severity";
  let discCache = [];
  const DISCOVERY_FOCUS_KEY = "quantamind_focus_discovery_id";
  const DISCOVERY_FLASH_KEY = "quantamind_focus_discovery_flash";

  function escHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function discSeverityRank(value) {
    return { high: 0, medium: 1, info: 2 }[value] ?? 9;
  }

  function escJsAttr(value) {
    return String(value ?? "").replace(/\\/g, "\\\\").replace(/'/g, "\\'");
  }

  function getDiscoveryById(id) {
    return (discCache || []).find((item) => item.id === id) || null;
  }

  function focusDiscoveryById(id, flash = true) {
    if (!id) return;
    sessionStorage.setItem(DISCOVERY_FOCUS_KEY, id);
    sessionStorage.setItem(DISCOVERY_FLASH_KEY, flash ? "1" : "0");
    goToPage("discovery");
  }

  function renderDiscoveryStats(items) {
    const statsEl = document.getElementById("disc-stats");
    const cats = ["告警", "数据", "实验", "假设", "周报"];
    const byCat = {};
    items.forEach((item) => {
      const category = item.category || "其他";
      byCat[category] = (byCat[category] || 0) + 1;
    });
    let html = '<div class="disc-stats-row">';
    html +=
      '<div class="disc-stat-card" data-disc-cat=""><div class="disc-stat-label">总数</div><div class="disc-stat-value">' +
      items.length +
      '</div><div class="disc-stat-hint">全部发现</div></div>';
    cats.forEach((category) => {
      html +=
        '<div class="disc-stat-card" data-disc-cat="' +
        category +
        '"><div class="disc-stat-label">' +
        category +
        '</div><div class="disc-stat-value">' +
        (byCat[category] || 0) +
        '</div><div class="disc-stat-hint">条</div></div>';
    });
    html += "</div>";
    statsEl.innerHTML = html;
    statsEl.querySelectorAll("[data-disc-cat]").forEach((el) =>
      el.addEventListener("click", () => {
        discCategory = el.dataset.discCat || "";
        discType = "";
        document
          .querySelectorAll("#disc-tabs .tab-btn")
          .forEach((x) => x.classList.remove("active"));
        const tab = [...document.querySelectorAll("#disc-tabs .tab-btn")].find(
          (x) => x.dataset.c === discCategory
        );
        if (tab) tab.classList.add("active");
        renderDiscoveries();
      })
    );
  }

  function renderDiscoveries() {
    const el = document.getElementById("disc-list");
    let items = [...(discCache || [])];
    renderDiscoveryStats(items);
    if (discCategory) items = items.filter((x) => (x.category || "") === discCategory);
    if (discType) items = items.filter((x) => (x.type || "") === discType);
    if (discOnlyUnhandled) items = items.filter((x) => !x.handled);
    items.sort((a, b) => {
      if (discSort === "time") {
        return String(b.time_iso || "").localeCompare(String(a.time_iso || ""));
      }
      const sev = discSeverityRank(a.severity) - discSeverityRank(b.severity);
      if (sev !== 0) return sev;
      return String(b.time_iso || "").localeCompare(String(a.time_iso || ""));
    });
    el.innerHTML = "";
    items.forEach((disc) => {
      const sev = escHtml(disc.severity || "info");
      const entity =
        disc.entity_type || disc.entity_id
          ? '<div class="disc-entity">关联对象：' +
            escHtml(disc.entity_type || "对象") +
            " · " +
            escHtml(disc.entity_id || "未指定") +
            "</div>"
          : "";
      const reco = disc.recommended_action
        ? '<div class="disc-reco"><strong>建议动作：</strong>' +
          escHtml(disc.recommended_action) +
          "</div>"
        : "";
      const handled = disc.handled
        ? '<span class="disc-badge">已处理</span>'
        : '<span class="disc-badge">未处理</span>';
      const occurrenceCount = Math.max(1, parseInt(disc.occurrence_count || 1, 10) || 1);
      const traceMeta = [
        occurrenceCount > 1 ? "重复出现 " + occurrenceCount + " 次" : "",
        disc.first_seen_at ? "首次发现 " + escHtml(String(disc.first_seen_at).replace("T", " ").slice(0, 19)) : "",
        disc.last_seen_at ? "最近出现 " + escHtml(String(disc.last_seen_at).replace("T", " ").slice(0, 19)) : "",
        disc.linked_task_id ? "任务 " + escHtml(disc.linked_task_id) : "",
        disc.handled_by ? "处理人 " + escHtml(disc.handled_by) : "",
      ]
        .filter(Boolean)
        .join(" · ");
      const handledMeta = disc.handled
        ? [
            disc.handled_at
              ? "处理时间 " + escHtml(String(disc.handled_at).replace("T", " ").slice(0, 19))
              : "",
            disc.resolution ? "处理结论 " + escHtml(disc.resolution) : "",
            disc.action_note ? "备注 " + escHtml(disc.action_note) : "",
          ]
            .filter(Boolean)
            .join(" · ")
        : "";
      const nextPrompt = (
        disc.recommended_action ||
        `关于发现「${disc.title}」，请详细分析并给出下一步动作`
      ).replace(/'/g, "\\'");
      const safeId = (disc.id || "").replace(/'/g, "\\'");
      const focusedDiscoveryId = sessionStorage.getItem(DISCOVERY_FOCUS_KEY);
      const isFocused = focusedDiscoveryId && focusedDiscoveryId === disc.id;
      const linkedTaskBtn = disc.linked_task_id
        ? '<button class="btn btn-primary" onclick="showDiscoveryTask(\'' +
          escJsAttr(disc.linked_task_id) +
          "')\">查看任务</button>"
        : '<button class="btn btn-primary" onclick="openDiscoveryTaskModal(\'' +
          safeId +
          "')\">生成任务</button>";
      el.innerHTML +=
        '<div class="disc-card" data-discovery-id="' +
        safeId +
        '"' +
        (isFocused
          ? ' style="box-shadow:0 0 0 1px rgba(87,148,242,.55), 0 0 0 3px rgba(87,148,242,.15);background:rgba(87,148,242,.06)"'
          : "") +
        '>' +
        '<div class="disc-top"><div><h4>' +
        escHtml(disc.title) +
        "</h4><div class=\"meta\">" +
        escHtml(disc.time || "") +
        " · " +
        escHtml(disc.source || "") +
        " · " +
        escHtml(disc.level || "") +
        '</div></div><div class="disc-badges"><span class="disc-badge ' +
        sev +
        '">' +
        escHtml(disc.category || disc.type || "发现") +
        "</span>" +
        handled +
        "</div></div>" +
        entity +
        '<div class="summary">' +
        escHtml(disc.summary || "") +
        "</div>" +
        (traceMeta ? '<div class="disc-reco" style="font-size:.8rem;color:var(--muted)"><strong>追踪：</strong>' + traceMeta + "</div>" : "") +
        (handledMeta ? '<div class="disc-reco" style="font-size:.8rem"><strong>处理：</strong>' + handledMeta + "</div>" : "") +
        reco +
        '<div class="disc-actions">' +
        '<button class="btn" onclick="goToPage(\'chat\');document.getElementById(\'chat-in\').value=\'' +
        nextPrompt +
        '\';document.getElementById(\'chat-in\').focus()">在对话中继续</button>' +
        '<button class="btn" onclick="openDiscoveryEventsModal(\'' +
        safeId +
        "')\">查看事件流</button>" +
        linkedTaskBtn +
        '<button class="btn" onclick="' +
        (disc.handled ? "setDiscoveryHandled('" + safeId + "',false)" : "openDiscoveryHandleModal('" + safeId + "')") +
        '">' +
        (disc.handled ? "重新打开" : "标记已处理") +
        "</button>" +
        "</div>" +
        "</div>";
    });
    const focusedDiscoveryId = sessionStorage.getItem(DISCOVERY_FOCUS_KEY);
    const shouldFlash = sessionStorage.getItem(DISCOVERY_FLASH_KEY) === "1";
    if (focusedDiscoveryId) {
      const focusedCard = el.querySelector('[data-discovery-id="' + focusedDiscoveryId + '"]');
      if (focusedCard) {
        focusedCard.scrollIntoView({ behavior: "smooth", block: "center" });
        if (shouldFlash) {
          setTimeout(() => {
            focusedCard.style.transition = "box-shadow .4s ease, background .4s ease";
            focusedCard.style.boxShadow = "0 0 0 2px rgba(87,148,242,.95), 0 0 0 5px rgba(87,148,242,.18)";
          }, 50);
        }
      }
      sessionStorage.removeItem(DISCOVERY_FOCUS_KEY);
      sessionStorage.removeItem(DISCOVERY_FLASH_KEY);
    }
    if (!items.length) {
      el.innerHTML = '<div style="color:var(--muted)">当前筛选条件下暂无发现</div>';
    }
  }

  async function setDiscoveryHandled(id, handled = true, extra = {}) {
    try {
      await fetch(
        BASE + "/api/v1/heartbeat/discoveries/" + encodeURIComponent(id) + "/handle",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ handled, ...extra }),
        }
      );
      await loadDiscoveries();
    } catch (error) {
      showToast("更新处理状态失败: " + error.message, "danger");
    }
  }

  function openDiscoveryHandleModal(id) {
    const disc = getDiscoveryById(id);
    if (!disc) {
      showToast("未找到发现记录", "danger");
      return;
    }
    showModal(
      "标记发现已处理",
      '<div class="modal-row"><div class="modal-label">发现标题</div><div class="modal-val" style="font-weight:600">' +
        escHtml(disc.title || id) +
        '</div></div>' +
        '<div class="modal-row"><div class="modal-label">建议动作</div><div class="modal-val">' +
        escHtml(disc.recommended_action || "—") +
        '</div></div>' +
        '<div style="display:grid;gap:10px;margin-top:10px">' +
        '<label><div style="font-size:.82rem;color:var(--muted);margin-bottom:4px">处理人</div><input id="disc-handle-by" value="web-ui" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg);color:var(--text)"></label>' +
        '<label><div style="font-size:.82rem;color:var(--muted);margin-bottom:4px">处理结论</div><input id="disc-handle-resolution" value="已确认并纳入跟进" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg);color:var(--text)"></label>' +
        '<label><div style="font-size:.82rem;color:var(--muted);margin-bottom:4px">处理备注</div><textarea id="disc-handle-note" style="width:100%;min-height:88px;padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg);color:var(--text)">' +
        escHtml(disc.recommended_action || "") +
        '</textarea></label>' +
        '<div style="display:flex;gap:8px;align-items:center;margin-top:4px"><button class="btn btn-primary" id="disc-handle-confirm-btn">确认处理</button><span id="disc-handle-status" style="font-size:.82rem;color:var(--muted)"></span></div>' +
        "</div>"
    );

    const overlays = document.querySelectorAll(".modal-overlay");
    const overlay = overlays[overlays.length - 1];
    if (!overlay) return;
    const confirmBtn = overlay.querySelector("#disc-handle-confirm-btn");
    const statusEl = overlay.querySelector("#disc-handle-status");
    confirmBtn.addEventListener("click", async () => {
      confirmBtn.disabled = true;
      statusEl.textContent = "处理中...";
      try {
        await setDiscoveryHandled(id, true, {
          handled_by: overlay.querySelector("#disc-handle-by").value.trim() || "web-ui",
          resolution: overlay.querySelector("#disc-handle-resolution").value.trim() || "已处理",
          action_note: overlay.querySelector("#disc-handle-note").value.trim(),
        });
        statusEl.textContent = "已更新";
        statusEl.style.color = "var(--ok)";
        showToast("发现已标记为处理完成", "ok");
        overlay.remove();
      } catch (error) {
        statusEl.textContent = "处理失败";
        statusEl.style.color = "var(--danger)";
        showToast("更新处理状态失败: " + error.message, "danger");
        confirmBtn.disabled = false;
      }
    });
  }

  async function createTaskForDiscovery(id, body) {
    const response = await fetch(
      BASE + "/api/v1/heartbeat/discoveries/" + encodeURIComponent(id) + "/create-task",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    );
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }

  async function loadDiscoveryEvents(id, limit = 50) {
    const response = await fetch(
      BASE +
        "/api/v1/heartbeat/discoveries/" +
        encodeURIComponent(id) +
        "/events?limit=" +
        encodeURIComponent(limit)
    );
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }

  function formatDiscoveryEventType(eventType) {
    return (
      {
        created: "首次创建",
        reoccurred: "重复出现",
        handled: "标记已处理",
        reopened: "重新打开",
        task_linked: "关联任务",
      }[eventType] || eventType || "事件"
    );
  }

  function renderDiscoveryEventPayload(event) {
    const payload = event.payload || {};
    const parts = [];
    if (payload.title) parts.push("标题：" + escHtml(payload.title));
    if (payload.task_id) {
      parts.push(
        '任务：' +
          escHtml(payload.task_id) +
          ' <button class="btn" style="font-size:.72rem;padding:3px 8px;margin-left:6px" onclick="showDiscoveryTask(\'' +
          escJsAttr(payload.task_id) +
          "')\">查看任务</button>"
      );
    }
    if (payload.task_title) parts.push("任务标题：" + escHtml(payload.task_title));
    if (payload.handled_by) parts.push("处理人：" + escHtml(payload.handled_by));
    if (payload.resolution) parts.push("结论：" + escHtml(payload.resolution));
    if (payload.action_note) parts.push("备注：" + escHtml(payload.action_note));
    if (payload.occurrence_count != null) {
      parts.push("出现次数：" + escHtml(String(payload.occurrence_count)));
    }
    if (payload.severity) parts.push("严重级别：" + escHtml(payload.severity));
    if (payload.entity_id) parts.push("对象：" + escHtml(payload.entity_id));
    if (!parts.length && Object.keys(payload).length) {
      parts.push('<div class="modal-json">' + escHtml(JSON.stringify(payload, null, 2)) + "</div>");
    }
    return parts.join("<br>") || "—";
  }

  async function openDiscoveryEventsModal(id) {
    const disc = getDiscoveryById(id);
    if (!disc) {
      showToast("未找到发现记录", "danger");
      return;
    }
    showModal(
      "发现事件流",
      '<div class="modal-row"><div class="modal-label">发现</div><div class="modal-val" style="font-weight:600">' +
        escHtml(disc.title || id) +
        '</div></div><div id="disc-events-loading" style="padding:16px 0;color:var(--muted)">加载中...</div><div id="disc-events-body"></div>'
    );
    try {
      const data = await loadDiscoveryEvents(id, 50);
      const events = data.events || [];
      const body = document.getElementById("disc-events-body");
      const loading = document.getElementById("disc-events-loading");
      if (loading) loading.remove();
      if (!body) return;
      if (!events.length) {
        body.innerHTML = '<div style="color:var(--muted)">暂无事件记录</div>';
        return;
      }
      body.innerHTML = events
        .map(
          (event) =>
            '<div style="padding:10px 0;border-bottom:1px solid var(--border)">' +
            '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">' +
            '<span class="badge running">' +
            escHtml(formatDiscoveryEventType(event.event_type)) +
            "</span>" +
            '<span style="font-size:.8rem;color:var(--muted)">' +
            escHtml(String(event.created_at || "").replace("T", " ").slice(0, 19)) +
            "</span>" +
            "</div>" +
            '<div style="margin-top:6px;font-size:.84rem;line-height:1.7">' +
            renderDiscoveryEventPayload(event) +
            "</div>" +
            "</div>"
        )
        .join("");
    } catch (error) {
      const loading = document.getElementById("disc-events-loading");
      if (loading) {
        loading.textContent = "加载失败: " + error.message;
        loading.style.color = "var(--danger)";
      } else {
        showToast("加载事件流失败: " + error.message, "danger");
      }
    }
  }

  function openDiscoveryTaskModal(id) {
    const disc = getDiscoveryById(id);
    if (!disc) {
      showToast("未找到发现记录", "danger");
      return;
    }
    const defaultTitle = "跟进发现：" + (disc.title || id);
    showModal(
      "从发现生成任务",
      '<div class="modal-row"><div class="modal-label">发现标题</div><div class="modal-val" style="font-weight:600">' +
        escHtml(disc.title || id) +
        '</div></div>' +
        '<div class="modal-row"><div class="modal-label">建议动作</div><div class="modal-val">' +
        escHtml(disc.recommended_action || "—") +
        '</div></div>' +
        '<div style="display:grid;gap:10px;margin-top:10px">' +
        '<label><div style="font-size:.82rem;color:var(--muted);margin-bottom:4px">任务标题</div><input id="disc-task-title" value="' +
        escHtml(defaultTitle) +
        '" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg);color:var(--text)"></label>' +
        '<label><div style="font-size:.82rem;color:var(--muted);margin-bottom:4px">任务类型</div><input id="disc-task-type" value="discovery_followup" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg);color:var(--text)"></label>' +
        '<label><div style="font-size:.82rem;color:var(--muted);margin-bottom:4px">处理备注</div><textarea id="disc-task-note" style="width:100%;min-height:88px;padding:8px 10px;border:1px solid var(--border);border-radius:var(--radius);background:var(--bg);color:var(--text)">' +
        escHtml(disc.recommended_action || "") +
        '</textarea></label>' +
        '<label style="display:flex;align-items:center;gap:8px"><input id="disc-task-approval" type="checkbox" checked> 需要审批后执行</label>' +
        '<div style="display:flex;gap:8px;align-items:center;margin-top:4px"><button class="btn btn-primary" id="disc-task-create-btn">创建任务</button><span id="disc-task-create-status" style="font-size:.82rem;color:var(--muted)"></span></div>' +
        "</div>"
    );

    const overlays = document.querySelectorAll(".modal-overlay");
    const overlay = overlays[overlays.length - 1];
    if (!overlay) return;
    const createBtn = overlay.querySelector("#disc-task-create-btn");
    const statusEl = overlay.querySelector("#disc-task-create-status");
    createBtn.addEventListener("click", async () => {
      createBtn.disabled = true;
      statusEl.textContent = "创建中...";
      try {
        const result = await createTaskForDiscovery(id, {
          title: overlay.querySelector("#disc-task-title").value.trim(),
          task_type: overlay.querySelector("#disc-task-type").value.trim() || "discovery_followup",
          needs_approval: !!overlay.querySelector("#disc-task-approval").checked,
          created_by: "web-ui",
          action_note: overlay.querySelector("#disc-task-note").value.trim(),
        });
        statusEl.textContent = result.result === "existing" ? "已存在关联任务" : "任务已创建";
        statusEl.style.color = "var(--ok)";
        showToast("已关联任务：" + result.task_id, "ok");
        overlay.remove();
        await loadDiscoveries();
        if (window.focusTaskInTasks) {
          window.focusTaskInTasks(result.task_id, true);
        } else {
          goToPage("tasks");
        }
      } catch (error) {
        statusEl.textContent = "创建失败";
        statusEl.style.color = "var(--danger)";
        showToast("创建任务失败: " + error.message, "danger");
        createBtn.disabled = false;
      }
    });
  }

  async function showDiscoveryTask(taskId) {
    if (window.focusTaskInTasks) {
      window.focusTaskInTasks(taskId, true);
      return;
    }
    goToPage("tasks");
  }

  async function loadDiscoveries() {
    try {
      const response = await fetch(BASE + "/api/v1/heartbeat/discoveries");
      const data = await response.json();
      discCache = data.discoveries || [];
      renderDiscoveries();
    } catch (error) {
      document.getElementById("disc-list").innerHTML =
        '<div style="color:var(--danger)">加载失败</div>';
    }
  }

  document.getElementById("disc-tabs").addEventListener("click", (event) => {
    const button = event.target.closest(".tab-btn");
    if (!button) return;
    document
      .querySelectorAll("#disc-tabs .tab-btn")
      .forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    discType = button.dataset.t || "";
    discCategory = button.dataset.c || "";
    renderDiscoveries();
  });
  document
    .getElementById("disc-unhandled-only")
    .addEventListener("change", (event) => {
      discOnlyUnhandled = !!event.target.checked;
      renderDiscoveries();
    });
  document.getElementById("disc-sort").addEventListener("change", (event) => {
    discSort = event.target.value || "severity";
    renderDiscoveries();
  });

  window.setDiscoveryHandled = setDiscoveryHandled;
  window.openDiscoveryEventsModal = openDiscoveryEventsModal;
  window.openDiscoveryHandleModal = openDiscoveryHandleModal;
  window.openDiscoveryTaskModal = openDiscoveryTaskModal;
  window.showDiscoveryTask = showDiscoveryTask;
  window.focusDiscoveryById = focusDiscoveryById;
  window.loadDiscoveries = loadDiscoveries;
})();
