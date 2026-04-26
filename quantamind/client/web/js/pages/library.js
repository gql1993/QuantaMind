(function () {
  const libDrop = document.getElementById("lib-dropzone");
  const libFileInput = document.getElementById("lib-file-input");
  const libFolderInput = document.getElementById("lib-folder-input");

  document.getElementById("lib-pick-files").addEventListener("click", (event) => {
    event.stopPropagation();
    libFileInput.click();
  });
  document.getElementById("lib-pick-folder").addEventListener("click", (event) => {
    event.stopPropagation();
    libFolderInput.click();
  });

  libDrop.addEventListener("dragover", (event) => {
    event.preventDefault();
    libDrop.style.borderColor = "var(--accent)";
  });
  libDrop.addEventListener("dragleave", () => {
    libDrop.style.borderColor = "var(--border)";
  });
  libDrop.addEventListener("drop", async (event) => {
    event.preventDefault();
    libDrop.style.borderColor = "var(--border)";
    try {
      const items = event.dataTransfer.items;
      const allFiles = [];
      if (items && items.length && items[0].webkitGetAsEntry) {
        const promises = [];
        for (let i = 0; i < items.length; i += 1) {
          const entry = items[i].webkitGetAsEntry();
          if (entry) {
            promises.push(traverseEntry(entry, allFiles));
          } else {
            const file = items[i].getAsFile();
            if (file) allFiles.push(file);
          }
        }
        await Promise.all(promises);
      } else {
        const files = event.dataTransfer.files;
        for (let i = 0; i < files.length; i += 1) allFiles.push(files[i]);
      }
      if (allFiles.length) {
        uploadFiles(allFiles);
      } else {
        showToast("未检测到文件，请重试", "warn");
      }
    } catch (error) {
      showToast("拖拽处理失败: " + error.message, "danger");
      console.error(error);
    }
  });

  async function traverseEntry(entry, fileList, pathPrefix = "") {
    if (entry.isFile) {
      return new Promise((resolve) => {
        entry.file((file) => {
          file._relativePath = pathPrefix + file.name;
          fileList.push(file);
          resolve();
        });
      });
    }
    if (entry.isDirectory) {
      const reader = entry.createReader();
      return new Promise((resolve) => {
        reader.readEntries(async (entries) => {
          for (const item of entries) {
            await traverseEntry(item, fileList, pathPrefix + entry.name + "/");
          }
          resolve();
        });
      });
    }
    return Promise.resolve();
  }

  libFileInput.addEventListener("change", () => {
    uploadFiles(libFileInput.files);
    libFileInput.value = "";
  });
  libFolderInput.addEventListener("change", () => {
    uploadFiles(libFolderInput.files);
    libFolderInput.value = "";
  });

  function escJsAttr(value) {
    return String(value ?? "").replace(/\\/g, "\\\\").replace(/'/g, "\\'");
  }

  async function uploadFiles(fileList) {
    const files = Array.from(fileList).filter((file) => file.size > 0);
    if (!files.length) {
      showToast("没有有效文件", "warn");
      return;
    }
    const status = document.getElementById("lib-upload-status");
    let success = 0;
    let fail = 0;
    let lastErr = "";
    for (let i = 0; i < files.length; i += 1) {
      const file = files[i];
      const relPath = file._relativePath || file.webkitRelativePath || file.name;
      status.innerHTML =
        '<span style="color:var(--accent)">上传中（' +
        (i + 1) +
        "/" +
        files.length +
        "）：" +
        relPath +
        " (" +
        Math.round(file.size / 1024) +
        "KB)</span>";
      const fd = new FormData();
      fd.append("file", file, relPath.replace(/[\/\\]/g, "_"));
      fd.append("project_id", "default");
      const folderId = document.getElementById("lib-upload-folder").value;
      if (folderId) fd.append("folder_id", folderId);
      try {
        const response = await fetch(BASE + "/api/v1/library/upload", { method: "POST", body: fd });
        if (response.ok) {
          await response.json();
          success += 1;
        } else {
          fail += 1;
          lastErr = await response.text();
        }
      } catch (error) {
        fail += 1;
        lastErr = error.message;
      }
    }
    if (success > 0) {
      status.innerHTML =
        '<span style="color:var(--ok)">完成：' +
        success +
        " 个成功" +
        (fail ? ' · <span style="color:var(--danger)">' + fail + " 个失败</span>" : "") +
        "</span>";
      showToast(success + " 个文件上传成功", "ok");
    } else {
      status.innerHTML = '<span style="color:var(--danger)">上传失败：' + lastErr + "</span>";
      showToast("上传失败: " + lastErr, "danger");
    }
    setTimeout(() => {
      status.innerHTML = "";
    }, 8000);
    await loadLibrary();
  }

  async function loadLibrary() {
    const search = document.getElementById("lib-search")?.value || "";
    try {
      const [filesR, statsR, jobsR] = await Promise.all([
        fetch(BASE + "/api/v1/library/files" + (search ? "?search=" + encodeURIComponent(search) : "")),
        fetch(BASE + "/api/v1/library/stats"),
        fetch(BASE + "/api/v1/state/library-ingest-jobs?limit=20"),
      ]);
      const fd = await filesR.json();
      const st = await statsR.json();
      const jobs = await jobsR.json();
      const byType = st.by_type || {};
      const typeHtml = Object.entries(byType)
        .map(([key, value]) => key + " " + value)
        .join(" · ");
      document.getElementById("lib-stats").innerHTML =
        '<div class="card stat-card"><div class="stat-label">总文件</div><div class="stat-value">' +
        st.total_files +
        '</div></div>' +
        '<div class="card stat-card"><div class="stat-label">总大小</div><div class="stat-value">' +
        (st.total_size_bytes > 1048576
          ? (st.total_size_bytes / 1048576).toFixed(1) + "MB"
          : (st.total_size_bytes / 1024).toFixed(0) + "KB") +
        '</div></div>' +
        '<div class="card stat-card"><div class="stat-label">已解析</div><div class="stat-value ok">' +
        st.parsed +
        '</div></div>' +
        '<div class="card stat-card"><div class="stat-label">类型分布</div><div style="font-size:.78rem;color:var(--muted);padding:8px">' +
        typeHtml +
        "</div></div>";

      const jobsTable = document.getElementById("lib-jobs-tb");
      jobsTable.innerHTML = "";
      (jobs.records || []).forEach((job) => {
        const badgeCls =
          job.status === "completed" ? "completed" : job.status === "failed" ? "failed" : "running";
        jobsTable.innerHTML +=
          '<tr><td style="font-family:monospace;font-size:.78rem">' +
          job.job_id +
          "</td><td>" +
          (job.filename || "—") +
          "</td><td><span class=\"badge " +
          badgeCls +
          '">' +
          (job.status || "—") +
          "</span></td><td>" +
          (job.stage || "—") +
          "</td><td>" +
          (job.attempts || 0) +
          '</td><td style="font-size:.78rem">' +
          (job.updated_at || "").replace("T", " ").slice(0, 19) +
          "</td></tr>";
      });
      if (!(jobs.records || []).length) {
        jobsTable.innerHTML =
          '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:16px">暂无解析 / 索引任务</td></tr>';
      }

      const foldersR = await fetch(BASE + "/api/v1/library/folders");
      const foldersD = await foldersR.json();
      const allFolders = foldersD.folders || [];
      const sel = document.getElementById("lib-upload-folder");
      const curVal = sel.value;
      sel.innerHTML = '<option value="">未分类</option>';
      allFolders.forEach((folder) => {
        sel.innerHTML += '<option value="' + folder.folder_id + '">' + folder.name + "</option>";
      });
      sel.value = curVal;

      const filesByFolder = { "": [] };
      allFolders.forEach((folder) => {
        filesByFolder[folder.folder_id] = [];
      });
      (fd.files || []).forEach((file) => {
        const folderId = file.folder_id || "";
        if (!filesByFolder[folderId]) filesByFolder[folderId] = [];
        filesByFolder[folderId].push(file);
      });

      const foldersEl = document.getElementById("lib-folders");
      foldersEl.innerHTML = "";
      if (!fd.files?.length && !allFolders.length) {
        foldersEl.innerHTML =
          '<div class="card" style="text-align:center;color:var(--muted);padding:30px">暂无文件。先创建文件夹，再上传文件。</div>';
        return;
      }
      const moveOptions =
        allFolders.map((folder) => '<option value="' + folder.folder_id + '">' + folder.name + "</option>").join("") +
        '<option value="">未分类</option>';

      function ingestStageLabel(stage) {
        const labels = {
          uploaded: "已上传",
          parsed: "已解析",
          indexed: "已索引",
          deleted: "已删除",
        };
        return labels[stage] || stage || "—";
      }

      function renderIngestStatusCell(file) {
        const job = file.latest_ingest_job;
        if (!job) {
          return file.parsed ? '<span class="badge completed">已解析</span>' : '<span class="badge pending">待处理</span>';
        }
        const badgeCls =
          job.status === "completed" ? "completed" : job.status === "failed" ? "failed" : "running";
        const label =
          job.status === "failed"
            ? "失败"
            : job.status === "completed"
              ? ingestStageLabel(job.stage)
              : "进行中";
        let html = '<div><span class="badge ' + badgeCls + '">' + label + "</span></div>";
        html += '<div style="font-size:.72rem;color:var(--muted);margin-top:4px">' + ingestStageLabel(job.stage) + "</div>";
        return html;
      }

      function renderRetryButton(file) {
        const job = file.latest_ingest_job;
        if (!job || job.status !== "failed") return "";
        const safeFileId = escJsAttr(file.file_id);
        return (
          ' <button class="btn" style="font-size:.76rem" onclick="retryLibFile(\'' +
          safeFileId +
          "')\">重试</button>"
        );
      }

      function renderFolder(folderId, name, desc, files, canDelete) {
        const safeFolderId = escJsAttr(folderId);
        const safeName = escJsAttr(name);
        const totalSize = files.reduce((acc, file) => acc + file.size_bytes, 0);
        const failedCount = files.filter((file) => (file.latest_ingest_job || {}).status === "failed").length;
        const sizeLabel =
          totalSize > 1048576 ? (totalSize / 1048576).toFixed(1) + " MB" : (totalSize / 1024).toFixed(0) + " KB";
        let html =
          '<div class="card lib-folder-card" data-folder-id="' +
          folderId +
          '" style="margin-bottom:12px;transition:border-color .2s">';
        html += '<div class="folder-header" style="display:flex;align-items:center;gap:8px;cursor:pointer">';
        html += '<span style="font-size:1.3rem">📁</span>';
        html += '<span style="font-weight:600;font-size:.95rem">' + name + "</span>";
        if (desc) html += '<span style="font-size:.78rem;color:var(--muted)">' + desc + "</span>";
        html += '<span class="badge completed" style="font-size:.72rem">' + files.length + " 个文件</span>";
        html += '<span style="font-size:.78rem;color:var(--muted)">' + sizeLabel + "</span>";
        if (canDelete) {
          if (failedCount) {
            html +=
              '<button class="btn" style="font-size:.72rem" onclick="event.stopPropagation();retryFolderFailed(\'' +
              safeFolderId +
              '\',\'' +
              safeName +
              "')\">重试失败项(" +
              failedCount +
              ")</button>";
          }
          html +=
            '<button class="btn" style="margin-left:auto;font-size:.72rem" onclick="event.stopPropagation();renameFolder(\'' +
            safeFolderId +
            '\',\'' +
            safeName +
            "')\">重命名</button>";
          html +=
            '<button class="btn btn-no" style="font-size:.72rem" onclick="event.stopPropagation();deleteFolder(\'' +
            safeFolderId +
            '\',\'' +
            safeName +
            "')\">删除文件夹</button>";
        } else {
          html += '<span style="margin-left:auto;color:var(--muted);font-size:.8rem">▾</span>';
        }
        html += "</div>";
        html +=
          '<div class="folder-drop-hint" style="display:none;padding:12px;margin-top:6px;border:2px dashed var(--accent);border-radius:var(--radius);text-align:center;color:var(--accent);font-size:.84rem">松开鼠标，上传到「' +
          name +
          "」</div>";
        html += '<div class="folder-body" style="margin-top:8px">';
        if (files.length) {
          html += '<table class="dtable"><thead><tr><th>文件名</th><th>类型</th><th>大小</th><th>任务状态</th><th>操作</th></tr></thead><tbody>';
          files.forEach((file) => {
            const safeFileId = escJsAttr(file.file_id);
            const safeFilename = escJsAttr(file.filename);
            const size =
              file.size_bytes > 1048576
                ? (file.size_bytes / 1048576).toFixed(1) + "MB"
                : (file.size_bytes / 1024).toFixed(0) + "KB";
            html +=
              '<tr draggable="true" data-file-id="' +
              file.file_id +
              '" data-file-name="' +
              file.filename +
              '" style="cursor:grab"><td style="font-weight:500">' +
              file.filename +
              '</td><td><span class="badge running" style="font-size:.7rem">' +
              file.file_type +
              "</span></td><td>" +
              size +
              "</td><td>" +
              renderIngestStatusCell(file) +
              "</td>";
            html +=
              '<td style="white-space:nowrap"><button class="btn" onclick="showFileDetail(\'' +
              safeFileId +
              "')\">详情</button> <button class=\"btn\" onclick=\"window.open(BASE+'/api/v1/library/files/" +
              safeFileId +
              '/download\')">下载</button> ';
            html += renderRetryButton(file);
            html +=
              '<select class="btn" style="font-size:.76rem;padding:4px;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:4px" onchange="moveFile(\'' +
              safeFileId +
              "',this.value);this.value=''\" title=\"移动到…\"><option value=\"\">移动到…</option>" +
              moveOptions.replace('value="' + folderId + '"', 'value="' + folderId + '" disabled') +
              "</select> ";
            html +=
              '<button class="btn btn-no" onclick="deleteLibFile(\'' +
              safeFileId +
              '\',\'' +
              safeFilename +
              "')\">删</button></td></tr>";
          });
          html += "</tbody></table>";
        } else {
          html += '<div style="color:var(--muted);font-size:.84rem;padding:10px">文件夹为空</div>';
        }
        html += '<div style="margin-top:8px;padding:8px;border-top:1px solid var(--border);display:flex;align-items:center;gap:8px">';
        html += '<input type="file" multiple class="folder-file-input" data-folder-id="' + folderId + '" style="display:none"/>';
        html += '<button class="btn" style="font-size:.78rem" onclick="this.previousElementSibling.click()">上传文件到此文件夹</button>';
        html += '<span style="font-size:.76rem;color:var(--muted)">或直接拖拽文件到此卡片</span>';
        html += "</div>";
        html += "</div></div>";
        return html;
      }

      allFolders.forEach((folder) => {
        foldersEl.innerHTML += renderFolder(
          folder.folder_id,
          folder.name,
          folder.description,
          filesByFolder[folder.folder_id] || [],
          true
        );
      });
      const uncategorized = filesByFolder[""] || [];
      if (uncategorized.length) {
        foldersEl.innerHTML += renderFolder("", "未分类", "未归入任何文件夹的文件", uncategorized, false);
      }

      document.querySelectorAll(".lib-folder-card").forEach((card) => {
        const folderId = card.dataset.folderId;
        const hint = card.querySelector(".folder-drop-hint");
        const header = card.querySelector(".folder-header");
        header.addEventListener("click", () => {
          const body = card.querySelector(".folder-body");
          body.style.display = body.style.display === "none" ? "block" : "none";
        });
        card.addEventListener("dragover", (event) => {
          event.preventDefault();
          card.style.borderColor = "var(--accent)";
          if (hint) hint.style.display = "block";
        });
        card.addEventListener("dragleave", (event) => {
          if (!card.contains(event.relatedTarget)) {
            card.style.borderColor = "var(--border)";
            if (hint) hint.style.display = "none";
          }
        });
        card.addEventListener("drop", async (event) => {
          event.preventDefault();
          card.style.borderColor = "var(--border)";
          if (hint) hint.style.display = "none";
          const dragFileId = event.dataTransfer.getData("text/file-id");
          if (dragFileId) {
            await moveFile(dragFileId, folderId);
            return;
          }
          const items = event.dataTransfer.items;
          const allFiles = [];
          if (items && items.length && items[0].webkitGetAsEntry) {
            const promises = [];
            for (let i = 0; i < items.length; i += 1) {
              const entry = items[i].webkitGetAsEntry();
              if (entry) {
                promises.push(traverseEntry(entry, allFiles));
              } else {
                const file = items[i].getAsFile();
                if (file) allFiles.push(file);
              }
            }
            await Promise.all(promises);
          } else {
            for (let i = 0; i < event.dataTransfer.files.length; i += 1) {
              allFiles.push(event.dataTransfer.files[i]);
            }
          }
          if (allFiles.length) {
            const uploadFolder = document.getElementById("lib-upload-folder");
            const origSel = uploadFolder.value;
            uploadFolder.value = folderId;
            await uploadFiles(allFiles);
            uploadFolder.value = origSel;
          }
        });
      });

      document.querySelectorAll(".folder-file-input").forEach((input) => {
        input.addEventListener("change", async () => {
          const folderId = input.dataset.folderId;
          const uploadFolder = document.getElementById("lib-upload-folder");
          const origSel = uploadFolder.value;
          uploadFolder.value = folderId;
          await uploadFiles(input.files);
          uploadFolder.value = origSel;
          input.value = "";
        });
      });

      document.querySelectorAll("tr[draggable=true]").forEach((row) => {
        row.addEventListener("dragstart", (event) => {
          event.dataTransfer.setData("text/file-id", row.dataset.fileId);
          event.dataTransfer.effectAllowed = "move";
          row.style.opacity = "0.4";
        });
        row.addEventListener("dragend", () => {
          row.style.opacity = "1";
        });
      });
    } catch (error) {
      console.error(error);
    }
  }

  async function createFolder() {
    const name = document.getElementById("lib-new-folder").value.trim();
    if (!name) {
      showToast("请输入文件夹名称", "warn");
      return;
    }
    const desc = document.getElementById("lib-new-folder-desc").value.trim();
    const fd = new FormData();
    fd.append("name", name);
    fd.append("description", desc);
    try {
      const response = await fetch(BASE + "/api/v1/library/folders", { method: "POST", body: fd });
      const data = await response.json();
      if (!response.ok || data.error) {
        showToast(data.error || "创建失败", "danger");
        return;
      }
      showToast("文件夹「" + name + "」已创建", "ok");
      document.getElementById("lib-new-folder").value = "";
      document.getElementById("lib-new-folder-desc").value = "";
      await loadLibrary();
    } catch (error) {
      showToast("创建失败: " + error.message, "danger");
    }
  }

  async function deleteFolder(fid, name) {
    if (!confirm("确定删除文件夹「" + name + "」及其中所有文件？")) return;
    try {
      const response = await fetch(BASE + "/api/v1/library/folders/" + fid, { method: "DELETE" });
      const data = await response.json();
      if (!response.ok || data.error) {
        showToast(data.error || "删除失败", "danger");
        return;
      }
      showToast("文件夹已删除", "ok");
      await loadLibrary();
    } catch (error) {
      showToast("删除失败: " + error.message, "danger");
    }
  }

  async function renameFolder(fid, currentName) {
    const name = prompt("请输入新的文件夹名称", currentName || "");
    if (name == null) return;
    const nextName = name.trim();
    if (!nextName || nextName === currentName) return;
    try {
      const fd = new FormData();
      fd.append("name", nextName);
      const response = await fetch(BASE + "/api/v1/library/folders/" + fid, {
        method: "PUT",
        body: fd,
      });
      const data = await response.json();
      if (!response.ok || data.error) {
        showToast(data.error || "重命名失败", "danger");
        return;
      }
      showToast("文件夹已重命名为「" + (data.name || nextName) + "」", "ok");
      await loadLibrary();
    } catch (error) {
      showToast("重命名失败: " + error.message, "danger");
    }
  }

  async function retryFolderFailed(fid, name) {
    try {
      const response = await fetch(BASE + "/api/v1/library/folders/" + fid + "/retry?failed_only=true", {
        method: "POST",
      });
      const data = await response.json();
      if (!response.ok || data.error) {
        showToast(data.error || "批量重试失败", "danger");
        return;
      }
      showToast("文件夹「" + (name || data.folder_name || "未命名") + "」已重试 " + (data.retried || 0) + " 项", "ok");
      await loadLibrary();
    } catch (error) {
      showToast("批量重试失败: " + error.message, "danger");
    }
  }

  async function moveFile(fileId, targetFolderId) {
    try {
      const response = await fetch(BASE + "/api/v1/library/files/" + fileId + "/move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_folder_id: targetFolderId || "" }),
      });
      const data = await response.json();
      if (!response.ok || data.error) {
        showToast(data.error || "移动失败", "danger");
        return;
      }
      showToast((data.filename || "文件") + " → " + (data.target_folder || "未分类"), "ok");
      await loadLibrary();
    } catch (error) {
      showToast("移动失败: " + error.message, "danger");
    }
  }

  async function deleteLibFile(fid, fname) {
    if (!confirm("确定删除文件 " + fname + " ？")) return;
    try {
      const response = await fetch(BASE + "/api/v1/library/files/" + fid, { method: "DELETE" });
      const data = await response.json();
      if (!response.ok || data.error) {
        showToast(data.error || "删除失败", "danger");
        return;
      }
      showToast(fname + " 已删除", "ok");
      await loadLibrary();
    } catch (error) {
      showToast("删除失败: " + error.message, "danger");
    }
  }

  async function retryLibFile(fid) {
    try {
      const response = await fetch(BASE + "/api/v1/library/files/" + fid + "/retry", { method: "POST" });
      const data = await response.json();
      if (!response.ok || data.error) {
        showToast(data.error || "重试失败", "danger");
        return;
      }
      showToast((data.filename || "文件") + " 已重新加入解析/索引", "ok");
      await loadLibrary();
    } catch (error) {
      showToast("重试失败: " + error.message, "danger");
    }
  }

  async function clearLibrary() {
    if (!confirm("确定清空全部文件？此操作不可恢复。")) return;
    try {
      const response = await fetch(BASE + "/api/v1/library/files", { method: "DELETE" });
      const data = await response.json();
      if (!response.ok || data.error) {
        showToast(data.error || "清空失败", "danger");
        return;
      }
      showToast("资料库已清空", "ok");
      await loadLibrary();
    } catch (error) {
      showToast("清空失败: " + error.message, "danger");
    }
  }

  async function showFileDetail(fid) {
    try {
      const response = await fetch(BASE + "/api/v1/library/files/" + fid);
      const file = await response.json();
      const latestJob = file.latest_ingest_job || null;
      const vectorIndex = file.vector_index || (latestJob && latestJob.stage === "indexed" ? latestJob.payload : null);
      let html =
        '<div class="modal-row"><div class="modal-label">文件名</div><div class="modal-val" style="font-weight:600">' +
        file.filename +
        "</div></div>";
      html +=
        '<div class="modal-row"><div class="modal-label">类型</div><div class="modal-val"><span class="badge running">' +
        file.file_type +
        "</span> (" +
        file.extension +
        ")</div></div>";
      html +=
        '<div class="modal-row"><div class="modal-label">大小</div><div class="modal-val">' +
        (file.size_bytes > 1048576
          ? (file.size_bytes / 1048576).toFixed(1) + " MB"
          : (file.size_bytes / 1024).toFixed(0) + " KB") +
        "</div></div>";
      html +=
        '<div class="modal-row"><div class="modal-label">项目</div><div class="modal-val">' +
        file.project_id +
        "</div></div>";
      html +=
        '<div class="modal-row"><div class="modal-label">上传时间</div><div class="modal-val">' +
        (file.uploaded_at || "").replace("T", " ").slice(0, 19) +
        "</div></div>";
      html +=
        '<div class="modal-row"><div class="modal-label">解析状态</div><div class="modal-val">' +
        (file.parsed
          ? '<span class="badge completed">已解析</span>'
          : '<span class="badge pending">未解析</span>') +
        "</div></div>";
      if (latestJob) {
        const jobBadgeCls =
          latestJob.status === "completed" ? "completed" : latestJob.status === "failed" ? "failed" : "running";
        html +=
          '<div class="modal-row"><div class="modal-label">最近任务</div><div class="modal-val"><span class="badge ' +
          jobBadgeCls +
          '">' +
          (latestJob.status || "—") +
          "</span> / " +
          (latestJob.stage || "—") +
          "</div></div>";
        html +=
          '<div class="modal-row"><div class="modal-label">任务时间</div><div class="modal-val">' +
          (latestJob.updated_at || "").replace("T", " ").slice(0, 19) +
          "</div></div>";
        if (latestJob.error_message) {
          html +=
            '<div class="modal-row"><div class="modal-label">任务错误</div><div class="modal-val" style="color:var(--danger)">' +
            latestJob.error_message +
            "</div></div>";
        }
        if (latestJob.status === "failed") {
          html +=
            '<div style="margin-top:12px"><button class="btn" onclick="retryLibFile(\'' +
            fid +
            "')\">重试解析 / 索引</button></div>";
        }
      }
      if (vectorIndex) {
        html +=
          '<div class="modal-row"><div class="modal-label">索引结果</div><div class="modal-val">' +
          "backend: " +
          (vectorIndex.backend || "—") +
          " · chunks: " +
          (vectorIndex.chunks != null ? vectorIndex.chunks : "—") +
          " · indexed: " +
          (vectorIndex.indexed != null ? vectorIndex.indexed : "—") +
          "</div></div>";
        if (vectorIndex.error) {
          html +=
            '<div class="modal-row"><div class="modal-label">索引错误</div><div class="modal-val" style="color:var(--danger)">' +
            vectorIndex.error +
            "</div></div>";
        }
      }

      const pr = file.parse_result;
      if (pr) {
        if (pr.error) {
          html +=
            '<div class="modal-row"><div class="modal-label">解析错误</div><div class="modal-val" style="color:var(--danger)">' +
            pr.error +
            "</div></div>";
        }
        if (pr.paragraphs != null) {
          html += '<div class="modal-row"><div class="modal-label">段落数</div><div class="modal-val">' + pr.paragraphs + "</div></div>";
        }
        if (pr.tables != null) {
          html += '<div class="modal-row"><div class="modal-label">表格数</div><div class="modal-val">' + pr.tables + "</div></div>";
        }
        if (pr.sheet_count != null) {
          html += '<div class="modal-row"><div class="modal-label">工作表</div><div class="modal-val">' + pr.sheet_count + " 张</div></div>";
        }
        if (pr.row_count != null) {
          html += '<div class="modal-row"><div class="modal-label">数据行</div><div class="modal-val">' + pr.row_count + " 行</div></div>";
        }
        if (pr.headers) {
          html +=
            '<div class="modal-row"><div class="modal-label">列头</div><div class="modal-val" style="font-size:.82rem;font-family:monospace">' +
            pr.headers.join(", ") +
            "</div></div>";
        }
        if (pr.extracted_params && pr.extracted_params.length) {
          html += '<div style="margin-top:12px"><div style="font-weight:600;margin-bottom:6px">自动提取的参数（' + pr.extracted_params.length + "个）</div>";
          html += '<table class="dtable" style="font-size:.82rem"><thead><tr><th>值</th><th>单位</th><th>类别</th></tr></thead><tbody>';
          pr.extracted_params.forEach((param) => {
            html +=
              '<tr><td style="font-weight:600">' +
              param.value +
              "</td><td>" +
              param.unit +
              '</td><td style="color:var(--muted)">' +
              param.category +
              "</td></tr>";
          });
          html += "</tbody></table></div>";
        }
        if (pr.tables_data && pr.tables_data.length) {
          html += '<div style="margin-top:12px"><div style="font-weight:600;margin-bottom:6px">表格预览（前 ' + pr.tables_data.length + " 张）</div>";
          pr.tables_data.forEach((table, index) => {
            html += '<div style="margin-top:8px;font-size:.8rem;color:var(--accent)">表 ' + (index + 1) + " (" + table.row_count + " 行)</div>";
            if (table.headers.length) {
              html += '<table class="dtable" style="font-size:.78rem"><thead><tr>';
              table.headers.forEach((header) => {
                html += "<th>" + header + "</th>";
              });
              html += "</tr></thead><tbody>";
              (table.rows || []).slice(0, 5).forEach((row) => {
                html += "<tr>";
                row.forEach((cell) => {
                  html += "<td>" + cell + "</td>";
                });
                html += "</tr>";
              });
              html += "</tbody></table>";
            }
          });
          html += "</div>";
        }
        if (pr.sheets) {
          html += '<div style="margin-top:12px"><div style="font-weight:600;margin-bottom:6px">Excel 工作表</div>';
          pr.sheets.forEach((sheet) => {
            html += '<div style="margin-top:8px;font-size:.8rem;color:var(--accent)">' + sheet.sheet + " (" + sheet.row_count + " 行)</div>";
            if (sheet.headers.length) {
              html += '<table class="dtable" style="font-size:.78rem"><thead><tr>';
              sheet.headers.forEach((header) => {
                html += "<th>" + header + "</th>";
              });
              html += "</tr></thead><tbody>";
              (sheet.rows || []).slice(0, 5).forEach((row) => {
                html += "<tr>";
                row.forEach((cell) => {
                  html += "<td>" + cell + "</td>";
                });
                html += "</tr>";
              });
              html += "</tbody></table>";
            }
          });
          html += "</div>";
        }
        if (pr.numeric_summary && pr.numeric_summary.length) {
          html += '<div style="margin-top:12px"><div style="font-weight:600;margin-bottom:6px">数值列统计</div>';
          html += '<table class="dtable" style="font-size:.82rem"><thead><tr><th>列名</th><th>最小</th><th>最大</th><th>均值</th></tr></thead><tbody>';
          pr.numeric_summary.forEach((item) => {
            html +=
              "<tr><td>" +
              item.column +
              "</td><td>" +
              item.min.toFixed(3) +
              "</td><td>" +
              item.max.toFixed(3) +
              "</td><td>" +
              item.mean.toFixed(3) +
              "</td></tr>";
          });
          html += "</tbody></table></div>";
        }
        if (pr.type === "python") {
          if (pr.classes && pr.classes.length) {
            html += '<div class="modal-row"><div class="modal-label">类定义</div><div class="modal-val" style="font-family:monospace;font-size:.82rem">' + pr.classes.join("<br>") + "</div></div>";
          }
          if (pr.functions && pr.functions.length) {
            html += '<div class="modal-row"><div class="modal-label">函数</div><div class="modal-val" style="font-family:monospace;font-size:.82rem">' + pr.functions.slice(0, 10).join("<br>") + "</div></div>";
          }
          if (pr.imports && pr.imports.length) {
            html += '<div class="modal-row"><div class="modal-label">依赖</div><div class="modal-val" style="font-size:.82rem;color:var(--muted)">' + pr.imports.join("<br>") + "</div></div>";
          }
        }
        if (pr.type === "notebook") {
          html += '<div class="modal-row"><div class="modal-label">单元格</div><div class="modal-val">共 ' + pr.total_cells + " 个（代码 " + pr.code_cells + " / Markdown " + pr.markdown_cells + "）</div></div>";
          if (pr.kernel) {
            html += '<div class="modal-row"><div class="modal-label">内核</div><div class="modal-val">' + pr.kernel + "</div></div>";
          }
          if (pr.titles && pr.titles.length) {
            html += '<div class="modal-row"><div class="modal-label">章节</div><div class="modal-val" style="font-size:.82rem">' + pr.titles.join("<br>") + "</div></div>";
          }
          if (pr.imports && pr.imports.length) {
            html += '<div class="modal-row"><div class="modal-label">依赖</div><div class="modal-val" style="font-size:.82rem;color:var(--muted)">' + pr.imports.slice(0, 10).join("<br>") + "</div></div>";
          }
        }
        if (pr.type === "pptx") {
          html += '<div class="modal-row"><div class="modal-label">幻灯片</div><div class="modal-val">' + pr.slides + " 页</div></div>";
          if (pr.slides_preview) {
            html += '<div style="margin-top:10px"><div style="font-weight:600;margin-bottom:6px">幻灯片内容预览</div>';
            pr.slides_preview.slice(0, 10).forEach((slide) => {
              html +=
                '<div style="padding:6px 0;border-bottom:1px solid var(--border);font-size:.82rem"><span style="color:var(--accent)">第 ' +
                slide.slide +
                " 页</span> " +
                slide.text_preview +
                "</div>";
            });
            html += "</div>";
          }
        }
        if (pr.code_preview) {
          html += '<div style="margin-top:12px"><div style="font-weight:600;margin-bottom:6px">代码预览</div>';
          html +=
            '<div class="modal-json" style="max-height:250px">' +
            pr.code_preview.replace(/</g, "&lt;").replace(/>/g, "&gt;") +
            "</div></div>";
        }
        if (pr.text_preview) {
          html += '<div style="margin-top:12px"><div style="font-weight:600;margin-bottom:6px">文档预览</div>';
          html += '<div class="modal-json" style="max-height:200px">' + pr.text_preview + "</div></div>";
        }
      }
      showModal(file.filename, html);
    } catch (error) {
      showToast("加载失败", "danger");
    }
  }

  document.getElementById("lib-search").addEventListener("input", loadLibrary);

  window.loadLibrary = loadLibrary;
  window.createFolder = createFolder;
  window.renameFolder = renameFolder;
  window.retryFolderFailed = retryFolderFailed;
  window.deleteFolder = deleteFolder;
  window.moveFile = moveFile;
  window.deleteLibFile = deleteLibFile;
  window.retryLibFile = retryLibFile;
  window.clearLibrary = clearLibrary;
  window.showFileDetail = showFileDetail;
})();
