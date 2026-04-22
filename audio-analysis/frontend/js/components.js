/**
 * UI 组件渲染模块
 * 包含所有 DOM 元素渲染函数
 */

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

/**
 * 获取文件图标（使用宠物图标）
 */
function getFileIcon(filename, status = 'idle') {
  return window.PetIcons.getFileIcon(filename, status);
}

/**
 * 获取状态文本
 */
function getStatusText(status) {
  const map = {
    pending: "等待",
    processing: "处理中",
    completed: "已完成",
    failed: "失败"
  };
  return map[status] || "等待";
}

/**
 * 获取阶段文本
 */
function getStageText(stage) {
  const map = {
    loading_model: "加载模型",
    transcribing: "正在转写",
    correcting: "正在修正",
    exporting: "生成报告",
    completed: "已完成",
    failed: "失败"
  };
  return map[stage] || "等待中";
}

/**
 * 格式化时间
 */
function formatTime(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}秒`;
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}分${secs}秒`;
  }
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}小时${mins}分`;
}

/**
 * 渲染文件列表项
 */
function renderFileItem(file, status = {}, isSelected = false) {
  const isDisabled = status.status && ["completed", "failed", "processing"].includes(status.status);

  return `
    <div class="file-item ${isSelected ? "selected" : ""} ${status.status || ""}">
      <input type="checkbox" class="file-checkbox"
        ${isDisabled ? "disabled" : ""}
        ${isSelected ? "checked" : ""}
        onchange="App.toggleSelect('${file.name}')">
      <span class="file-icon">${getFileIcon(file.name, status.status)}</span>
      <div class="file-info">
        <div class="file-name" title="${file.name}">${file.name}</div>
        <div class="file-meta">
          <span>${formatFileSize(file.size)}</span>
          ${status.message ? `<span>${status.message}</span>` : ""}
        </div>
      </div>
      <span class="status-badge status-${status.status || "pending"}">${getStatusText(status.status)}</span>
    </div>
  `;
}

/**
 * 渲染进度列表项（带阶段进度条）
 */
function renderProgressItem(file, status = {}) {
  const stageText = getStageText(status.stage);
  const progress = Math.round(status.progress || 0);

  // 计算各阶段进度
  const stages = [
    { key: "loading_model", threshold: 10 },
    { key: "transcribing", threshold: 60 },
    { key: "correcting", threshold: 80 },
    { key: "exporting", threshold: 95 }
  ];

  return `
    <div class="file-item ${status.status || ""}">
      <span class="file-icon">${getFileIcon(file.name, status.status)}</span>
      <div class="file-info">
        <div class="file-name">${file.name}</div>
        <div class="file-meta">
          <span>${formatFileSize(file.size)}</span>
          ${status.status === "processing" ? renderStageProgress(status) : `<span>${status.message || ""}</span>`}
        </div>
      </div>
      <span class="status-badge status-${status.status || "pending"}">
        ${status.status === "processing" ? `${progress}%` : getStatusText(status.status)}
      </span>
    </div>
  `;
}

/**
 * 渲染阶段进度条
 */
function renderStageProgress(status) {
  const progress = status.progress || 0;
  const elapsed = status.elapsed || 0;
  const remaining = status.remaining;

  // 各阶段完成状态
  const loadingDone = progress >= 10;
  const transcribingDone = progress >= 60;
  const correctingDone = progress >= 80;
  const exportingDone = progress >= 95;

  const elapsedText = formatTime(elapsed);
  const remainingText = remaining !== null && remaining !== undefined ? `剩余约 ${formatTime(remaining)}` : "";

  return `
    <span class="processing-detail">
      <div class="stage-steps">
        <div class="stage-step ${loadingDone ? "completed" : ""}"></div>
        <div class="stage-step ${transcribingDone ? "completed" : progress >= 50 ? "active" : ""}"></div>
        <div class="stage-step ${correctingDone ? "completed" : progress >= 70 ? "active" : ""}"></div>
        <div class="stage-step ${exportingDone ? "completed" : progress >= 85 ? "active" : ""}"></div>
      </div>
      <div class="stage-labels">
        <span>加载模型</span>
        <span>转写</span>
        <span>修正</span>
        <span>生成报告</span>
      </div>
      <div class="time-info">
        <span>已用时 ${elapsedText}</span>
        ${remainingText ? `<span>${remainingText}</span>` : ""}
      </div>
    </span>
  `;
}

/**
 * 渲染结果列表项
 */
function renderResultItem(file, status = {}) {
  return `
    <div class="file-item ${status.status}">
      <span class="file-icon">${getFileIcon(file.name, status.status)}</span>
      <div class="file-info">
        <div class="file-name">${file.name}</div>
        <div class="file-meta">
          ${status.status === "completed" && status.result
            ? `
              <span>时长: ${status.result.duration?.toFixed(0)}秒</span>
              <span>${status.result.correction_count || 0}句</span>
              <span>${status.result.text_length || 0}字</span>
            `
            : `<span>${status.error || ""}</span>`}
        </div>
      </div>
      <span class="status-badge status-${status.status}">${getStatusText(status.status)}</span>
    </div>
  `;
}

// 导出模块
window.Components = {
  formatFileSize,
  getFileIcon,
  getStatusText,
  getStageText,
  formatTime,
  renderFileItem,
  renderProgressItem,
  renderResultItem,
  renderStageProgress
};
