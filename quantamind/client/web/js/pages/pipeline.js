(function () {
  window.currentPipelineId = localStorage.getItem("quantamind_last_pipeline") || null;

  function syncPipelineId(pid) {
    window.currentPipelineId = pid || null;
    if (window.currentPipelineId) {
      localStorage.setItem("quantamind_last_pipeline", window.currentPipelineId);
    } else {
      localStorage.removeItem("quantamind_last_pipeline");
    }
  }

  if (window.currentPipelineId && (!window.isPageActive || window.isPageActive("pipeline"))) {
    document.getElementById("pipeline-view").style.display = "block";
    pollPipeline();
  }

  async function loadPipelineHistory() {
    try {
      const response = await fetch(BASE + "/api/v1/pipelines");
      const data = await response.json();
      const table = document.getElementById("pl-history-tb");
      table.innerHTML = "";
      (data.pipelines || []).forEach((pipeline) => {
        const typeLabel = pipeline.type === "chat" ? "对话" : "模板";
        const typeCls = pipeline.type === "chat" ? "running" : "completed";
        table.innerHTML +=
          '<tr><td style="font-family:monospace;font-size:.78rem">' +
          pipeline.pipeline_id +
          "</td><td>" +
          (pipeline.name || "—").slice(0, 30) +
          '</td><td><span class="badge ' +
          typeCls +
          '">' +
          typeLabel +
          '</span></td><td><span class="badge ' +
          (pipeline.status || "pending") +
          '">' +
          (pipeline.status || "—") +
          "</span></td><td>" +
          pipeline.steps_count +
          '</td><td style="font-size:.78rem">' +
          (pipeline.created_at || "").slice(11, 19) +
          '</td><td><button class="btn" onclick="viewPipeline(\'' +
          pipeline.pipeline_id +
          "')\">查看</button></td></tr>";
      });
      if (!data.pipelines?.length) {
        table.innerHTML =
          '<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:16px">暂无流水线记录。发起对话或启动模板流水线后自动生成。</td></tr>';
      }
    } catch (error) {
      console.error(error);
    }
  }

  function viewPipeline(pid) {
    syncPipelineId(pid);
    document.getElementById("pipeline-view").style.display = "block";
    document.getElementById("pl-name").textContent = "加载中…";
    pollPipeline();
    document.getElementById("pipeline-view").scrollIntoView({ behavior: "smooth" });
  }

  async function startPipeline(template) {
    const gateCheck = document.getElementById("pipeline-gate-check").checked;
    try {
      const response = await fetch(BASE + "/api/v1/pipelines", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ template, require_gate_approval: gateCheck }),
      });
      const data = await response.json();
      syncPipelineId(data.pipeline_id);
      document.getElementById("pipeline-view").style.display = "block";
      const names = {
        "1bit_standard": "单比特标准芯片",
        "2bit_coupler": "双比特可调耦合器",
        "20bit_tunable_coupler": "20比特可调耦合器",
        "100bit_tunable_coupler": "100比特可调耦合器",
        "105bit_tunable_coupler": "105比特可调耦合器",
      };
      document.getElementById("pl-name").textContent = names[template] || template;
      showToast("流水线已启动: " + window.currentPipelineId, "ok");
      pollPipeline();
      loadPipelineHistory();
    } catch (error) {
      showToast("启动失败: " + error.message, "danger");
    }
  }

  function plControl(action) {
    if (!window.currentPipelineId) return;
    const messages = {
      pause: "流水线已暂停",
      resume: "流水线已恢复",
      abort: "流水线已终止",
      skip_gate: "审批已通过，继续执行",
    };
    fetch(BASE + "/api/v1/pipelines/" + window.currentPipelineId + "/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    }).then(() => {
      showToast(messages[action] || "操作完成", action === "abort" ? "danger" : "ok");
      pollPipeline();
    });
  }

  async function downloadPipelineReport(format) {
    if (!window.currentPipelineId) return;
    try {
      const response = await fetch(BASE + "/api/v1/pipelines/" + window.currentPipelineId);
      if (!response.ok) {
        showToast("流水线数据已过期（服务重启后丢失），请重新运行流水线", "warn");
        return;
      }
    } catch (error) {
      showToast("无法连接服务", "danger");
      return;
    }
    window.open(
      BASE + "/api/v1/pipelines/" + window.currentPipelineId + "/report?format=" + format,
      "_blank"
    );
  }

  async function pollPipeline() {
    if (!window.currentPipelineId) return;
    try {
      const response = await fetch(BASE + "/api/v1/pipelines/" + window.currentPipelineId);
      if (!response.ok) {
        document.getElementById("pipeline-view").style.display = "none";
        syncPipelineId(null);
        showToast("流水线数据已过期，请重新运行", "warn");
        return;
      }
      const pipeline = await response.json();
      renderPipeline(pipeline);
      if (
        pipeline.status === "running" ||
        pipeline.status === "paused" ||
        pipeline.status === "waiting_approval"
      ) {
        setTimeout(pollPipeline, 800);
      }
    } catch (error) {
      console.error(error);
    }
  }

  function renderPipeline(pipeline) {
    const stages = pipeline.stages || [];
    const steps = pipeline.steps || [];
    const statusEl = document.getElementById("pl-status");
    const statusMap = {
      completed: "已完成",
      running: "运行中",
      paused: "已暂停",
      waiting_approval: "等待审批",
      aborted: "已终止",
      created: "等待",
    };
    const clsMap = {
      completed: "completed",
      running: "running",
      paused: "pending",
      waiting_approval: "approval",
      aborted: "failed",
      created: "pending",
    };
    statusEl.textContent = statusMap[pipeline.status] || pipeline.status;
    statusEl.className = "badge " + (clsMap[pipeline.status] || "pending");
    document.getElementById("pl-name").textContent = pipeline.name || (pipeline.agent_label || "流水线");
    document.getElementById("pl-pause").style.display = pipeline.status === "running" ? "" : "none";
    document.getElementById("pl-resume").style.display = pipeline.status === "paused" ? "" : "none";
    document.getElementById("pl-approve-gate").style.display =
      pipeline.status === "waiting_approval" ? "" : "none";
    document.getElementById("pl-abort").style.display = ["running", "paused", "waiting_approval"].includes(
      pipeline.status
    )
      ? ""
      : "none";

    const completed = steps.filter((step) => step.status === "completed").length;
    let progressText = completed + "/" + steps.length + " 步骤完成";
    if (pipeline.current_step) progressText += " · 当前：" + pipeline.current_step;
    document.getElementById("pl-progress-text").textContent = progressText;

    const bar = document.getElementById("pl-stages");
    bar.innerHTML = "";
    stages.forEach((stage) => {
      const stageSteps = steps.filter((step) => step.stage === stage.stage);
      const donePct = stageSteps.length
        ? (stageSteps.filter((step) => step.status === "completed").length / stageSteps.length) * 100
        : 0;
      const isActive = pipeline.current_stage === stage.stage;
      bar.innerHTML +=
        '<div style="flex:1;background:' +
        (donePct >= 100 ? stage.color : isActive ? stage.color + "88" : "var(--border)") +
        ';border-radius:3px;transition:background .5s" title="' +
        stage.name +
        " (" +
        Math.round(donePct) +
        '%)"></div>';
    });

    const cards = document.getElementById("pl-stage-cards");
    cards.innerHTML = "";
    stages.forEach((stage) => {
      const stageSteps = steps.filter((step) => step.stage === stage.stage);
      const done = stageSteps.filter((step) => step.status === "completed").length;
      const isActive = pipeline.current_stage === stage.stage;
      const isDone = stageSteps.length > 0 && done === stageSteps.length && pipeline.current_stage > stage.stage;
      const cls = isDone ? "done" : isActive ? "active" : "pending";
      cards.innerHTML +=
        '<div class="pl-stage-card ' +
        cls +
        '" style="border-left:3px solid ' +
        stage.color +
        '"><div class="emoji">' +
        stage.agent.slice(0, 2) +
        '</div><div class="info"><div class="name">' +
        stage.name +
        '</div><div class="agent">' +
        stage.agent +
        '</div></div><div class="count">' +
        done +
        "/" +
        stageSteps.length +
        "</div></div>";
    });

    (pipeline.gates || []).forEach((gate) => {
      if (gate.status === "waiting_approval") {
        cards.innerHTML +=
          '<div class="pl-stage-card active" style="border-left:3px solid var(--danger);background:rgba(248,81,73,.08)"><div class="emoji">🚦</div><div class="info"><div class="name">审批门：' +
          gate.stage +
          '</div><div class="agent">等待人工审批</div></div></div>';
      }
    });

    const timeline = document.getElementById("pl-timeline");
    timeline.innerHTML = "";
    steps.forEach((step) => {
      const resultStr = step.result ? JSON.stringify(step.result, null, 0).slice(0, 250) : "";
      timeline.innerHTML +=
        '<div class="tl-item"><div class="tl-dot ' +
        step.status +
        '"></div><div class="tl-body"><div class="tl-title">' +
        step.emoji +
        " " +
        step.title +
        '</div><div class="tl-meta">' +
        step.agent +
        " · " +
        (step.tool || "") +
        " · " +
        step.status +
        (step.completed_at ? " · " + step.completed_at.slice(11, 19) : "") +
        '</div>' +
        (resultStr ? '<div class="tl-result">' + resultStr + "</div>" : "") +
        "</div></div>";
    });
    timeline.scrollTop = timeline.scrollHeight;
  }

  document.getElementById("pl-pause").addEventListener("click", () => plControl("pause"));
  document.getElementById("pl-resume").addEventListener("click", () => plControl("resume"));
  document.getElementById("pl-abort").addEventListener("click", () => {
    if (confirm("确定终止流水线？")) plControl("abort");
  });
  document.getElementById("pl-approve-gate").addEventListener("click", () => plControl("skip_gate"));
  document.getElementById("pl-download-word").addEventListener("click", () => downloadPipelineReport("docx"));
  document.getElementById("pl-download-md").addEventListener("click", () => downloadPipelineReport("md"));

  let pipelinePageLoaded = false;
  function loadPipelinePage() {
    if (!pipelinePageLoaded) {
      pipelinePageLoaded = true;
      loadPipelineHistory();
    }
    if (window.currentPipelineId) {
      document.getElementById("pipeline-view").style.display = "block";
      pollPipeline();
    }
  }
  window.addEventListener("quantamind:pagechange", (event) => {
    if (event.detail && event.detail.page === "pipeline") loadPipelinePage();
  });
  if (!window.isPageActive || window.isPageActive("pipeline")) loadPipelinePage();

  window.loadPipelineHistory = loadPipelineHistory;
  window.loadPipelinePage = loadPipelinePage;
  window.viewPipeline = viewPipeline;
  window.startPipeline = startPipeline;
  window.pollPipeline = pollPipeline;
  window.renderPipeline = renderPipeline;
})();
