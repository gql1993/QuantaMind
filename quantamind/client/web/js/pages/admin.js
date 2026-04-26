(function () {
  let taskFilter = "all";
  let agentsData = [];
  let toolCatalog = {};
  let skillCatalog = [];
  const TASK_FOCUS_KEY = "quantamind_focus_task_id";
  const TASK_FLASH_KEY = "quantamind_focus_task_flash";
  const AGENT_SECTION_MAP = {
    chief_scientist: "skills-project",
    theorist: "skills-sim",
    chip_designer: "skills-design",
    simulation_engineer: "skills-sim",
    material_scientist: "skills-data",
    process_engineer: "skills-mes",
    device_ops: "skills-measure",
    measure_scientist: "skills-measure",
    algorithm_engineer: "skills-project",
    data_analyst: "skills-data",
    intel_officer: "skills-data",
    knowledge_engineer: "skills-data",
    project_manager: "skills-project",
  };
  const SECTION_LABEL_MAP = {
    "skills-design": "芯片设计",
    "skills-sim": "仿真验证",
    "skills-mes": "制造执行",
    "skills-measure": "测控校准",
    "skills-data": "数据与知识",
    "skills-project": "项目协同",
  };

  function getSubAgents(agent) {
    if (!agent) return [];
    const raw = agent.sub_agents ?? agent.subAgents;
    return Array.isArray(raw) ? raw : [];
  }

  /** 与 gateway.py process_engineer.sub_agents 同步；仅当 API 未返回 sub_agents 时使用（旧进程/缓存） */
  const PROCESS_ENGINEER_SUB_AGENTS_FALLBACK = [
    {
      id: "mes_equipment_engineer",
      label: "MES 设备工程师",
      role: "机台与 SECS/GEM",
      desc: "聚焦制造执行系统侧机台：设备枚举与在线状态、远程命令、配方列表与下发路径、告警闭环；配合 Grafana 机台监控与嵌入看板。",
      tools: [
        "secs_list_equipment",
        "secs_equipment_status",
        "secs_remote_command",
        "secs_list_alarms",
        "secs_get_recipes",
        "grafana_list_dashboards",
        "grafana_embed_url",
        "grafana_create_equipment_dashboard",
      ],
      skills: [
        "设备在线与状态诊断",
        "SECS/GEM 远程命令与配方管理",
        "设备告警分级与处置闭环",
        "机台监控大屏与嵌入",
      ],
    },
    {
      id: "mes_process_specialist",
      label: "工艺工程师",
      role: "路线与工艺窗口",
      desc: "负责工艺路线、站点顺序与工艺窗口；批次/工单派工与报工对齐机台配方，保障工艺参数在 MES 与现场一致。",
      tools: [
        "mes_list_routes",
        "mes_list_lots",
        "mes_get_lot",
        "mes_list_work_orders",
        "mes_dispatch",
        "mes_report_work",
        "secs_get_recipes",
      ],
      skills: ["工艺路线与站点编排", "批次派工与完工报工", "工艺窗口与配方对齐", "在制批次状态追踪"],
    },
    {
      id: "mes_defect_analyst",
      label: "缺陷分析工程师",
      role: "失效与根因",
      desc: "结合良率分层、SPC 失控与批次履历，定位缺陷模式与可疑工艺站点，输出可验证的根因假设与复现路径。",
      tools: ["mes_query_yield", "mes_query_spc", "mes_get_lot", "mes_list_lots"],
      skills: [
        "良率异常与缺陷模式识别",
        "SPC 失控与特殊原因分析",
        "批次—站点—参数追溯",
        "失效假设与验证清单",
      ],
    },
    {
      id: "mes_yield_engineer",
      label: "良率工程师",
      role: "良率与统计",
      desc: "负责良率指标定义、趋势与分层（站点/产品/时间）；维护控制图与规格限，支撑良率目标与改善闭环。",
      tools: ["mes_query_yield", "mes_query_spc", "mes_get_lot", "mes_list_lots"],
      skills: ["良率趋势与分层统计", "控制图与过程能力", "规格限与判异规则", "良率目标分解与追踪"],
    },
    {
      id: "mes_pie",
      label: "制程整合工程师",
      role: "跨站整合",
      desc: "打通多站点瓶颈与资源约束，协调设备状态、工艺窗口与良率结果，推动跨模块问题升级与一体化改善方案。",
      tools: [
        "mes_list_routes",
        "mes_list_lots",
        "mes_get_lot",
        "mes_query_yield",
        "mes_query_spc",
        "mes_dispatch",
        "secs_list_equipment",
        "secs_equipment_status",
        "secs_list_alarms",
        "grafana_list_dashboards",
        "grafana_embed_url",
      ],
      skills: [
        "跨站瓶颈与产能平衡",
        "设备—工艺—良率联动分析",
        "制程窗口整合与风险评审",
        "一体化改善与升级路径",
      ],
    },
    {
      id: "mes_test_engineer",
      label: "测试工程师",
      role: "测试与数据 gate",
      desc: "负责测试站点报工、测试结果与良率 gate 核对，保证测试数据进入 MES 履历完整、可追溯，支撑放行与返工决策。",
      tools: ["mes_report_work", "mes_get_lot", "mes_list_work_orders", "mes_query_yield", "mes_list_lots"],
      skills: ["测试程序与站点报工", "良率 gate 与规格核对", "测试数据完整性与追溯", "放行/返工数据支撑"],
    },
  ];

  function normalizeProcessEngineerAgent(agent) {
    if (!agent || agent.id !== "process_engineer") return agent;
    const next = { ...agent };
    if (next.label === "AI 工艺工程师") next.label = "AI 制造工程师";
    if (next.role === "制造") next.role = "制造（多子智能体）";
    if (!getSubAgents(next).length) {
      next.sub_agents = PROCESS_ENGINEER_SUB_AGENTS_FALLBACK;
    }
    return next;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function normalizeName(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[\s_\-()（）/]/g, "");
  }

  function getAgentStatusLabel(status) {
    return status === "active" ? "在线" : "待命";
  }

  function getAgentSection(agent, fallbackName) {
    if (agent?.id && AGENT_SECTION_MAP[agent.id]) return AGENT_SECTION_MAP[agent.id];
    const name = String(fallbackName || "");
    if (/^(metal_|kqc_|qeda_)/.test(name)) return "skills-design";
    if (/^(sim_|theorist_)/.test(name)) return "skills-sim";
    if (/^(mes_|secs_|chipmes_|grafana_)/.test(name)) return "skills-mes";
    if (/^(artiq_|pulse_|mitiq_)/.test(name)) return "skills-measure";
    if (/^(warehouse_|qdata_|seatunnel_|qcodes_|knowledge_|intel_)/.test(name)) return "skills-data";
    return "skills-project";
  }

  function openPromptInChat(prompt) {
    if (!prompt) return;
    goToPage("chat");
    const input = document.getElementById("chat-in");
    if (input) {
      input.value = prompt;
      input.focus();
    }
  }

  function selectAgentCard(agentId) {
    document.querySelectorAll(".agent-card").forEach((card) => {
      card.classList.toggle("selected", card.dataset.agentId === agentId);
    });
  }

  function getPrimaryRunPrompt(agent) {
    const firstAction = (agent.actions || [])[0];
    return firstAction?.prompt || ("请立即执行 " + (agent.label || "该智能体") + " 的核心任务。");
  }

  function getHistoryPrompt(agent) {
    const historyAction = (agent.actions || []).find((action) => /历史|记录|日报|报告|近期|状态/.test(action.label || ""));
    return (
      historyAction?.prompt ||
      ("请汇总 " + (agent.label || "该智能体") + " 最近的历史记录、报告、关键输出与执行状态。")
    );
  }

  function findSkillDefinition(skillName) {
    const normalized = normalizeName(skillName);
    return skillCatalog.find((skill) => {
      const name = normalizeName(skill.name || skill._id || "");
      if (name && (name === normalized || name.includes(normalized) || normalized.includes(name))) return true;
      const triggers = []
        .concat(skill.trigger || [])
        .concat(skill.triggers || [])
        .join("|");
      return normalizeName(triggers).includes(normalized);
    });
  }

  function linkAgentForDetail() {
    return {
      status: "active",
      id: "deeplink",
      label: "（链接）",
      role: "",
      desc: "",
      platforms: "—",
      tools: [],
      skills: [],
      actions: [],
    };
  }

  function getToolMeta(agent, toolName) {
    const tool = toolCatalog[toolName];
    const agentOk = !agent || agent.status === "active";
    const available = agentOk && !!tool;
    const reason = !agentOk
      ? "当前智能体处于待命状态"
      : tool
        ? ""
        : "当前工具未注册到执行层";
    const sectionId = getAgentSection(agent, toolName);
    const sectionLabel = SECTION_LABEL_MAP[sectionId] || "相关";
    return {
      name: toolName,
      description: tool?.description || "查看工具详情并进入相关运行能力页。",
      available,
      reason,
      sectionId,
      sectionLabel,
      tooltip: available
        ? "点击查看工具详情并跳转到" + sectionLabel + "能力页"
        : "当前不可用：" + reason,
    };
  }

  function getSkillMeta(agent, skillName) {
    const definition = findSkillDefinition(skillName);
    const available = !agent || agent.status === "active";
    const reason = available ? "" : "当前智能体处于待命状态";
    const sectionId = getAgentSection(agent, skillName);
    const sectionLabel = SECTION_LABEL_MAP[sectionId] || "相关";
    return {
      name: skillName,
      description: definition?._body || "查看技能说明、触发条件与配置入口。",
      available,
      reason,
      sectionId,
      sectionLabel,
      tooltip: available
        ? "点击查看技能详情并跳转到" + sectionLabel + "配置页"
        : "当前不可用：" + reason,
    };
  }

  function renderInteractiveTag(type, agentIndex, itemName, meta) {
    return (
      '<button type="button" class="agent-chip ' +
      type +
      (meta.available ? "" : " unavailable") +
      '" data-agent-idx="' +
      agentIndex +
      '" data-name="' +
      escapeHtml(itemName) +
      '" title="' +
      escapeHtml(meta.tooltip) +
      '">' +
      escapeHtml(itemName) +
      "</button>"
    );
  }

  function renderTagGroup(type, agent, agentIndex, items) {
    if (!items?.length) {
      return '<span class="agent-empty">—</span>';
    }
    return items
      .map((itemName) => {
        const meta = type === "tool" ? getToolMeta(agent, itemName) : getSkillMeta(agent, itemName);
        return renderInteractiveTag(type, agentIndex, itemName, meta);
      })
      .join("");
  }

  function aggregatedToolSkillCounts(agent) {
    const subs = getSubAgents(agent);
    if (!subs.length) {
      return { toolCount: (agent.tools || []).length, skillCount: (agent.skills || []).length };
    }
    const tools = new Set(agent.tools || []);
    const skills = new Set(agent.skills || []);
    subs.forEach((sub) => {
      (sub.tools || []).forEach((t) => tools.add(t));
      (sub.skills || []).forEach((s) => skills.add(s));
    });
    return { toolCount: tools.size, skillCount: skills.size };
  }

  /** 多子智能体 Agent 在子分工之下的顶层工具/技能（与情报员、制造工程师等一致） */
  function renderParentUmbrellaHtml(agent, parentIndex) {
    return (
      '<div class="agent-umbrella-capability" style="margin-top:14px;padding-top:12px;border-top:1px solid var(--border)">' +
      '<div class="stat-label" style="margin-bottom:8px;color:var(--muted);font-size:.78rem">统筹（顶层入口，与子智能体分工互补）</div>' +
      '<div class="agent-meta-block"><div class="stat-label" style="margin-bottom:6px">统筹 · 可用工具</div><div class="agent-chip-row">' +
      renderTagGroup("tool", agent, parentIndex, agent.tools || []) +
      '</div></div><div class="agent-meta-block"><div class="stat-label" style="margin-bottom:6px">统筹 · 触发技能</div><div class="agent-chip-row">' +
      renderTagGroup("skill", agent, parentIndex, agent.skills || []) +
      "</div></div></div>"
    );
  }

  function renderSubAgentsExpandedHtml(agent, parentIndex) {
    return getSubAgents(agent)
      .map(
        (sub) =>
          '<div class="agent-subagent-block">' +
          '<div class="agent-subagent-head"><span class="agent-subagent-name">' +
          escapeHtml(sub.label || "") +
          '</span><span class="agent-subagent-role">' +
          escapeHtml(sub.role || "") +
          "</span></div>" +
          '<div class="agent-subagent-desc">' +
          escapeHtml(sub.desc || "") +
          '</div><div class="agent-meta-block"><div class="stat-label" style="margin-bottom:6px">可用工具</div><div class="agent-chip-row">' +
          renderTagGroup("tool", agent, parentIndex, sub.tools || []) +
          '</div></div><div class="agent-meta-block"><div class="stat-label" style="margin-bottom:6px">触发技能</div><div class="agent-chip-row">' +
          renderTagGroup("skill", agent, parentIndex, sub.skills || []) +
          "</div></div></div>"
      )
      .join("");
  }

  function bindInteractiveTags(root) {
    if (!root) return;
    root.querySelectorAll(".agent-chip.tool").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const agent = agentsData[parseInt(button.dataset.agentIdx, 10)];
        if (agent) openToolTag(agent, button.dataset.name || "");
      });
    });
    root.querySelectorAll(".agent-chip.skill").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const agent = agentsData[parseInt(button.dataset.agentIdx, 10)];
        if (agent) openSkillTag(agent, button.dataset.name || "");
      });
    });
  }

  function renderQuickActions(agent) {
    if (!(agent.actions || []).length) {
      return '<div class="agent-empty">暂无快捷动作</div>';
    }
    return (agent.actions || [])
      .map(
        (action) =>
          '<button type="button" class="btn agent-quick-btn" data-prompt="' +
          escapeHtml(action.prompt || "") +
          '" title="将动作提示词带入对话页">' +
          escapeHtml(action.label || "快捷动作") +
          "</button>"
      )
      .join("");
  }

  function bindQuickActions(root) {
    if (!root) return;
    root.querySelectorAll(".agent-quick-btn").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        openPromptInChat(button.dataset.prompt || "");
      });
    });
  }

  function bindAgentCardCollapse(root) {
    if (!root) return;
    root.querySelectorAll(".agent-card").forEach((card) => {
      const expandBtn = card.querySelector(".agent-card-expand-btn");
      const collapseBtn = card.querySelector(".agent-card-collapse-btn");
      const compact = card.querySelector(".agent-card-compact");
      function expandCard() {
        card.classList.remove("is-collapsed");
      }
      function collapseCard() {
        card.classList.add("is-collapsed");
      }
      if (expandBtn) {
        expandBtn.addEventListener("click", (event) => {
          event.stopPropagation();
          expandCard();
        });
      }
      if (collapseBtn) {
        collapseBtn.addEventListener("click", (event) => {
          event.stopPropagation();
          collapseCard();
        });
      }
      if (compact) {
        compact.addEventListener("click", (event) => {
          if (!card.classList.contains("is-collapsed")) return;
          if (event.target.closest(".agent-card-expand-btn")) return;
          expandCard();
        });
      }
    });
  }

  async function ensureToolSkillCatalog() {
    if (Object.keys(toolCatalog).length && skillCatalog.length) return;
    try {
      const [toolsResponse, skillsResponse] = await Promise.all([
        fetch(BASE + "/api/v1/tools"),
        fetch(BASE + "/api/v1/skills"),
      ]);
      const toolsPayload = await toolsResponse.json();
      const skillsPayload = await skillsResponse.json();
      toolCatalog = Object.fromEntries((toolsPayload.tools || []).map((tool) => [tool.name, tool]));
      skillCatalog = skillsPayload.skills || [];
    } catch (error) {
      console.error(error);
    }
  }

  function closeAgentDrawer() {
    const overlay = document.getElementById("agent-drawer-overlay");
    if (overlay) {
      overlay.classList.remove("open");
      overlay.setAttribute("aria-hidden", "true");
    }
  }

  function openAgentDrawer(opts) {
    const overlay = document.getElementById("agent-drawer-overlay");
    if (!overlay) return;
    const titleEl = document.getElementById("drawer-title-text");
    const subEl = document.getElementById("drawer-subtitle-text");
    const bodyEl = document.getElementById("agent-drawer-body");
    const footEl = document.getElementById("agent-drawer-footer");
    if (titleEl) titleEl.textContent = opts.title || "详情";
    if (subEl) subEl.textContent = opts.subtitle || "";
    if (bodyEl) bodyEl.innerHTML = opts.bodyHtml || "";
    if (footEl) {
      footEl.innerHTML = "";
      if (opts.onBuildFooter) opts.onBuildFooter(footEl);
      else {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn";
        btn.textContent = "关闭";
        btn.addEventListener("click", () => closeAgentDrawer());
        footEl.appendChild(btn);
      }
    }
    overlay.classList.add("open");
    overlay.setAttribute("aria-hidden", "false");
  }

  function openAgentDrawerForTool(agent, toolName, meta) {
    const body =
      '<div class="drawer-section"><h4>说明</h4><div>' +
      escapeHtml(meta.description) +
      "</div></div>" +
      '<div class="drawer-section"><h4>上下文</h4><div class="drawer-kv">' +
      '<div><span>关联智能体</span><span>' +
      escapeHtml(agent.label || "—") +
      "</span></div>" +
      '<div><span>能力分区</span><span>' +
      escapeHtml(meta.sectionLabel) +
      "</span></div></div></div>";
    openAgentDrawer({
      title: toolName,
      subtitle: meta.available ? "工具 · 已注册" : "工具 · 不可用",
      bodyHtml: body,
      onBuildFooter(foot) {
        if (meta.available) {
          const full = document.createElement("button");
          full.type = "button";
          full.className = "btn btn-primary";
          full.textContent = "打开独立详情页";
          full.addEventListener("click", () => {
            closeAgentDrawer();
            window._pendingToolDetail = { agent, toolName };
            if (history.replaceState) {
              history.replaceState(null, "", "#tool/" + encodeURIComponent(toolName));
            }
            goToPage("tool-detail");
          });
          foot.appendChild(full);
          const gotoSkills = document.createElement("button");
          gotoSkills.type = "button";
          gotoSkills.className = "btn";
          gotoSkills.textContent = "前往能力分区";
          gotoSkills.addEventListener("click", () => {
            closeAgentDrawer();
            goToPage("skills");
            setTimeout(() => {
              if (window.scrollToNavGroup) window.scrollToNavGroup("capability");
              if (window.scrollToSkillSection) window.scrollToSkillSection(meta.sectionId);
            }, 30);
            showToast("已定位到「" + meta.sectionLabel + "」", "ok");
          });
          foot.appendChild(gotoSkills);
        }
        const closeBtn = document.createElement("button");
        closeBtn.type = "button";
        closeBtn.className = "btn";
        closeBtn.textContent = "关闭";
        closeBtn.addEventListener("click", () => closeAgentDrawer());
        foot.appendChild(closeBtn);
      },
    });
  }

  function openAgentDrawerForSkill(agent, skillName, meta) {
    const body =
      '<div class="drawer-section"><h4>说明与触发</h4><div>' +
      escapeHtml(meta.description) +
      "</div></div>" +
      '<div class="drawer-section"><h4>上下文</h4><div class="drawer-kv">' +
      '<div><span>关联智能体</span><span>' +
      escapeHtml(agent.label || "—") +
      "</span></div>" +
      '<div><span>能力分区</span><span>' +
      escapeHtml(meta.sectionLabel) +
      "</span></div></div></div>";
    openAgentDrawer({
      title: skillName,
      subtitle: meta.available ? "技能 · 可配置" : "技能 · 不可用",
      bodyHtml: body,
      onBuildFooter(foot) {
        if (meta.available) {
          const full = document.createElement("button");
          full.type = "button";
          full.className = "btn btn-primary";
          full.textContent = "打开独立详情页";
          full.addEventListener("click", () => {
            closeAgentDrawer();
            window._pendingSkillDetail = { agent, skillName };
            if (history.replaceState) {
              history.replaceState(null, "", "#skill/" + encodeURIComponent(skillName));
            }
            goToPage("skill-detail");
          });
          foot.appendChild(full);
          const gotoSkills = document.createElement("button");
          gotoSkills.type = "button";
          gotoSkills.className = "btn";
          gotoSkills.textContent = "前往能力分区";
          gotoSkills.addEventListener("click", () => {
            closeAgentDrawer();
            goToPage("skills");
            setTimeout(() => {
              if (window.scrollToNavGroup) window.scrollToNavGroup("capability");
              if (window.scrollToSkillSection) window.scrollToSkillSection(meta.sectionId);
            }, 30);
            showToast("已定位到「" + meta.sectionLabel + "」", "ok");
          });
          foot.appendChild(gotoSkills);
        }
        const closeBtn = document.createElement("button");
        closeBtn.type = "button";
        closeBtn.className = "btn";
        closeBtn.textContent = "关闭";
        closeBtn.addEventListener("click", () => closeAgentDrawer());
        foot.appendChild(closeBtn);
      },
    });
  }

  function openToolTag(agent, toolName) {
    const meta = getToolMeta(agent, toolName);
    if (!meta.available) {
      const body =
        '<div class="drawer-section"><h4>状态</h4><div><span class="badge pending">当前不可用</span></div></div>' +
        '<div class="drawer-section"><h4>原因</h4><div>' +
        escapeHtml(meta.reason) +
        "</div></div>" +
        '<div class="drawer-section"><h4>说明</h4><div>' +
        escapeHtml(meta.description) +
        "</div></div>";
      openAgentDrawer({
        title: toolName,
        subtitle: "工具 · 不可用",
        bodyHtml: body,
      });
      showToast(toolName + " 当前不可用：" + meta.reason, "warn");
      return;
    }
    openAgentDrawerForTool(agent, toolName, meta);
  }

  function openSkillTag(agent, skillName) {
    const meta = getSkillMeta(agent, skillName);
    if (!meta.available) {
      const body =
        '<div class="drawer-section"><h4>状态</h4><div><span class="badge pending">当前不可用</span></div></div>' +
        '<div class="drawer-section"><h4>原因</h4><div>' +
        escapeHtml(meta.reason) +
        "</div></div>" +
        '<div class="drawer-section"><h4>说明</h4><div>' +
        escapeHtml(meta.description) +
        "</div></div>";
      openAgentDrawer({
        title: skillName,
        subtitle: "技能 · 不可用",
        bodyHtml: body,
      });
      showToast(skillName + " 当前不可用：" + meta.reason, "warn");
      return;
    }
    openAgentDrawerForSkill(agent, skillName, meta);
  }

  function clearHashIfAny() {
    if (location.hash && history.replaceState) {
      history.replaceState(null, "", location.pathname + location.search);
    }
  }

  async function renderToolDetailPage() {
    await ensureToolSkillCatalog();
    const pending = window._pendingToolDetail;
    const toolName = pending && pending.toolName;
    if (!toolName) return;
    const agent = pending.agent || linkAgentForDetail();
    const meta = getToolMeta(agent, toolName);
    const h1 = document.getElementById("tool-detail-h1");
    const crumb = document.getElementById("tool-detail-crumb-name");
    if (h1) h1.textContent = toolName;
    if (crumb) crumb.textContent = toolName;
    const badgeWrap = document.getElementById("tool-detail-badge-wrap");
    if (badgeWrap) {
      badgeWrap.innerHTML = meta.available
        ? '<span class="badge completed">可用</span>'
        : '<span class="badge pending">当前不可用 · ' + escapeHtml(meta.reason) + "</span>";
    }
    const metaEl = document.getElementById("tool-detail-meta");
    if (metaEl) {
      metaEl.innerHTML =
        '<div class="detail-meta-row"><span class="detail-meta-label">关联智能体</span><span>' +
        escapeHtml(agent.label || "—") +
        "</span></div>" +
        '<div class="detail-meta-row"><span class="detail-meta-label">能力分区</span><span>' +
        escapeHtml(meta.sectionLabel) +
        "</span></div>" +
        '<div class="detail-meta-row"><span class="detail-meta-label">工具标识</span><span style="font-family:monospace">' +
        escapeHtml(toolName) +
        "</span></div>";
    }
    const bodyEl = document.getElementById("tool-detail-body");
    if (bodyEl) bodyEl.textContent = meta.description || "—";
    const btnSkills = document.getElementById("tool-detail-goto-skills");
    const btnChat = document.getElementById("tool-detail-open-chat");
    if (btnSkills) {
      btnSkills.onclick = () => {
        goToPage("skills");
        setTimeout(() => {
          if (window.scrollToNavGroup) window.scrollToNavGroup("capability");
          if (window.scrollToSkillSection) window.scrollToSkillSection(meta.sectionId);
        }, 30);
      };
    }
    if (btnChat) {
      btnChat.onclick = () => {
        openPromptInChat("请调用工具 " + toolName + "，说明当前环境与参数预期，并给出可执行步骤。");
      };
    }
  }

  async function renderSkillDetailPage() {
    await ensureToolSkillCatalog();
    const pending = window._pendingSkillDetail;
    const skillName = pending && pending.skillName;
    if (!skillName) return;
    const agent = pending.agent || linkAgentForDetail();
    const meta = getSkillMeta(agent, skillName);
    const h1 = document.getElementById("skill-detail-h1");
    const crumb = document.getElementById("skill-detail-crumb-name");
    if (h1) h1.textContent = skillName;
    if (crumb) crumb.textContent = skillName;
    const badgeWrap = document.getElementById("skill-detail-badge-wrap");
    if (badgeWrap) {
      badgeWrap.innerHTML = meta.available
        ? '<span class="badge completed">可用</span>'
        : '<span class="badge pending">当前不可用 · ' + escapeHtml(meta.reason) + "</span>";
    }
    const metaEl = document.getElementById("skill-detail-meta");
    if (metaEl) {
      metaEl.innerHTML =
        '<div class="detail-meta-row"><span class="detail-meta-label">关联智能体</span><span>' +
        escapeHtml(agent.label || "—") +
        "</span></div>" +
        '<div class="detail-meta-row"><span class="detail-meta-label">能力分区</span><span>' +
        escapeHtml(meta.sectionLabel) +
        "</span></div>" +
        '<div class="detail-meta-row"><span class="detail-meta-label">技能名称</span><span>' +
        escapeHtml(skillName) +
        "</span></div>";
    }
    const bodyEl = document.getElementById("skill-detail-body");
    if (bodyEl) bodyEl.textContent = meta.description || "—";
    const btnSkills = document.getElementById("skill-detail-goto-skills");
    const btnChat = document.getElementById("skill-detail-open-chat");
    if (btnSkills) {
      btnSkills.onclick = () => {
        goToPage("skills");
        setTimeout(() => {
          if (window.scrollToNavGroup) window.scrollToNavGroup("capability");
          if (window.scrollToSkillSection) window.scrollToSkillSection(meta.sectionId);
        }, 30);
      };
    }
    if (btnChat) {
      btnChat.onclick = () => {
        openPromptInChat(
          "请说明技能「" + skillName + "」的触发条件、配置项与与当前智能体的关系，并给出可执行的配置或验证步骤。"
        );
      };
    }
  }

  function bindAgentDetailShellOnce() {
    const overlay = document.getElementById("agent-drawer-overlay");
    const backdrop = document.getElementById("agent-drawer-backdrop");
    const closeBtn = document.getElementById("agent-drawer-close");
    if (backdrop && !backdrop.dataset.bound) {
      backdrop.dataset.bound = "1";
      backdrop.addEventListener("click", () => closeAgentDrawer());
    }
    if (closeBtn && !closeBtn.dataset.bound) {
      closeBtn.dataset.bound = "1";
      closeBtn.addEventListener("click", () => closeAgentDrawer());
    }
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && overlay && overlay.classList.contains("open")) closeAgentDrawer();
    });
    const tb = document.getElementById("tool-detail-back");
    const ta = document.getElementById("tool-detail-crumb-agents");
    if (tb && !tb.dataset.bound) {
      tb.dataset.bound = "1";
      tb.addEventListener("click", () => {
        clearHashIfAny();
        goToPage("agents");
      });
    }
    if (ta && !ta.dataset.bound) {
      ta.dataset.bound = "1";
      ta.addEventListener("click", (event) => {
        event.preventDefault();
        clearHashIfAny();
        goToPage("agents");
      });
    }
    const sb = document.getElementById("skill-detail-back");
    const sa = document.getElementById("skill-detail-crumb-agents");
    if (sb && !sb.dataset.bound) {
      sb.dataset.bound = "1";
      sb.addEventListener("click", () => {
        clearHashIfAny();
        goToPage("agents");
      });
    }
    if (sa && !sa.dataset.bound) {
      sa.dataset.bound = "1";
      sa.addEventListener("click", (event) => {
        event.preventDefault();
        clearHashIfAny();
        goToPage("agents");
      });
    }
  }

  async function applyAgentHashRoute() {
    const h = location.hash || "";
    if (!h || h === "#") return;
    const m = h.match(/^#(tool|skill)\/(.+)$/);
    if (!m) return;
    const kind = m[1];
    const name = decodeURIComponent(m[2]);
    await ensureToolSkillCatalog();
    if (kind === "tool") {
      window._pendingToolDetail = { agent: null, toolName: name, fromHash: true };
      goToPage("tool-detail");
    } else {
      window._pendingSkillDetail = { agent: null, skillName: name, fromHash: true };
      goToPage("skill-detail");
    }
  }

  function runAgent(agent) {
    if (agent.status !== "active") {
      showToast((agent.label || "该智能体") + " 当前处于待命状态，暂不可立即执行", "warn");
      return;
    }
    openPromptInChat(getPrimaryRunPrompt(agent));
  }

  function viewAgentHistory(agent) {
    openPromptInChat(getHistoryPrompt(agent));
  }

  function openAgentDetail(agent) {
    if (!agent) return;
    selectAgentCard(agent.id);
    showAgentDetail(agent);
  }

  function setTaskTabFilter(filter) {
    taskFilter = filter;
    document.querySelectorAll("#task-tabs .tab-btn").forEach((item) => {
      item.classList.toggle("active", item.dataset.f === filter);
    });
  }

  function focusTaskInTasks(taskId, flash = true) {
    if (!taskId) return;
    sessionStorage.setItem(TASK_FOCUS_KEY, taskId);
    sessionStorage.setItem(TASK_FLASH_KEY, flash ? "1" : "0");
    setTaskTabFilter("all");
    goToPage("tasks");
  }

  const taskTabsEl = document.getElementById("task-tabs");
  if (taskTabsEl) {
    taskTabsEl.addEventListener("click", (event) => {
      const button = event.target.closest(".tab-btn");
      if (!button) return;
      document.querySelectorAll("#task-tabs .tab-btn").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      taskFilter = button.dataset.f;
      loadTasks();
    });
  }

  async function loadTasks() {
    try {
      const response = await fetch(
        BASE + "/api/v1/tasks" + (taskFilter !== "all" ? "?filter=" + taskFilter : "")
      );
      const data = await response.json();
      const table = document.getElementById("task-tb");
      table.innerHTML = "";
      const statusMap = { pending: "待办", running: "进行中", completed: "已完成", failed: "失败" };
      const focusedTaskId = sessionStorage.getItem(TASK_FOCUS_KEY);
      const shouldFlash = sessionStorage.getItem(TASK_FLASH_KEY) === "1";
      (data.tasks || []).forEach((task, idx) => {
        const sourceDiscoveryId =
          task.source_discovery_id || task.result?.discovery_id || task.result?.source_discovery_id || null;
        const approval = task.needs_approval
          ? '<button class="btn btn-ok" onclick="approveTask(\'' +
            task.task_id +
            "',\'approve\')\">通过</button> <button class=\"btn btn-no\" onclick=\"approveTask('" +
            task.task_id +
            "',\'reject\')\">拒绝</button>"
          : "—";
        const actions = '<button class="btn" onclick="showTaskDetail(' + idx + ')">详情</button>';
        const sourceCell = sourceDiscoveryId
          ? '<button class="btn" style="font-size:.76rem" onclick="showTaskSourceDiscovery(\'' +
            sourceDiscoveryId +
            "')\">发现 " +
            sourceDiscoveryId.slice(0, 8) +
            "…</button>"
          : '<span style="color:var(--muted)">—</span>';
        const isFocused = focusedTaskId && focusedTaskId === task.task_id;
        table.innerHTML +=
          '<tr data-task-id="' +
          task.task_id +
          '"' +
          (isFocused
            ? ' style="background:rgba(87,148,242,.10);box-shadow:inset 0 0 0 1px rgba(87,148,242,.45)"'
            : "") +
          "><td>" +
          (task.task_type || "—") +
          "</td><td>" +
          (task.title || task.task_id) +
          "</td><td>" +
          sourceCell +
          '</td><td><span class="badge ' +
          (task.status || "pending") +
          '">' +
          (statusMap[task.status] || task.status) +
          "</span></td><td>" +
          approval +
          "</td><td>" +
          actions +
          "</td></tr>";
      });
      window._taskCache = data.tasks || [];
      if (!data.tasks?.length) {
        table.innerHTML =
          '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:20px">暂无任务</td></tr>';
      }
      if (focusedTaskId) {
        const focusedRow = table.querySelector('tr[data-task-id="' + focusedTaskId + '"]');
        if (focusedRow) {
          focusedRow.scrollIntoView({ behavior: "smooth", block: "center" });
          if (shouldFlash) {
            setTimeout(() => {
              focusedRow.style.transition = "box-shadow .4s ease, background .4s ease";
              focusedRow.style.boxShadow = "inset 0 0 0 2px rgba(87,148,242,.9)";
            }, 50);
          }
        }
        sessionStorage.removeItem(TASK_FOCUS_KEY);
        sessionStorage.removeItem(TASK_FLASH_KEY);
      }
    } catch (error) {
      document.getElementById("task-tb").innerHTML =
        '<tr><td colspan="6" style="color:var(--danger)">加载失败</td></tr>';
    }
  }

  function showTaskDetail(idx) {
    const task = (window._taskCache || [])[idx];
    if (!task) return;
    const statusMap = { pending: "待办", running: "进行中", completed: "已完成", failed: "失败" };
    const sourceDiscoveryId =
      task.source_discovery_id || task.result?.discovery_id || task.result?.source_discovery_id || null;
    let html =
      '<div class="modal-row"><div class="modal-label">任务 ID</div><div class="modal-val" style="font-family:monospace">' +
      (task.task_id || "") +
      "</div></div>";
    html += '<div class="modal-row"><div class="modal-label">标题</div><div class="modal-val">' + (task.title || "—") + "</div></div>";
    html += '<div class="modal-row"><div class="modal-label">类型</div><div class="modal-val">' + (task.task_type || "—") + "</div></div>";
    html +=
      '<div class="modal-row"><div class="modal-label">状态</div><div class="modal-val"><span class="badge ' +
      (task.status || "pending") +
      '">' +
      (statusMap[task.status] || task.status) +
      "</span></div></div>";
    html +=
      '<div class="modal-row"><div class="modal-label">需审批</div><div class="modal-val">' +
      (task.needs_approval ? '<span class="badge approval">是</span>' : "否") +
      "</div></div>";
    html +=
      '<div class="modal-row"><div class="modal-label">会话 ID</div><div class="modal-val" style="font-family:monospace">' +
      (task.session_id || "—") +
      "</div></div>";
    html +=
      '<div class="modal-row"><div class="modal-label">创建时间</div><div class="modal-val">' +
      (task.created_at || "—") +
      "</div></div>";
    if (sourceDiscoveryId) {
      html +=
        '<div class="modal-row"><div class="modal-label">来源发现</div><div class="modal-val" style="font-family:monospace">' +
        sourceDiscoveryId +
        "</div></div>";
    }
    if (task.error) {
      html +=
        '<div class="modal-row"><div class="modal-label">错误</div><div class="modal-val" style="color:var(--danger)">' +
        task.error +
        "</div></div>";
    }
    if (task.result) {
      html +=
        '<div class="modal-row"><div class="modal-label">结果</div><div class="modal-val"><div class="modal-json">' +
        JSON.stringify(task.result, null, 2) +
        "</div></div></div>";
    }
    if (sourceDiscoveryId) {
      html +=
        '<div style="display:flex;gap:8px;margin-top:12px"><button class="btn btn-primary" onclick="showTaskSourceDiscovery(\'' +
        sourceDiscoveryId +
        "')\">前往发现</button></div>";
    }
    showModal(task.title || "任务详情", html);
  }

  function showTaskSourceDiscovery(discoveryId) {
    const overlays = document.querySelectorAll(".modal-overlay");
    const overlay = overlays[overlays.length - 1];
    if (overlay) overlay.remove();
    if (window.focusDiscoveryById) {
      window.focusDiscoveryById(discoveryId, true);
      return;
    }
    goToPage("discovery");
  }

  async function approveTask(id, action) {
    try {
      await fetch(BASE + "/api/v1/tasks/" + id + "/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      showToast(action === "approve" ? "已审批通过" : "已拒绝", action === "approve" ? "ok" : "danger");
      await loadTasks();
      await refreshDash();
    } catch (error) {
      showToast("操作失败: " + error.message, "danger");
    }
  }

  async function loadAgents() {
    try {
      const bust = "_bust=" + Date.now();
      const [agentsResponse, toolsResponse, skillsResponse] = await Promise.all([
        fetch(BASE + "/api/v1/agents?" + bust, { cache: "no-store" }),
        fetch(BASE + "/api/v1/tools?" + bust, { cache: "no-store" }),
        fetch(BASE + "/api/v1/skills?" + bust, { cache: "no-store" }),
      ]);
      const [agentsPayload, toolsPayload, skillsPayload] = await Promise.all([
        agentsResponse.json(),
        toolsResponse.json(),
        skillsResponse.json(),
      ]);
      agentsData = (agentsPayload.agents || []).map(normalizeProcessEngineerAgent);
      toolCatalog = Object.fromEntries((toolsPayload.tools || []).map((tool) => [tool.name, tool]));
      skillCatalog = skillsPayload.skills || [];
      const el = document.getElementById("agent-list");
      el.innerHTML = "";
      agentsData.forEach((agent, index) => {
        const runDisabled = agent.status !== "active" ? " disabled" : "";
        const { toolCount, skillCount } = aggregatedToolSkillCounts(agent);
        const subCount = getSubAgents(agent).length;
        const subHint = subCount ? " · 子智能体 " + subCount : "";
        const hasSubs = subCount > 0;
        el.innerHTML +=
          '<div class="agent-card is-collapsed" data-agent-id="' +
          escapeHtml(agent.id || "") +
          '" data-idx="' +
          index +
          '">' +
          '<div class="agent-card-compact" data-idx="' +
          index +
          '" title="点击展开查看工具、技能与操作">' +
          '<div class="agent-head"><div class="agent-emoji">' +
          escapeHtml(agent.emoji || "AI") +
          '</div><div class="agent-info"><div class="name">' +
          escapeHtml(agent.label) +
          ' <span class="agent-status ' +
          escapeHtml(agent.status || "active") +
          '">' +
          getAgentStatusLabel(agent.status) +
          '</span></div><div class="role">' +
          escapeHtml(agent.role) +
          '</div><div class="desc">' +
          escapeHtml(agent.desc) +
          '</div><div class="agent-hint-row"><span class="agent-mini-meta">工具 ' +
          toolCount +
          " · 技能 " +
          skillCount +
          subHint +
          '</span><button type="button" class="btn agent-card-expand-btn" data-idx="' +
          index +
          '" title="展开完整信息">展开</button></div></div></div></div>' +
          '<div class="agent-card-collapse-wrap"><button type="button" class="btn agent-card-collapse-btn" data-idx="' +
          index +
          '" title="收起">收起</button></div>' +
          '<div class="agent-card-expanded">' +
          '<div class="platforms" style="font-size:.76rem;color:var(--muted);margin-bottom:12px">关联平台：' +
          escapeHtml(agent.platforms) +
          "</div>" +
          (hasSubs
            ? '<div class="agent-subagents"><div class="stat-label" style="margin-bottom:8px">子智能体（分工）</div>' +
              renderSubAgentsExpandedHtml(agent, index) +
              "</div>" +
              renderParentUmbrellaHtml(agent, index)
            : '<div class="agent-meta-block"><div class="stat-label" style="margin-bottom:6px">可用工具</div><div class="agent-chip-row">' +
              renderTagGroup("tool", agent, index, agent.tools || []) +
              '</div></div><div class="agent-meta-block"><div class="stat-label" style="margin-bottom:6px">触发技能</div><div class="agent-chip-row">' +
              renderTagGroup("skill", agent, index, agent.skills || []) +
              "</div></div>") +
          '<div class="agent-actions">' +
          '<button type="button" class="btn btn-primary agent-run-btn" data-idx="' +
          index +
          '" title="立即执行当前智能体主流程"' +
          runDisabled +
          ">立即执行</button>" +
          '<button type="button" class="btn agent-history-btn" data-idx="' +
          index +
          '" title="查看最近历史记录与报告">查看历史</button>' +
          '<button type="button" class="btn agent-detail-btn" data-idx="' +
          index +
          '" title="进入智能体详情">进入详情</button>' +
          "</div></div></div>";
      });
      bindInteractiveTags(el);
      bindQuickActions(el);
      bindAgentCardCollapse(el);
      el.querySelectorAll(".agent-run-btn").forEach((button) => {
        button.addEventListener("click", (event) => {
          event.stopPropagation();
          runAgent(agentsData[parseInt(button.dataset.idx, 10)]);
        });
      });
      el.querySelectorAll(".agent-history-btn").forEach((button) => {
        button.addEventListener("click", (event) => {
          event.stopPropagation();
          viewAgentHistory(agentsData[parseInt(button.dataset.idx, 10)]);
        });
      });
      el.querySelectorAll(".agent-detail-btn").forEach((button) => {
        button.addEventListener("click", (event) => {
          event.stopPropagation();
          openAgentDetail(agentsData[parseInt(button.dataset.idx, 10)]);
        });
      });
      if (agentsData.length) openAgentDetail(agentsData[0]);
    } catch (error) {
      document.getElementById("agent-list").innerHTML = '<div style="color:var(--danger)">加载失败</div>';
    }
  }

  function showAgentDetail(agent) {
    const panel = document.getElementById("agent-detail");
    const agentIndex = agentsData.findIndex((item) => item.id === agent.id);
    if (agentIndex >= 0) {
      document.querySelectorAll(".agent-card").forEach((c) => {
        if (parseInt(c.dataset.idx, 10) === agentIndex) c.classList.remove("is-collapsed");
      });
    }
    panel.style.display = "block";
    document.getElementById("ad-emoji").textContent = agent.emoji;
    document.getElementById("ad-name").textContent = agent.label;
    document.getElementById("ad-role").textContent = agent.role;
    document.getElementById("ad-status").textContent = getAgentStatusLabel(agent.status);
    document.getElementById("ad-status").className = "agent-status " + (agent.status || "active");
    document.getElementById("ad-desc").textContent = agent.desc;
    document.getElementById("ad-platforms").textContent = agent.platforms;
    const subSection = document.getElementById("ad-subagents-section");
    const toolsWrap = document.getElementById("ad-tools-wrapper");
    const skillsWrap = document.getElementById("ad-skills-wrapper");
    const capGrid = document.getElementById("ad-capabilities-grid");
    const hasSubs = getSubAgents(agent).length > 0;
    const toolsLabelEl = toolsWrap && toolsWrap.querySelector(".stat-label");
    const skillsLabelEl = skillsWrap && skillsWrap.querySelector(".stat-label");
    if (hasSubs) {
      if (subSection) {
        subSection.style.display = "block";
        subSection.innerHTML =
          '<div class="stat-label" style="margin-bottom:8px">子智能体（分工）</div><div class="agent-subagents">' +
          renderSubAgentsExpandedHtml(agent, agentIndex) +
          "</div>";
      }
      if (toolsWrap) toolsWrap.style.display = "";
      if (skillsWrap) skillsWrap.style.display = "";
      if (toolsLabelEl) toolsLabelEl.textContent = "统筹 · 可用工具";
      if (skillsLabelEl) skillsLabelEl.textContent = "统筹 · 触发技能";
      if (capGrid) capGrid.className = "grid grid-3";
      document.getElementById("ad-tools").innerHTML =
        renderTagGroup("tool", agent, agentIndex, agent.tools || []);
      document.getElementById("ad-skills").innerHTML =
        renderTagGroup("skill", agent, agentIndex, agent.skills || []);
    } else {
      if (subSection) {
        subSection.style.display = "none";
        subSection.innerHTML = "";
      }
      if (toolsWrap) toolsWrap.style.display = "";
      if (skillsWrap) skillsWrap.style.display = "";
      if (toolsLabelEl) toolsLabelEl.textContent = "可用工具";
      if (skillsLabelEl) skillsLabelEl.textContent = "触发技能";
      if (capGrid) capGrid.className = "grid grid-3";
      document.getElementById("ad-tools").innerHTML =
        renderTagGroup("tool", agent, agentIndex, agent.tools || []);
      document.getElementById("ad-skills").innerHTML =
        renderTagGroup("skill", agent, agentIndex, agent.skills || []);
    }
    const actions = document.getElementById("ad-actions");
    actions.innerHTML =
      '<div class="agent-detail-actions">' +
      '<button type="button" class="btn btn-primary agent-run-btn" data-idx="' +
      agentIndex +
      '" title="立即执行当前智能体主流程"' +
      (agent.status !== "active" ? " disabled" : "") +
      ">立即执行</button>" +
      '<button type="button" class="btn agent-history-btn" data-idx="' +
      agentIndex +
      '" title="查看最近历史记录与报告">查看历史</button>' +
      '<button type="button" class="btn agent-detail-btn active" data-idx="' +
      agentIndex +
      '" title="当前已位于详情面板">进入详情</button>' +
      '</div><div class="stat-label" style="margin:12px 0 6px">快捷操作</div><div class="agent-quick-actions">' +
      renderQuickActions(agent) +
      "</div>";
    bindInteractiveTags(panel);
    bindQuickActions(panel);
    actions.querySelectorAll(".agent-run-btn").forEach((button) => {
      button.addEventListener("click", () => runAgent(agentsData[parseInt(button.dataset.idx, 10)]));
    });
    actions.querySelectorAll(".agent-history-btn").forEach((button) => {
      button.addEventListener("click", () => viewAgentHistory(agentsData[parseInt(button.dataset.idx, 10)]));
    });
    actions.querySelectorAll(".agent-detail-btn").forEach((button) => {
      button.addEventListener("click", () => panel.scrollIntoView({ behavior: "smooth", block: "nearest" }));
    });
    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  async function loadSessions() {
    try {
      const response = await fetch(BASE + "/api/v1/sessions");
      const data = await response.json();
      const table = document.getElementById("sess-tb");
      table.innerHTML = "";
      (data.sessions || []).forEach((session) => {
        table.innerHTML +=
          '<tr><td style="font-family:monospace;font-size:.82rem">' +
          session.session_id +
          "</td><td>" +
          (session.project_id || "—") +
          "</td><td>" +
          session.messages +
          "</td><td>" +
          (session.created_at || "—") +
          '</td><td><button class="btn btn-no" onclick="deleteSession(\'' +
          session.session_id +
          '\');loadSessions()">删除</button></td></tr>';
      });
      if (!data.sessions?.length) {
        table.innerHTML =
          '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:20px">暂无会话</td></tr>';
      }
    } catch (error) {
      console.error(error);
    }
  }

  async function loadLogs() {
    try {
      const level = document.getElementById("log-level").value;
      const response = await fetch(BASE + "/api/v1/logs?limit=200" + (level ? "&level=" + level : ""));
      const data = await response.json();
      const search = (document.getElementById("log-search").value || "").toLowerCase();
      let logs = data.logs || [];
      if (search) {
        logs = logs.filter(
          (log) =>
            (log.message || "").toLowerCase().includes(search) ||
            (log.subsystem || "").toLowerCase().includes(search)
        );
      }
      document.getElementById("log-count").textContent = logs.length + " 条";
      const table = document.getElementById("log-tb");
      table.innerHTML = "";
      logs.reverse().forEach((log) => {
        table.innerHTML +=
          '<tr><td class="log-time">' +
          log.time +
          '</td><td class="log-level ' +
          (log.level || "") +
          '">' +
          log.level +
          '</td><td class="log-sub">' +
          log.subsystem +
          '</td><td class="log-msg">' +
          log.message +
          "</td></tr>";
      });
    } catch (error) {
      console.error(error);
    }
  }

  async function loadDebug() {
    try {
      const [statusR, healthR] = await Promise.all([
        fetch(BASE + "/api/v1/debug/status"),
        fetch(BASE + "/api/v1/debug/health"),
      ]);
      document.getElementById("dbg-status").textContent = JSON.stringify(await statusR.json(), null, 2);
      document.getElementById("dbg-health").textContent = JSON.stringify(await healthR.json(), null, 2);
    } catch (error) {
      document.getElementById("dbg-status").textContent = "加载失败: " + error.message;
    }
  }

  async function recoverStateStore(statusElId) {
    const el = document.getElementById(statusElId);
    if (el) {
      el.textContent = "恢复中...";
      el.style.color = "var(--muted)";
    }
    try {
      const response = await fetch(BASE + "/api/v1/state-store/recover", { method: "POST" });
      const data = await response.json();
      if (data.state_store?.available) {
        if (el) {
          el.textContent = "已恢复到正常模式";
          el.style.color = "var(--ok)";
        }
        if (window.resetDegradedToast) window.resetDegradedToast();
      } else if (el) {
        el.textContent = "恢复失败：" + (data.state_store?.last_error || "未知错误");
        el.style.color = "var(--danger)";
      }
      await refreshDash();
      if (document.getElementById("dbg-status")) await loadDebug();
    } catch (error) {
      if (el) {
        el.textContent = "恢复失败：" + error.message;
        el.style.color = "var(--danger)";
      }
    }
  }

  async function debugRpc() {
    const method = document.getElementById("dbg-method").value;
    const path = document.getElementById("dbg-path").value;
    const body = document.getElementById("dbg-body").value;
    try {
      const opts = { method };
      if (method === "POST" && body) {
        opts.headers = { "Content-Type": "application/json" };
        opts.body = body;
      }
      const response = await fetch(BASE + path, opts);
      const text = await response.text();
      try {
        document.getElementById("dbg-result").textContent = JSON.stringify(JSON.parse(text), null, 2);
      } catch (error) {
        document.getElementById("dbg-result").textContent = text;
      }
    } catch (error) {
      document.getElementById("dbg-result").textContent = "错误: " + error.message;
    }
  }

  const logLevelEl = document.getElementById("log-level");
  const logSearchEl = document.getElementById("log-search");
  if (logLevelEl) logLevelEl.addEventListener("change", loadLogs);
  if (logSearchEl) logSearchEl.addEventListener("input", loadLogs);

  window.loadTasks = loadTasks;
  window.showTaskDetail = showTaskDetail;
  window.showTaskSourceDiscovery = showTaskSourceDiscovery;
  window.approveTask = approveTask;
  window.loadAgents = loadAgents;
  window.showAgentDetail = showAgentDetail;
  window.renderToolDetailPage = renderToolDetailPage;
  window.renderSkillDetailPage = renderSkillDetailPage;
  window.applyAgentHashRoute = applyAgentHashRoute;
  window.closeAgentDrawer = closeAgentDrawer;
  window.loadSessions = loadSessions;
  window.loadLogs = loadLogs;
  window.loadDebug = loadDebug;
  window.recoverStateStore = recoverStateStore;
  window.debugRpc = debugRpc;
  window.focusTaskInTasks = focusTaskInTasks;

  bindAgentDetailShellOnce();
  setTimeout(() => {
    applyAgentHashRoute();
  }, 0);
})();
