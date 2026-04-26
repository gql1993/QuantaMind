(function () {
  async function loadDataHub() {
    try {
      const [capR, histR, pulseR, assetsR, syncStatusR, syncJobsR, standardsR] = await Promise.all([
        fetch(BASE + "/api/v1/dataplatform/capabilities"),
        fetch(BASE + "/api/v1/state/pipeline-history"),
        fetch(BASE + "/api/v1/state/pulse-calibration-history?limit=30"),
        fetch(BASE + "/api/v1/dataplatform/assets"),
        fetch(BASE + "/api/v1/dataplatform/sync-status"),
        fetch(BASE + "/api/v1/dataplatform/sync-jobs"),
        fetch(BASE + "/api/v1/dataplatform/standards"),
      ]);
      const cap = await capR.json();
      const hist = await histR.json();
      const pulse = await pulseR.json();
      const assetsData = await assetsR.json();
      const syncStatus = await syncStatusR.json();
      const syncJobs = await syncJobsR.json();
      const standards = await standardsR.json();
      const wh = cap.warehouse || {};
      const olapDisplayName = wh.source || syncJobs.olap_display || "";
      const hintEl = document.getElementById("datahub-olap-hint");
      if (hintEl) {
        const src = wh.source || "—";
        const eng = wh.engine ? String(wh.engine) : "";
        hintEl.textContent = eng
          ? "OLAP 数据层：" + src + " · engine=" + eng
          : "OLAP 数据层：" + src;
      }
      function displaySyncSink(s) {
        if (olapDisplayName && /doris/i.test(String(s || ""))) return olapDisplayName;
        return s || "—";
      }
      function displaySyncName(n) {
        if (!n) return "—";
        if (olapDisplayName && /doris/i.test(String(n))) return String(n).replace(/\bDoris\b/gi, olapDisplayName);
        return n;
      }
      const pipelineRecords = hist.records || [];
      const pulseRecords = pulse.records || [];
      const assets = assetsData.assets || [];
      const jobs = syncJobs.jobs || [];
      const standardsList = standards.standards || [];
      const domainCount = Array.isArray(wh.domains) ? wh.domains.length : 0;
      document.getElementById("datahub-stats").innerHTML =
        '<div class="card stat-card"><div class="stat-label">数据域</div><div class="stat-value">' +
        domainCount +
        '</div><div class="stat-hint">' +
        (wh.total_tables || 0) +
        ' 张表</div></div>' +
        '<div class="card stat-card"><div class="stat-label">总行数</div><div class="stat-value">' +
        (wh.total_rows || 0).toLocaleString() +
        '</div><div class="stat-hint">条记录</div></div>' +
        '<div class="card stat-card"><div class="stat-label">数据资产</div><div class="stat-value">' +
        assets.length +
        '</div><div class="stat-hint">qData 目录</div></div>' +
        '<div class="card stat-card"><div class="stat-label">同步任务</div><div class="stat-value ok">' +
        (syncStatus.running || 0) +
        '</div><div class="stat-hint">运行中 / 共 ' +
        (syncStatus.total_jobs || jobs.length || 0) +
        " 个</div></div>";

      const pipelineTable = document.getElementById("datahub-pipelines");
      pipelineTable.innerHTML = "";
      pipelineRecords.forEach((record) => {
        const totalSteps = (record.steps || []).length;
        const doneSteps = (record.steps || []).filter((step) => step.status === "completed").length;
        pipelineTable.innerHTML +=
          '<tr><td style="font-family:monospace;font-size:.8rem">' +
          record.pipeline_id +
          "</td><td>" +
          (record.name || "—") +
          '</td><td><span class="badge ' +
          (record.status || "pending") +
          '">' +
          (record.status || "—") +
          "</span></td><td>" +
          doneSteps +
          "/" +
          totalSteps +
          "</td><td>" +
          (record.created_at || "") +
          "</td></tr>";
      });
      if (!pipelineRecords.length) {
        pipelineTable.innerHTML =
          '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:20px">暂无流水线运行记录。启动流水线后数据将自动持久化到 PostgreSQL。</td></tr>';
      }

      const pulseTable = document.getElementById("datahub-pulse-history");
      pulseTable.innerHTML = "";
      pulseRecords.slice(0, 30).forEach((record) => {
        const payload = record.payload || {};
        const keyVal = payload.value_ghz ?? payload.value ?? payload.readout_freq_ghz ?? payload.T1_us ?? "—";
        pulseTable.innerHTML +=
          '<tr><td style="font-family:monospace;font-size:.78rem">' +
          (record.calibration_key || "—") +
          "</td><td>" +
          (payload.qubit || "—") +
          "</td><td>" +
          (payload.source || "—") +
          "</td><td>" +
          keyVal +
          '</td><td style="font-size:.78rem">' +
          (record.recorded_at || "").replace("T", " ").slice(0, 19) +
          "</td></tr>";
      });
      if (!pulseRecords.length) {
        pulseTable.innerHTML =
          '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:16px">暂无 Pulse 校准历史。运行 Qiskit Experiments 或 Pulse 校准后会自动写入。</td></tr>';
      }

      const assetsTable = document.getElementById("datahub-assets");
      assetsTable.innerHTML = "";
      assets.forEach((asset) => {
        assetsTable.innerHTML +=
          '<tr><td style="font-weight:600">' +
          (asset.name || "—") +
          '</td><td><span class="badge running" style="font-size:.74rem">' +
          (asset.domain || "—") +
          "</span></td><td style=\"font-family:monospace;font-size:.8rem\">" +
          (asset.table || "—") +
          "</td><td>" +
          (asset.owner || "—") +
          "</td><td>" +
          (asset.quality_score != null ? asset.quality_score + "%" : "—") +
          '</td><td style="font-size:.78rem;color:var(--muted)">' +
          ((asset.tags || []).join(" · ") || "—") +
          "</td></tr>";
      });
      if (!assets.length) {
        assetsTable.innerHTML =
          '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:16px">暂无数据资产目录。</td></tr>';
      }

      const jobsTable = document.getElementById("datahub-sync-jobs");
      jobsTable.innerHTML = "";
      jobs.forEach((job) => {
        jobsTable.innerHTML +=
          '<tr><td style="font-weight:600">' +
          displaySyncName(job.name || "—") +
          "</td><td>" +
          (job.source || "—") +
          "</td><td>" +
          displaySyncSink(job.sink) +
          "</td><td>" +
          (job.sync_type || "—") +
          '</td><td><span class="badge ' +
          (job.status || "pending") +
          '">' +
          (job.status || "—") +
          "</span></td><td>" +
          (job.records_synced || 0).toLocaleString() +
          "</td></tr>";
      });
      if (!jobs.length) {
        jobsTable.innerHTML =
          '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:16px">暂无同步任务。</td></tr>';
      }

      const standardsEl = document.getElementById("datahub-standards");
      let standardsHtml = "";
      standardsList.forEach((standard) => {
        standardsHtml +=
          '<div class="card" style="margin-bottom:10px;padding:12px">' +
          '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">' +
          '<span style="font-weight:600">' +
          (standard.name || "—") +
          "</span>" +
          '<span class="badge completed" style="font-size:.72rem">' +
          (standard.domain || "—") +
          "</span>" +
          '<span style="margin-left:auto;color:var(--ok);font-weight:700">' +
          (standard.compliance != null ? standard.compliance + "%" : "—") +
          "</span></div>" +
          '<div style="font-size:.8rem;color:var(--muted)">' +
          ((standard.rules || []).join(" · ") || "暂无规则") +
          "</div></div>";
      });
      standardsEl.innerHTML = standardsHtml || '<div style="color:var(--muted)">暂无数据标准</div>';

      await loadDomainTables();
      await loadStepRecords();
    } catch (error) {
      console.error(error);
    }
  }

  async function loadDomainTables() {
    try {
      const response = await fetch(BASE + "/api/v1/dataplatform/tables");
      const data = await response.json();
      const el = document.getElementById("datahub-domains");
      const tables = data.tables || [];
      const domains = {};
      tables.forEach((table) => {
        if (!domains[table.domain]) domains[table.domain] = { tables: [], desc: "" };
        domains[table.domain].tables.push(table);
      });
      let html = "";
      Object.entries(domains).forEach(([domainKey, domainValue]) => {
        html +=
          '<div style="margin-bottom:14px"><div style="font-weight:600;color:var(--accent);margin-bottom:6px;cursor:pointer" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display===\'none\'?\'block\':\'none\'">' +
          domainKey +
          " (" +
          domainValue.tables.length +
          ' 张表) ▾</div>';
        html += '<table class="dtable" style="display:block"><thead><tr><th>表名</th><th>列</th><th>行数</th></tr></thead><tbody>';
        domainValue.tables.forEach((table) => {
          html +=
            '<tr style="cursor:pointer" onclick="showTableDetail(\'' +
            table.table +
            "','" +
            table.domain +
            "')\"><td style=\"font-family:monospace;font-size:.82rem;color:var(--accent)\">" +
            table.table +
            '</td><td style="font-size:.78rem;color:var(--muted)">' +
            table.columns.join(", ") +
            "</td><td>" +
            table.rows.toLocaleString() +
            "</td></tr>";
        });
        html += "</tbody></table></div>";
      });
      el.innerHTML = html || '<div style="color:var(--muted)">暂无数据域</div>';
    } catch (error) {
      document.getElementById("datahub-domains").innerHTML = '<div style="color:var(--danger)">加载失败</div>';
    }
  }

  async function showTableDetail(table, domain) {
    showModal(table, '<div style="text-align:center;color:var(--muted);padding:20px">加载中…</div>');
    try {
      const response = await fetch(
        BASE +
          "/api/v1/dataplatform/table-detail?table=" +
          encodeURIComponent(table) +
          "&domain=" +
          encodeURIComponent(domain)
      );
      const data = await response.json();
      if (data.error) {
        document.querySelector(".modal-body").innerHTML = '<div style="color:var(--danger)">' + data.error + "</div>";
        return;
      }
      let html = "";
      html += '<div class="modal-row"><div class="modal-label">表名</div><div class="modal-val" style="font-family:monospace;color:var(--accent)">' + data.table + "</div></div>";
      html += '<div class="modal-row"><div class="modal-label">数据域</div><div class="modal-val">' + data.domain + "</div></div>";
      html += '<div class="modal-row"><div class="modal-label">总行数</div><div class="modal-val" style="font-weight:600">' + (data.rows || 0).toLocaleString() + " 条</div></div>";
      const quality = data.quality || {};
      const scoreColor =
        quality.score >= 95 ? "var(--ok)" : quality.score >= 85 ? "var(--warn)" : "var(--danger)";
      html +=
        '<div class="modal-row"><div class="modal-label">数据质量</div><div class="modal-val"><span style="color:' +
        scoreColor +
        ';font-weight:700;font-size:1.1rem">' +
        quality.score +
        '%</span> <span style="color:var(--muted);font-size:.82rem">（' +
        quality.total +
        " 条记录，" +
        quality.issues +
        " 个问题）</span></div></div>";
      if (quality.checks && quality.checks.length) {
        html += '<div class="modal-row"><div class="modal-label">检查项</div><div class="modal-val" style="font-size:.82rem;color:var(--muted)">' + quality.checks.join(" · ") + "</div></div>";
      }
      const lineage = data.lineage || {};
      html += '<div class="modal-row"><div class="modal-label">数据上游</div><div class="modal-val">';
      (lineage.upstream || []).forEach((item) => {
        html += '<span class="badge running" style="margin:2px;font-size:.76rem">' + item + "</span>";
      });
      html += "</div></div>";
      html += '<div class="modal-row"><div class="modal-label">数据下游</div><div class="modal-val">';
      (lineage.downstream || []).forEach((item) => {
        html += '<span class="badge completed" style="margin:2px;font-size:.76rem">' + item + "</span>";
      });
      html += "</div></div>";
      html += '<div style="margin-top:14px"><div style="font-weight:600;margin-bottom:8px;font-size:.9rem">列结构（' + (data.columns || []).length + " 列）</div>";
      html += '<table class="dtable" style="font-size:.84rem"><thead><tr><th>列名</th><th>说明</th></tr></thead><tbody>';
      (data.columns || []).forEach((column) => {
        html +=
          '<tr><td style="font-family:monospace;color:var(--accent);width:180px">' +
          column.name +
          '</td><td style="color:var(--muted)">' +
          (column.description || "—") +
          "</td></tr>";
      });
      html += "</tbody></table></div>";
      document.querySelector(".modal-body").innerHTML = html;
    } catch (error) {
      document.querySelector(".modal-body").innerHTML =
        '<div style="color:var(--danger)">加载失败: ' + error.message + "</div>";
    }
  }

  async function loadStepRecords() {
    const agent = document.getElementById("dh-filter-agent")?.value || "";
    const tool = document.getElementById("dh-filter-tool")?.value || "";
    let url = BASE + "/api/v1/state/pipeline-step-history?limit=30&";
    if (agent) url += "agent=" + encodeURIComponent(agent) + "&";
    if (tool) url += "tool=" + encodeURIComponent(tool) + "&";
    try {
      const response = await fetch(url);
      const data = await response.json();
      const table = document.getElementById("datahub-steps");
      table.innerHTML = "";
      (data.records || []).slice(0, 30).forEach((step) => {
        if (!step.step_id && !step.agent) return;
        table.innerHTML +=
          '<tr><td style="font-family:monospace;font-size:.78rem">' +
          (step.step_key || step.step_id || "—") +
          "</td><td>" +
          (step.agent || "—") +
          "</td><td>" +
          (step.title || "—") +
          '</td><td style="font-size:.8rem">' +
          (step.tool || "—") +
          '</td><td><span class="badge ' +
          (step.status || "pending") +
          '">' +
          (step.status || "—") +
          '</span></td><td style="font-size:.78rem">' +
          ((step.completed_at || step.updated_at || "").replace("T", " ").slice(11, 19)) +
          "</td></tr>";
      });
      if (!data.records?.length) {
        table.innerHTML =
          '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:16px">暂无步骤记录（PostgreSQL 状态中心）</td></tr>';
      }
    } catch (error) {
      console.error(error);
    }
  }

  document.getElementById("export-training-btn").addEventListener("click", () => {
    window.open(BASE + "/api/v1/dataplatform/training-export?domain=all", "_blank");
  });

  window.loadDataHub = loadDataHub;
  window.showTableDetail = showTableDetail;
  window.loadStepRecords = loadStepRecords;
})();
