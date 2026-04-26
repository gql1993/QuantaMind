(function () {
  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatLocalTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  }

  function displayBackend(value) {
    return (
      {
        "live-rss": "arXiv RSS",
        "live-search-html": "arXiv Search",
        "live-api": "arXiv API",
        "live-openalex": "OpenAlex",
        "live-crossref": "Crossref",
        cache: "cache",
      }[value] ||
      value ||
      "unknown"
    );
  }

  function renderSummaryChips(el, counts, formatter) {
    if (!el) return;
    el.innerHTML = "";
    const entries = Object.entries(counts || {});
    if (!entries.length) {
      el.innerHTML = '<span class="intel-chip" style="color:var(--muted);border-color:var(--border);background:var(--surface2)">暂无</span>';
      return;
    }
    entries.forEach(([key, value]) => {
      const label = formatter ? formatter(key) : key;
      el.innerHTML += '<span class="intel-chip">' + escapeHtml(label) + " " + escapeHtml(value) + "篇</span>";
    });
  }

  function summarizePapers(papers, field) {
    const counts = {};
    (papers || []).forEach((paper) => {
      const key = paper && paper[field];
      if (!key) return;
      counts[key] = (counts[key] || 0) + 1;
    });
    return counts;
  }

  const INTEL_ROUTE_KIND_STYLES = {
    problem: { border: "#f87171", bg: "rgba(248,113,113,.14)" },
    method: { border: "#60a5fa", bg: "rgba(96,165,250,.12)" },
    implementation: { border: "#60a5fa", bg: "rgba(96,165,250,.1)" },
    evaluation: { border: "#a78bfa", bg: "rgba(167,139,250,.14)" },
    conclusion: { border: "#34d399", bg: "rgba(52,211,153,.14)" },
  };

  function renderTechRouteBlock(paper) {
    const graph = paper && paper.tech_route_graph;
    const nodes = graph && Array.isArray(graph.nodes) ? graph.nodes : [];
    if (!nodes.length) return "";
    const components = graph.components || [];
    const compLine =
      components.length > 0
        ? '<div class="intel-route-components">关键组件: ' +
          escapeHtml(components.slice(0, 6).join("、")) +
          "</div>"
        : "";
    const subTitle = paper.title
      ? '<div class="intel-route-subtitle">' + escapeHtml(paper.title) + "</div>"
      : "";
    let flow = '<div class="intel-route-flow">';
    nodes.forEach(function (node, idx) {
      const kind = node && node.kind;
      const st = INTEL_ROUTE_KIND_STYLES[kind] || INTEL_ROUTE_KIND_STYLES.method;
      if (idx > 0) {
        flow += '<span class="intel-route-arrow" aria-hidden="true">→</span>';
      }
      flow +=
        '<div class="intel-route-step" style="border-color:' +
        st.border +
        ";background:" +
        st.bg +
        '">' +
        '<div class="step-label">' +
        escapeHtml((node && node.label) || "") +
        "</div>" +
        '<div class="step-text">' +
        escapeHtml((node && node.text) || "—") +
        "</div></div>";
    });
    flow += "</div>";
    return (
      '<div class="intel-route-card">' +
      '<div class="intel-route-title">技术路线图</div>' +
      subTitle +
      compLine +
      flow +
      "</div>"
    );
  }

  function renderIntelPanel(data) {
    const latestReport = data.latest_report || null;
    const papers = data.recent_papers || [];
    const sourceSummary = data.source_summary || {};
    document.getElementById("intel-next-run").textContent = formatLocalTime(data.next_intel_run);
    document.getElementById("intel-last-report").textContent =
      (latestReport && latestReport.report_id) || data.last_intel_report_id || "—";
    document.getElementById("intel-papers-count").textContent = latestReport
      ? (latestReport.papers_count ?? "—") + " 篇"
      : papers.length + " 篇";
    renderSummaryChips(
      document.getElementById("intel-source-summary"),
      sourceSummary.source_counts || summarizePapers(papers, "source")
    );
    renderSummaryChips(
      document.getElementById("intel-backend-summary"),
      sourceSummary.backend_counts || summarizePapers(papers, "retrieval_backend"),
      displayBackend
    );

    const list = document.getElementById("intel-paper-list");
    const empty = document.getElementById("intel-empty");
    list.innerHTML = "";
    if (!papers.length) {
      empty.style.display = "block";
      return;
    }
    empty.style.display = "none";
    papers.slice(0, 5).forEach((paper) => {
      const topics = (paper.matched_topics || []).join(" / ") || "未分类";
      const source = paper.source || "arXiv";
      const backend = displayBackend(paper.retrieval_backend);
      list.innerHTML +=
        '<div class="intel-item">' +
        '<div class="intel-item-title">' +
        escapeHtml(paper.title || "未命名论文") +
        "</div>" +
        '<div class="intel-item-meta">' +
        '<span class="badge running">' + escapeHtml(source) + "</span>" +
        '<span class="badge completed">' + escapeHtml(backend) + "</span>" +
        '<span class="badge pending">' + escapeHtml(topics) + "</span>" +
        "</div>" +
        renderTechRouteBlock(paper) +
        '<div class="intel-item-summary">' +
        escapeHtml(paper.core_conclusion || paper.technical_route || paper.summary || "暂无摘要") +
        "</div>" +
        (paper.arxiv_url
          ? '<a class="intel-item-link" href="' + escapeHtml(paper.arxiv_url) + '" target="_blank" rel="noreferrer">查看论文</a>'
          : "") +
        "</div>";
    });
  }

  async function refreshDash() {
    try {
      const [statusResponse, debugResponse] = await Promise.all([
        fetch(BASE + "/api/v1/status"),
        fetch(BASE + "/api/v1/debug/status"),
      ]);
      const statusData = await statusResponse.json();
      const debugData = await debugResponse.json();
      try {
        const intelResponse = await fetch(BASE + "/api/v1/intel/overview?_bust=" + Date.now(), { cache: "no-store" });
        const intelData = await intelResponse.json();
        renderIntelPanel(intelData);
      } catch (_) {
        renderIntelPanel({});
      }
      const degraded = !!statusData.gateway?.degraded;
      document.getElementById("conn-dot").className = "dot " + (degraded ? "warn" : "ok");
      document.getElementById("conn-text").textContent = degraded ? "已连接（降级模式）" : "已连接";
      document.getElementById("uptime-text").textContent = "运行 " + debugData.uptime_human;
      document.getElementById("gw-st").textContent =
        (statusData.gateway?.status || "—") + (degraded ? " · 降级" : "");
      document.getElementById("gw-sess").textContent = statusData.sessions_count ?? "—";
      const heartbeat = statusData.heartbeat || {};
      document.getElementById("hb-lvl").textContent = heartbeat.level || "—";
      document.getElementById("hb-int").textContent = (heartbeat.interval_minutes || "—") + " 分钟";
      const tasks = statusData.tasks || {};
      document.getElementById("s-total").textContent = tasks.total ?? "—";
      document.getElementById("s-pending").textContent = tasks.pending ?? "—";
      document.getElementById("s-running").textContent = tasks.running ?? "—";
      document.getElementById("s-done").textContent = tasks.completed ?? "—";
      document.getElementById("s-appr").textContent = tasks.pending_approval ?? "—";
      document.getElementById("s-agents").textContent = debugData.agents_count ?? "—";
      document.getElementById("s-skills").textContent = statusData.skills_count ?? "—";
      document.getElementById("s-tools").textContent = statusData.tools_count ?? "—";
      const list = document.getElementById("plat-list");
      list.innerHTML = "";
      Object.entries(statusData.platforms || {}).forEach(([key, value]) => {
        list.innerHTML +=
          '<li class="platform-item"><span class="platform-dot ' +
          (value.status || "off") +
          '"></span><span class="platform-name">' +
          (value.name || key) +
          '</span><span class="platform-msg">' +
          (value.message || "") +
          "</span></li>";
      });
      if (degraded && !window._degradedToastShown) {
        showToast("QuantaMind 当前以降级模式运行：状态持久化不可用，核心页面仍可访问。", "warn", 2500);
        window._degradedToastShown = true;
      }
      if (!degraded) window._degradedToastShown = false;
      document.getElementById("dash-time").textContent =
        "上次刷新 " + new Date().toLocaleTimeString() + " · 每 5s";
    } catch (error) {
      document.getElementById("conn-dot").className = "dot off";
      document.getElementById("conn-text").textContent = "未连接";
    }
  }

  function shouldRefreshDash() {
    return !window.isPageActive || window.isPageActive("overview");
  }

  if (shouldRefreshDash()) refreshDash();
  setInterval(() => {
    if (shouldRefreshDash()) refreshDash();
  }, 5000);

  window.refreshDash = refreshDash;
})();
