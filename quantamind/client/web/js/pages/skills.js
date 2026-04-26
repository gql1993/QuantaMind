(function () {
  const skillSectionMap = {
    "skills-design": "skill-nav-design",
    "skills-sim": "skill-nav-sim",
    "skills-mes": "skill-nav-mes",
    "skills-measure": "skill-nav-measure",
    "skills-data": "skill-nav-data",
    "skills-project": "skill-nav-project",
  };

  let dbConnOverview = { configs: {}, statuses: {} };

  function updateSkillNavStickyState() {
    const page = document.getElementById("page-skills");
    const nav = page ? page.querySelector(".skills-nav-sticky") : null;
    const content = document.querySelector(".content");
    if (!page || !nav || !content) return;
    if (!page.classList.contains("active")) {
      nav.classList.remove("is-stuck");
      return;
    }
    const contentRect = content.getBoundingClientRect();
    const navRect = nav.getBoundingClientRect();
    const stuck = content.scrollTop > 0 && navRect.top <= contentRect.top + 1;
    nav.classList.toggle("is-stuck", stuck);
  }

  async function launchTool(tool) {
    try {
      const response = await fetch(BASE + "/api/v1/launch/" + tool);
      const data = await response.json();
      if (data.status === "launched") {
        showToast(tool.charAt(0).toUpperCase() + tool.slice(1) + " 已启动", "success");
      } else {
        showToast("启动失败：" + data.message, "error");
      }
    } catch (error) {
      showToast("启动失败：" + error.message, "error");
    }
  }

  async function enableChipmes() {
    const el = document.getElementById("chipmes-status");
    const resetBadge = () => {
      el.innerHTML =
        '<span class="badge completed" style="cursor:pointer" onclick="enableChipmes()" title="点击重试启动 CHIPMES">已安装，点击启用 CHIPMES ↗</span>';
    };
    try {
      el.innerHTML = '<span class="badge pending">启动中…</span>';
      const response = await fetch(BASE + "/api/v1/chipmes/start", { method: "POST" });
      if (!response.ok) {
        resetBadge();
        const text = await response.text();
        let message = "HTTP " + response.status;
        try {
          const parsed = JSON.parse(text);
          message = parsed.detail || parsed.message || message;
        } catch (error) {
          console.error(error);
        }
        showToast("启动失败：" + message + "（请重启 QuantaMind Gateway 加载新端点）", "error");
        return;
      }
      const data = await response.json();
      if (data.status === "already_running") {
        el.innerHTML = '<span class="badge completed">已连接（端口8082）</span>';
        showToast("CHIPMES 已在运行", "success");
        return;
      }
      if (data.status === "starting") {
        showToast("CHIPMES 启动中，Spring Boot 应用约需 15-30 秒", "success");
        let tries = 0;
        const poll = setInterval(async () => {
          tries += 1;
          el.innerHTML = '<span class="badge pending">启动中…（' + tries * 5 + "s）</span>";
          try {
            const checkResponse = await fetch(BASE + "/api/v1/chipmes/info");
            const checkInfo = await checkResponse.json();
            if (checkInfo.connected) {
              clearInterval(poll);
              el.innerHTML = '<span class="badge completed">已连接（端口8082）</span>';
              showToast("CHIPMES 已成功连接", "success");
            } else if (tries >= 18) {
              clearInterval(poll);
              resetBadge();
              showToast("CHIPMES 启动超时（90s），请检查 console.log 或手动重试", "error");
            }
          } catch (error) {
            if (tries >= 18) {
              clearInterval(poll);
              resetBadge();
            }
          }
        }, 5000);
      } else if (data.status === "deps_missing") {
        resetBadge();
        showToast(data.message, "error");
      } else if (data.status === "startup_failed") {
        resetBadge();
        showToast("启动失败：" + (data.message || "CHIPMES 进程启动后立即退出"), "error");
      } else if (data.status === "error") {
        resetBadge();
        showToast("启动失败：" + data.message, "error");
      } else {
        resetBadge();
        showToast("启动失败：" + JSON.stringify(data), "error");
      }
    } catch (error) {
      resetBadge();
      showToast("请求失败：请确认 QuantaMind Gateway 已启动（" + error.message + "）", "error");
    }
  }

  function setActiveSkillNav(sectionId) {
    document.querySelectorAll(".skill-nav-btn").forEach((btn) => {
      btn.classList.remove("btn-primary");
      btn.classList.add("btn");
      btn.setAttribute("aria-current", "false");
    });
    const activeId = skillSectionMap[sectionId];
    const activeBtn = activeId ? document.getElementById(activeId) : null;
    if (activeBtn) {
      activeBtn.classList.remove("btn");
      activeBtn.classList.add("btn-primary");
      activeBtn.setAttribute("aria-current", "true");
    }
  }

  function scrollToSkillSection(id) {
    const el = document.getElementById(id);
    if (el) {
      setActiveSkillNav(id);
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function observeSkillSections() {
    const page = document.getElementById("page-skills");
    if (!page || !("IntersectionObserver" in window)) return;
    const ids = Object.keys(skillSectionMap);
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => Math.abs(a.boundingClientRect.top) - Math.abs(b.boundingClientRect.top));
        if (visible.length) setActiveSkillNav(visible[0].target.id);
      },
      { root: null, rootMargin: "-20% 0px -65% 0px", threshold: [0, 1] }
    );
    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    setActiveSkillNav("skills-design");
  }

  function bindSkillNavStickyState() {
    const content = document.querySelector(".content");
    if (content) {
      content.addEventListener("scroll", updateSkillNavStickyState, { passive: true });
    }
    window.addEventListener("resize", updateSkillNavStickyState);
    window.addEventListener("quantamind:pagechange", updateSkillNavStickyState);
    requestAnimationFrame(updateSkillNavStickyState);
  }

  function triggerSkill(prompt) {
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
    document.querySelector('[data-page="chat"]').classList.add("active");
    document.querySelectorAll(".page").forEach((page) => page.classList.remove("active"));
    document.getElementById("page-chat").classList.add("active");
    document.getElementById("chat-in").value = prompt;
    document.getElementById("chat-in").focus();
  }

  function renderDbConnDetail(key) {
    const cfg = dbConnOverview.configs?.[key] || {};
    const st = dbConnOverview.statuses?.[key] || {};
    const title = (st.label || key) + " 详情";
    const cfgRows = [];
    if (cfg.host) cfgRows.push("host: " + cfg.host);
    if (cfg.port) cfgRows.push("port: " + cfg.port);
    if (cfg.database) cfgRows.push("database: " + cfg.database);
    if (cfg.user) cfgRows.push("user: " + cfg.user);
    if (cfg.base_url) cfgRows.push("base_url: " + cfg.base_url);
    if (cfg.endpoint) cfgRows.push("endpoint: " + cfg.endpoint);
    if (cfg.bucket) cfgRows.push("bucket: " + cfg.bucket);
    if (cfg.table) cfgRows.push("table: " + cfg.table);
    if (cfg.dimensions) cfgRows.push("dimensions: " + cfg.dimensions);
    const checked = st.checked_at ? new Date(st.checked_at).toLocaleString() : "—";
    const statusRows = ["状态: " + (st.connected ? "已连接" : "未连接"), "结果: " + (st.detail || "—"), "最近检测: " + checked];
    if (st.checked?.length) {
      statusRows.push("探测端点:");
      st.checked.slice(0, 4).forEach((item) => {
        statusRows.push((item.url || "") + " -> " + (item.status_code || item.error || ""));
      });
    }
    document.getElementById("db-conn-detail-title").textContent = title;
    document.getElementById("db-conn-detail-config").innerHTML = cfgRows.join("<br>") || "—";
    document.getElementById("db-conn-detail-status").innerHTML = statusRows.join("<br>");
  }

  function showDbConnDetail(key) {
    document.querySelectorAll(".db-conn-card").forEach((el) => {
      el.style.boxShadow = "none";
    });
    const activeMap = {
      design_postgres: "db-card-designpg",
      mes_sqlserver: "db-card-messql",
      storage_minio: "db-card-minio",
      ai_pgvector: "db-card-pgvector",
    };
    const el = document.getElementById(activeMap[key]);
    if (el) {
      el.style.boxShadow = "0 0 0 1px var(--accent), 0 0 0 3px rgba(87,148,242,.15)";
    }
    renderDbConnDetail(key);
  }

  async function loadQedaStatus() {
    try {
      const [response, klayoutResponse] = await Promise.all([
        fetch(BASE + "/api/v1/qeda/capabilities"),
        fetch(BASE + "/api/v1/klayout/status"),
      ]);
      const data = await response.json();
      const klayoutData = klayoutResponse.ok ? await klayoutResponse.json() : {};
      const metal = data.qiskit_metal || {};
      const kqcircuits = data.kqcircuits || {};
      document.getElementById("metal-status").innerHTML = metal.installed
        ? '<span class="badge completed" title="Qiskit Metal 为 Python 库，请在终端中使用">已安装（Python 库）</span>'
        : '<span class="badge pending">未安装（Mock 模式）</span>';
      if (kqcircuits.installed && klayoutData.launchable) {
        document.getElementById("kqc-status").innerHTML =
          '<span class="badge completed" title="KQCircuits 已安装，点击启动 KLayout" style="cursor:pointer" onclick="launchTool(\'klayout\')">已安装 · 点击启动 KLayout ↗</span>';
      } else if (kqcircuits.installed) {
        document.getElementById("kqc-status").innerHTML =
          '<span class="badge completed" title="KQCircuits 已安装，但当前未检测到可启动的桌面版 KLayout">已安装（需 KLayout 桌面版）</span>';
      } else {
        document.getElementById("kqc-status").innerHTML = '<span class="badge pending">未安装（Mock 模式）</span>';
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function loadAnsysStatus() {
    try {
      let ansysOk = false;
      let ansysLaunchable = false;
      let offlineMode = false;
      try {
        const response = await fetch(BASE + "/api/v1/sim/status");
        if (response.ok) {
          const data = await response.json();
          ansysOk = data.ansys_desktop_installed || false;
          ansysLaunchable = data.ansys_launchable || false;
          offlineMode = !!data.pyaedt_installed && !ansysOk;
        }
      } catch (error) {
        ansysOk = false;
      }
      const el = document.getElementById("ansys-status");
      if (!el) return;
      if (ansysOk && ansysLaunchable) {
        el.innerHTML =
          '<span class="badge completed" style="cursor:pointer" onclick="launchTool(\'ansys\')" title="点击启动 Ansys Electronics Desktop">已安装 · 点击启动 Ansys ↗</span>';
      } else if (ansysOk) {
        el.innerHTML =
          '<span class="badge completed" title="检测到 Ansys 环境，但未找到可启动的桌面程序">已安装（未找到启动程序）</span>';
      } else if (offlineMode) {
        el.innerHTML = '<span class="badge pending">未安装桌面端（离线模式）</span>';
      } else {
        el.innerHTML = '<span class="badge pending">未安装（理论计算模式）</span>';
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function loadKlayoutStatus() {
    try {
      const response = await fetch(BASE + "/api/v1/klayout/status");
      const el = document.getElementById("klayout-status");
      if (response.ok) {
        const data = await response.json();
        if (!el) return;
        if (data.launchable) {
          el.innerHTML =
            '<span class="badge completed" style="cursor:pointer" onclick="launchTool(\'klayout\')" title="点击启动 KLayout">已安装 · 点击启动 KLayout ↗</span>';
        } else if (data.installed) {
          el.innerHTML =
            '<span class="badge completed" title="' +
            (data.message || "已安装 Python 模块，但未检测到可启动的桌面版 KLayout") +
            '">已安装（无桌面程序）</span>';
        } else {
          el.innerHTML = '<span class="badge pending">未安装</span>';
        }
      } else if (el) {
        el.innerHTML = '<span class="badge pending">检测中...</span>';
      }
    } catch (error) {
      const el = document.getElementById("klayout-status");
      if (el) el.innerHTML = '<span class="badge pending">检测中...</span>';
    }
  }

  async function loadDataPlatformStatus() {
    try {
      const [statusResponse, configResponse] = await Promise.all([
        fetch(BASE + "/api/v1/config/databases/status"),
        fetch(BASE + "/api/v1/config/databases"),
      ]);
      const statusData = await statusResponse.json();
      const configData = await configResponse.json();
      dbConnOverview = { configs: configData.configs || {}, statuses: statusData.statuses || {} };
      const statuses = dbConnOverview.statuses;
      const mk = (value) =>
        '<span class="badge ' +
        (value?.connected ? "completed" : "pending") +
        '">' +
        (value?.connected
          ? "已连接 · " + (value.detail || "")
          : "未连接" + (value?.detail ? " · " + value.detail : "")) +
        "</span>";
      document.getElementById("designpg-status").innerHTML = mk(statuses.design_postgres);
      document.getElementById("messql-status").innerHTML = mk(statuses.mes_sqlserver);
      document.getElementById("minio-status").innerHTML = mk(statuses.storage_minio);
      document.getElementById("pgvector-status").innerHTML = mk(statuses.ai_pgvector);
      showDbConnDetail("design_postgres");
    } catch (error) {
      console.error(error);
    }
  }

  async function loadMeasureStatus() {
    try {
      const response = await fetch(BASE + "/api/v1/measure/capabilities");
      const data = await response.json();
      document.getElementById("artiq-status").innerHTML =
        '<span class="badge ' +
        (data.artiq?.installed ? "completed" : "pending") +
        '">' +
        (data.artiq?.installed ? "已安装" : "Mock 模式") +
        "</span>";
      document.getElementById("qexp-status").innerHTML =
        '<span class="badge ' +
        (data.qiskit_experiments?.installed ? "completed" : "pending") +
        '">' +
        (data.qiskit_experiments?.installed ? "已安装" : "标准实验层（Mock 分析）") +
        "</span>";
      document.getElementById("pulse-status").innerHTML =
        '<span class="badge ' +
        (data.qiskit_pulse?.installed ? "completed" : "pending") +
        '">' +
        (data.qiskit_pulse?.installed ? "已安装" : "Mock 模式") +
        "</span>";
      document.getElementById("mitiq-status").innerHTML =
        '<span class="badge ' +
        (data.mitiq?.installed ? "completed" : "pending") +
        '">' +
        (data.mitiq?.installed ? "已安装" : "Mock 模式") +
        "</span>";
    } catch (error) {
      console.error(error);
    }
  }

  async function loadMesStatus() {
    try {
      const [mesResponse, chipmesResponse] = await Promise.all([
        fetch(BASE + "/api/v1/mes/capabilities"),
        fetch(BASE + "/api/v1/chipmes/info").catch(() => ({ json: () => ({}) })),
      ]);
      const mesData = await mesResponse.json();
      const chipmesData = await chipmesResponse.json();
      const secs = mesData.secsgem || {};
      const openmes = mesData.openmes || {};
      const grafana = mesData.grafana || {};
      const chipmesConnected = chipmesData.connected || false;
      document.getElementById("chipmes-status").innerHTML = chipmesConnected
        ? '<span class="badge completed">已连接（端口8082）</span>'
        : '<span class="badge completed" style="cursor:pointer" onclick="enableChipmes()" title="点击启动 CHIPMES 系统">已安装，点击启用 CHIPMES ↗</span>';
      document.getElementById("secs-status").innerHTML =
        '<span class="badge ' +
        (secs.installed ? "completed" : "pending") +
        '">' +
        (secs.installed ? "已安装" : "Mock 模式") +
        "</span>";
      document.getElementById("mes-status").innerHTML =
        '<span class="badge ' +
        (openmes.connected ? "completed" : "pending") +
        '">' +
        (openmes.connected ? "已连接" : "Mock 模式") +
        "</span>";
      document.getElementById("grafana-status").innerHTML =
        '<span class="badge ' +
        (grafana.connected ? "completed" : "pending") +
        '">' +
        (grafana.connected ? "已连接" : "Mock 模式") +
        "</span>";
    } catch (error) {
      console.error(error);
    }
  }

  observeSkillSections();
  bindSkillNavStickyState();
  let skillsPageLoaded = false;
  function loadSkillsPage() {
    if (skillsPageLoaded) return;
    skillsPageLoaded = true;
    loadQedaStatus();
    loadAnsysStatus();
    loadKlayoutStatus();
    loadDataPlatformStatus();
    loadMeasureStatus();
    loadMesStatus();
  }
  window.addEventListener("quantamind:pagechange", (event) => {
    if (event.detail && event.detail.page === "skills") loadSkillsPage();
  });
  if (!window.isPageActive || window.isPageActive("skills")) loadSkillsPage();

  window.launchTool = launchTool;
  window.enableChipmes = enableChipmes;
  window.scrollToSkillSection = scrollToSkillSection;
  window.triggerSkill = triggerSkill;
  window.showDbConnDetail = showDbConnDetail;
  window.loadSkillsPage = loadSkillsPage;
})();
