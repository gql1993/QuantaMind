(function () {
  const chatMsgs = document.getElementById("chat-msgs");
  let chatSending = false;
  let chatPipelineId = null;
  let chatPipelinePollTimer = null;
  let activeChatController = null;
  let activeChatIdleTimer = null;
  let chatJobPollTimer = null;
  let activeChatJobId = null;
  const CHAT_CONNECT_TIMEOUT_MS = 20000;
  const CHAT_STREAM_IDLE_TIMEOUT_MS = 30000;
  const CHAT_AUX_TIMEOUT_MS = 10000;

  function appendMsg(role, text) {
    const wrapper = document.createElement("div");
    wrapper.className = "msg " + role;
    wrapper.innerHTML =
      '<div class="msg-role">' +
      (role === "user" ? "我" : "QuantaMind") +
      '</div><div class="msg-bubble"></div>';
    const bubble = wrapper.querySelector(".msg-bubble");
    bubble.textContent = text;
    chatMsgs.appendChild(wrapper);
    chatMsgs.scrollTop = chatMsgs.scrollHeight;
    return bubble;
  }

  function clearChatIdleTimer() {
    if (activeChatIdleTimer) {
      clearTimeout(activeChatIdleTimer);
      activeChatIdleTimer = null;
    }
  }

  function clearChatPipelineTimer() {
    if (chatPipelinePollTimer) {
      clearTimeout(chatPipelinePollTimer);
      chatPipelinePollTimer = null;
    }
  }

  function clearChatJobTimer() {
    if (chatJobPollTimer) {
      clearTimeout(chatJobPollTimer);
      chatJobPollTimer = null;
    }
  }

  function stopActiveChatRequest(reason) {
    clearChatIdleTimer();
    if (activeChatController) {
      try {
        activeChatController.abort(reason || "chat_cancelled");
      } catch (_) {}
      activeChatController = null;
    }
  }

  function armChatIdleTimeout() {
    clearChatIdleTimer();
    activeChatIdleTimer = setTimeout(() => {
      stopActiveChatRequest("chat_stream_idle_timeout");
    }, CHAT_STREAM_IDLE_TIMEOUT_MS);
  }

  async function fetchWithTimeout(url, options, timeoutMs) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort("fetch_timeout"), timeoutMs);
    try {
      const response = await fetch(url, { ...(options || {}), signal: controller.signal });
      return response;
    } finally {
      clearTimeout(timer);
    }
  }

  async function sendChat() {
    if (chatSending) return;
    const input = document.getElementById("chat-in");
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    input.disabled = true;
    document.getElementById("chat-send").disabled = true;
    chatSending = true;

    if (!window.curSession) {
      try {
        const response = await fetch(BASE + "/api/v1/sessions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
        });
        window.curSession = (await response.json()).session_id;
      } catch (error) {
        appendMsg("assistant", "[连接失败]");
        input.disabled = false;
        document.getElementById("chat-send").disabled = false;
        chatSending = false;
        return;
      }
    }

    appendMsg("user", message);
    const bubble = appendMsg("assistant", "思考中…");
    try {
      stopActiveChatRequest("chat_replaced");
      clearChatPipelineTimer();
      clearChatJobTimer();
      activeChatJobId = null;
      activeChatController = new AbortController();
      const connectTimer = setTimeout(() => {
        if (activeChatController) activeChatController.abort("chat_connect_timeout");
      }, CHAT_CONNECT_TIMEOUT_MS);
      const response = await fetch(BASE + "/api/v1/chat-async", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: window.curSession, message }),
        signal: activeChatController.signal,
      });
      clearTimeout(connectTimer);
      if (!response.ok) throw new Error("HTTP " + response.status);
      const payload = await response.json();
      activeChatJobId = payload.job_id || null;
      bubble.textContent = "已提交，正在后台执行…";
      if (activeChatJobId) {
        startChatJobPolling(activeChatJobId, bubble);
      } else {
        bubble.textContent = "[未创建聊天任务]";
      }
    } catch (error) {
      const messageText =
        error && error.name === "AbortError"
          ? "[请求已中断或超时，可稍后重试]"
          : "[请求失败: " + error.message + "]";
      bubble.textContent = bubble.textContent ? bubble.textContent + "\n" + messageText : messageText;
    } finally {
      clearChatIdleTimer();
      activeChatController = null;
      input.disabled = false;
      document.getElementById("chat-send").disabled = false;
      chatSending = false;
      input.focus();
      chatMsgs.scrollTop = chatMsgs.scrollHeight;
      refreshChatSessions();
      if (!chatPipelineId && !activeChatJobId) {
        startChatPipelinePolling();
      }
    }
  }

  function startChatJobPolling(jobId, bubble) {
    clearChatJobTimer();
    chatJobPollTimer = setTimeout(() => pollChatJob(jobId, bubble, 0), 500);
  }

  function renderChatJobStatus(job) {
    const parts = [];
    if (job.status_message) parts.push(job.status_message);
    if (job.agent_label) parts.push("智能体：" + job.agent_label);
    if (job.tool_name) parts.push("工具：" + job.tool_name);
    if (job.pipeline_id) parts.push("流水线：" + job.pipeline_id);
    return parts.join("\n");
  }

  async function pollChatJob(jobId, bubble, attempt) {
    const tries = typeof attempt === "number" ? attempt : 0;
    try {
      const response = await fetchWithTimeout(BASE + "/api/v1/chat-jobs/" + jobId, undefined, CHAT_AUX_TIMEOUT_MS);
      if (!response.ok) throw new Error("HTTP " + response.status);
      const job = await response.json();
      activeChatJobId = job.job_id || jobId;
      if (job.pipeline_id) {
        chatPipelineId = job.pipeline_id;
        startChatPipelinePolling(job.pipeline_id);
      }
      if (job.content) {
        bubble.textContent = job.content;
      } else if (job.status === "running" || job.status === "queued") {
        bubble.textContent = renderChatJobStatus(job) || "正在执行中…";
      }
      if (job.status === "completed") {
        clearChatJobTimer();
        activeChatJobId = null;
        if (!bubble.textContent) bubble.textContent = "[空回复]";
        refreshChatSessions();
        return;
      }
      if (job.status === "failed") {
        clearChatJobTimer();
        activeChatJobId = null;
        const statusText = renderChatJobStatus(job);
        bubble.textContent = (job.content || statusText || "") + "\n[请求失败: " + (job.error || "未知错误") + "]";
        refreshChatSessions();
        return;
      }
      if (tries < 240) {
        chatJobPollTimer = setTimeout(() => pollChatJob(jobId, bubble, tries + 1), 1000);
      } else {
        clearChatJobTimer();
        activeChatJobId = null;
        bubble.textContent = (bubble.textContent || "") + "\n[后台任务轮询超时，可稍后查看会话历史]";
      }
    } catch (error) {
      console.error(error);
      if (tries < 60) {
        chatJobPollTimer = setTimeout(() => pollChatJob(jobId, bubble, tries + 1), 1500);
      } else {
        clearChatJobTimer();
        activeChatJobId = null;
        bubble.textContent = (bubble.textContent || "") + "\n[结果查询超时，可稍后重试]";
      }
    }
  }

  function startChatPipelinePolling(pid) {
    if (pid) chatPipelineId = pid;
    clearChatPipelineTimer();
    chatPipelinePollTimer = setTimeout(() => pollChatPipelines(0), 500);
  }

  async function pollChatPipelines(attempt) {
    const tries = typeof attempt === "number" ? attempt : 0;
    try {
      const response = await fetchWithTimeout(BASE + "/api/v1/chat-pipelines", undefined, CHAT_AUX_TIMEOUT_MS);
      if (!response.ok) throw new Error("HTTP " + response.status);
      const data = await response.json();
      const pipelines = data.pipelines || [];
      if (pipelines.length > 0) {
        const latest = pipelines[pipelines.length - 1];
        if (!chatPipelineId || latest.pipeline_id === chatPipelineId) {
          chatPipelineId = latest.pipeline_id;
          if (latest.steps_count > 0 || latest.status === "completed" || latest.status === "failed") {
            renderChatPipeline(latest.pipeline_id);
            return;
          }
        }
      }
      if (tries < 40) {
        chatPipelinePollTimer = setTimeout(() => pollChatPipelines(tries + 1), 800);
      }
    } catch (error) {
      console.error(error);
      if (tries < 12) {
        chatPipelinePollTimer = setTimeout(() => pollChatPipelines(tries + 1), 1200);
      }
    }
  }

  async function renderChatPipeline(pid) {
    try {
      const response = await fetchWithTimeout(BASE + "/api/v1/chat-pipelines/" + pid, undefined, CHAT_AUX_TIMEOUT_MS);
      if (!response.ok) throw new Error("HTTP " + response.status);
      const pipeline = await response.json();
      const panel = document.getElementById("chat-pipeline-panel");
      if (!pipeline.steps || pipeline.steps.length === 0) {
        panel.style.display = "none";
        return;
      }
      panel.style.display = "block";
      const statusMap = { completed: "已完成", running: "运行中", failed: "失败" };
      const clsMap = { completed: "completed", running: "running", failed: "failed" };
      document.getElementById("cp-status").textContent = statusMap[pipeline.status] || pipeline.status;
      document.getElementById("cp-status").className = "badge " + (clsMap[pipeline.status] || "pending");
      document.getElementById("cp-title").textContent =
        (pipeline.agent_label || "对话") + " · " + pipeline.steps.length + " 步";
      const done = pipeline.steps.filter((step) => step.status === "completed").length;
      document.getElementById("cp-progress").textContent = done + "/" + pipeline.steps.length;
      const stepsEl = document.getElementById("cp-steps");
      stepsEl.innerHTML = "";
      pipeline.steps.forEach((step) => {
        const resultPreview = step.result ? JSON.stringify(step.result).slice(0, 150) : "";
        stepsEl.innerHTML +=
          '<div class="tl-item"><div class="tl-dot ' +
          (step.status || "pending") +
          '"></div><div class="tl-body"><div class="tl-title">' +
          (step.tool || "") +
          '</div><div class="tl-meta">' +
          (step.agent || "") +
          " · " +
          (step.status || "") +
          (step.completed_at ? " · " + step.completed_at.slice(11, 19) : "") +
          '</div>' +
          (resultPreview ? '<div class="tl-result">' + resultPreview + "</div>" : "") +
          "</div></div>";
      });
      if (pipeline.status === "running") {
        clearChatPipelineTimer();
        chatPipelinePollTimer = setTimeout(() => renderChatPipeline(pid), 800);
      } else {
        clearChatPipelineTimer();
      }
    } catch (error) {
      console.error(error);
      clearChatPipelineTimer();
      chatPipelinePollTimer = setTimeout(() => renderChatPipeline(pid), 1200);
    }
  }

  async function refreshChatSessions() {
    try {
      const response = await fetchWithTimeout(BASE + "/api/v1/sessions", undefined, CHAT_AUX_TIMEOUT_MS);
      if (!response.ok) throw new Error("HTTP " + response.status);
      const data = await response.json();
      const el = document.getElementById("chat-session-list");
      el.innerHTML = "";
      (data.sessions || []).forEach((session) => {
        const active = session.session_id === window.curSession ? "active" : "";
        const label = session.title || session.session_id.slice(0, 8) + "…";
        el.innerHTML +=
          '<div class="item ' +
          active +
          '" data-sid="' +
          session.session_id +
          '"><span>' +
          label +
          ' <span style="color:var(--muted);font-size:.72rem">(' +
          session.messages +
          '条)</span></span><span class="del" data-sid="' +
          session.session_id +
          '">✕</span></div>';
      });
      el.querySelectorAll(".item").forEach((item) =>
        item.addEventListener("click", (event) => {
          if (event.target.classList.contains("del")) {
            deleteSession(event.target.dataset.sid);
            return;
          }
          window.curSession = item.dataset.sid;
          loadChatHistory(window.curSession);
          refreshChatSessions();
        })
      );
    } catch (error) {
      console.error(error);
    }
  }

  async function loadChatHistory(sid) {
    try {
      const response = await fetchWithTimeout(BASE + "/api/v1/sessions/" + sid + "/history", undefined, CHAT_AUX_TIMEOUT_MS);
      if (!response.ok) throw new Error("HTTP " + response.status);
      const data = await response.json();
      chatMsgs.innerHTML = "";
      (data.messages || []).forEach((message) => appendMsg(message.role, message.content));
    } catch (error) {
      console.error(error);
    }
  }

  async function deleteSession(sid) {
    try {
      const response = await fetchWithTimeout(
        BASE + "/api/v1/sessions/" + sid,
        { method: "DELETE" },
        CHAT_AUX_TIMEOUT_MS
      );
      if (!response.ok) throw new Error("HTTP " + response.status);
      showToast("会话已删除", "ok");
      if (sid === window.curSession) {
        window.curSession = null;
        chatMsgs.innerHTML =
          '<div class="msg assistant"><div class="msg-role">QuantaMind</div><div class="msg-bubble">会话已删除。</div></div>';
      }
      refreshChatSessions();
    } catch (error) {
      showToast("删除失败", "danger");
    }
  }

  document.getElementById("chat-send").addEventListener("click", sendChat);
  document.getElementById("chat-in").addEventListener("keydown", (event) => {
    if (event.key === "Enter") sendChat();
  });
  document.getElementById("chat-new").addEventListener("click", () => {
    window.curSession = null;
    chatMsgs.innerHTML =
      '<div class="msg assistant"><div class="msg-role">QuantaMind</div><div class="msg-bubble">新会话已创建。</div></div>';
    refreshChatSessions();
  });
  document.getElementById("cp-view-full").addEventListener("click", () => {
    if (chatPipelineId) {
      window.currentPipelineId = chatPipelineId;
      localStorage.setItem("quantamind_last_pipeline", chatPipelineId);
      goToPage("pipeline");
      setTimeout(() => {
        document.getElementById("pipeline-empty").style.display = "none";
        document.getElementById("pipeline-view").style.display = "block";
        document.getElementById("pl-name").textContent = "对话流水线";
      }, 100);
    }
  });

  let chatPageLoaded = false;
  function loadChatPage() {
    if (chatPageLoaded) return;
    chatPageLoaded = true;
    refreshChatSessions();
  }
  window.addEventListener("quantamind:pagechange", (event) => {
    if (event.detail && event.detail.page === "chat") {
      loadChatPage();
    } else {
      stopActiveChatRequest("leave_chat_page");
      clearChatPipelineTimer();
      clearChatJobTimer();
    }
  });
  window.addEventListener("beforeunload", () => {
    stopActiveChatRequest("page_unload");
    clearChatPipelineTimer();
    clearChatJobTimer();
  });
  if (!window.isPageActive || window.isPageActive("chat")) loadChatPage();

  window.sendChat = sendChat;
  window.appendMsg = appendMsg;
  window.refreshChatSessions = refreshChatSessions;
  window.loadChatPage = loadChatPage;
  window.loadChatHistory = loadChatHistory;
  window.deleteSession = deleteSession;
})();
