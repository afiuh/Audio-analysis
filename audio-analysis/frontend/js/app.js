/**
 * 主应用模块
 * 处理所有业务逻辑
 */

class AudioApp {
  constructor() {
    // 数据状态
    this.allFiles = [];
    this.selectedFiles = new Set();
    this.fileStatus = {}; // { filename: { status, taskId, result, error, stage, progress, message } }
    this.processingQueue = [];
    this.overallStartTime = null;

    // DOM 引用
    this.dom = {};

    // 初始化
    this.init();
  }

  /**
   * 初始化应用
   */
  init() {
    this.cacheDom();
    this.bindEvents();
    this.initPets();
    this.loadFileList();
  }

  /**
   * 初始化宠物图标
   */
  initPets() {
    // Header 宠物
    const headerPet = document.getElementById("headerPet");
    if (headerPet) {
      headerPet.innerHTML = window.PetIcons.getIcon('idle');
    }
  }

  /**
   * 缓存 DOM 元素
   */
  cacheDom() {
    const get = id => document.getElementById(id);
    this.dom = {
      // 选择卡片
      selectCard: get("selectCard"),
      folderPath: get("folderPath"),
      loadingState: get("loadingState"),
      emptyState: get("emptyState"),
      fileList: get("fileList"),
      selectActions: get("selectActions"),
      startBatchBtn: get("startBatchBtn"),
      selectAllBtn: get("selectAllBtn"),
      selectNoneBtn: get("selectNoneBtn"),
      selectedCount: get("selectedCount"),
      btnCount: get("btnCount"),
      refreshBtn: get("refreshBtn"),
      errorMessage: get("errorMessage"),

      // 进度卡片
      progressCard: get("progressCard"),
      progressFileList: get("progressFileList"),
      progressPet: get("progressPet"),
      progressCurrent: get("progressCurrent"),
      progressTotal: get("progressTotal"),
      progressCompleted: get("progressCompleted"),
      progressFailed: get("progressFailed"),
      currentFileName: get("currentFileName"),
      overallPercent: get("overallPercent"),
      overallProgressBar: get("overallProgressBar"),
      timeElapsed: get("timeElapsed"),
      timeRemaining: get("timeRemaining"),

      // 结果卡片
      resultCard: get("resultCard"),
      resultFileList: get("resultFileList"),
      statTotal: get("statTotal"),
      statCompleted: get("statCompleted"),
      statFailed: get("statFailed"),
      statTotalDuration: get("statTotalDuration"),
      openReportsBtn: get("openReportsBtn"),
      restartBtn: get("restartBtn")
    };
  }

  /**
   * 绑定事件
   */
  bindEvents() {
    this.dom.selectAllBtn.addEventListener("click", () => this.selectAll());
    this.dom.selectNoneBtn.addEventListener("click", () => this.selectNone());
    this.dom.startBatchBtn.addEventListener("click", () => this.startBatchProcess());
    this.dom.refreshBtn.addEventListener("click", () => this.loadFileList());
    this.dom.openReportsBtn.addEventListener("click", () => this.openReportsFolder());
    this.dom.restartBtn.addEventListener("click", () => this.resetToStart());
  }

  // ==================== 文件列表 ====================

  /**
   * 加载文件列表
   */
  async loadFileList() {
    this.showLoading(true);
    this.hideError();

    try {
      const data = await window.AudioAPI.getFileList();

      if (!data.success) {
        throw new Error(data.message || "获取文件列表失败");
      }

      this.dom.folderPath.textContent = data.folder;
      this.allFiles = data.files || [];
      this.fileStatus = {};

      if (this.allFiles.length === 0) {
        this.showEmpty();
      } else {
        this.showFileList();
        this.renderFileList();
      }
    } catch (error) {
      console.error("加载文件列表失败:", error);
      this.showError(`加载失败: ${error.message}`);
    } finally {
      this.showLoading(false);
    }
  }

  /**
   * 切换文件选择
   */
  toggleSelect(filename) {
    if (this.selectedFiles.has(filename)) {
      this.selectedFiles.delete(filename);
    } else {
      this.selectedFiles.add(filename);
    }
    this.renderFileList();
  }

  /**
   * 全选
   */
  selectAll() {
    this.allFiles.forEach(f => {
      const status = this.fileStatus[f.name] || {};
      if (!status.status) {
        this.selectedFiles.add(f.name);
      }
    });
    this.renderFileList();
  }

  /**
   * 取消全选
   */
  selectNone() {
    this.selectedFiles.clear();
    this.renderFileList();
  }

  // ==================== 批量处理 ====================

  /**
   * 开始批量处理
   */
  async startBatchProcess() {
    if (this.selectedFiles.size === 0) return;

    const selectedList = this.allFiles.filter(f => this.selectedFiles.has(f.name));
    this.processingQueue = [...selectedList];
    this.overallStartTime = Date.now();

    // 切换到进度卡片
    this.dom.selectCard.classList.add("hidden");
    this.dom.progressCard.classList.remove("hidden");
    this.dom.resultCard.classList.add("hidden");

    // 初始化统计
    this.initProgressStats(selectedList);

    // 标记所有文件为处理中
    selectedList.forEach(f => {
      this.selectedFiles.delete(f.name);
      this.fileStatus[f.name] = { status: "processing", stage: "pending", progress: 0 };
    });
    this.renderProgressList(selectedList);

    let completedCount = 0;
    let failedCount = 0;

    // 顺序处理文件
    for (let i = 0; i < selectedList.length; i++) {
      const file = selectedList[i];
      this.dom.progressCurrent.textContent = i + 1;
      this.dom.currentFileName.textContent = file.name;

      try {
        // 1. 创建任务
        const createData = await window.AudioAPI.createTask(file.name);
        if (!createData.success) {
          throw new Error(createData.message);
        }

        const taskId = createData.task_id;
        this.fileStatus[file.name] = { status: "processing", taskId, stage: "transcribing", progress: 0 };

        // 2. 启动异步处理（后端会立即返回）
        const transcribeData = await window.AudioAPI.transcribe(taskId);

        // 3. 轮询等待任务完成
        await this.waitForTaskCompletion(file.name, taskId);

        // 检查最终状态
        const finalStatus = this.fileStatus[file.name];
        if (finalStatus.status === "completed") {
          completedCount++;
        } else {
          failedCount++;
        }

      } catch (error) {
        console.error(`处理失败: ${file.name}`, error);
        this.fileStatus[file.name] = {
          status: "failed",
          error: error.message
        };
        failedCount++;
      }

      this.updateProgressStats(completedCount, failedCount, selectedList.length);
      this.renderProgressList(selectedList);
      this.updateOverallProgress(selectedList, i + 1, completedCount, failedCount);
    }

    // 显示结果
    this.showResults(selectedList, completedCount, failedCount);
  }

  /**
   * 轮询等待任务完成
   */
  async waitForTaskCompletion(filename, taskId) {
    let checkCount = 0;

    while (true) {
      try {
        // 获取进度
        const progressData = await window.AudioAPI.getProgress(taskId);

        if (progressData.success) {
          // 更新状态
          this.fileStatus[filename] = {
            ...this.fileStatus[filename],
            stage: progressData.stage,
            progress: progressData.progress,
            message: progressData.message || progressData.stage_text,
            elapsed: progressData.elapsed || 0,
            remaining: progressData.remaining
          };

          // 更新UI
          const progressInt = Math.round(progressData.progress || 0);
          this.dom.overallPercent.textContent = `${progressInt}%`;
          this.dom.overallProgressBar.style.width = `${progressInt}%`;
          this.dom.timeElapsed.textContent = `已用时: ${window.Components.formatTime(progressData.elapsed || 0)}`;
          if (progressData.remaining !== null && progressData.remaining !== undefined) {
            this.dom.timeRemaining.textContent = `预计剩余: ${window.Components.formatTime(progressData.remaining)}`;
          }
          // 更新宠物图标
          this.updatePetIcon(progressData.stage, progressData.progress);
          this.renderProgressList(this.processingQueue);

          // 检查是否完成
          if (progressData.stage === "completed") {
            // 获取最终结果
            const statusData = await window.AudioAPI.getStatus(taskId);
            if (statusData.success && statusData.data) {
              this.fileStatus[filename] = {
                status: "completed",
                taskId,
                result: statusData.data.result
              };
            }
            return;
          }

          // 检查是否失败
          if (progressData.stage === "failed") {
            this.fileStatus[filename] = {
              status: "failed",
              error: progressData.message || "处理失败"
            };
            return;
          }
        }

        await this.sleep(5000); // 每 5 秒轮询一次

      } catch (error) {
        console.error("轮询进度失败:", error);
        await this.sleep(5000);
      }
    }
  }

  /**
   * 睡眠工具函数
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 初始化进度统计
   */
  initProgressStats(files) {
    this.dom.progressTotal.textContent = files.length;
    this.dom.progressCompleted.textContent = "0";
    this.dom.progressFailed.textContent = "0";
    this.dom.progressCurrent.textContent = "0";
    this.dom.overallPercent.textContent = "0%";
    this.dom.overallProgressBar.style.width = "0%";
    this.dom.timeElapsed.textContent = "已用时: 0秒";
    this.dom.timeRemaining.textContent = "预计剩余: 计算中...";
  }

  /**
   * 更新进度统计
   */
  updateProgressStats(completed, failed, total) {
    this.dom.progressCompleted.textContent = completed;
    this.dom.progressFailed.textContent = failed;
  }

  /**
   * 更新整体进度
   */
  updateOverallProgress(files, current, completed, failed) {
    const total = files.length;
    const overallPercent = Math.round(((completed + failed) / total) * 100);

    this.dom.overallPercent.textContent = `${overallPercent}%`;
    this.dom.overallProgressBar.style.width = `${overallPercent}%`;
  }

  /**
   * 更新宠物图标
   */
  updatePetIcon(stage, progress) {
    let petStatus = 'thinking';
    if (stage === 'loading_model') {
      petStatus = 'thinking';
    } else if (stage === 'transcribing') {
      petStatus = 'working';
    } else if (stage === 'correcting') {
      petStatus = 'working';
    } else if (stage === 'exporting') {
      petStatus = 'working';
    } else if (stage === 'completed') {
      petStatus = 'happy';
    } else if (stage === 'failed') {
      petStatus = 'error';
    }
    this.dom.progressPet.innerHTML = window.PetIcons.getIcon(petStatus);
  }

  /**
   * 更新时间显示
   */
  updateTimeDisplay() {
    if (!this.overallStartTime) return;

    const elapsed = (Date.now() - this.overallStartTime) / 1000;
    this.dom.timeElapsed.textContent = `已用时: ${window.Components.formatTime(elapsed)}`;

    const completed = parseInt(this.dom.progressCompleted.textContent) || 0;
    const total = parseInt(this.dom.progressTotal.textContent) || 1;

    if (completed > 0) {
      const avgTime = elapsed / completed;
      const remaining = (total - completed) * avgTime;
      this.dom.timeRemaining.textContent = `预计剩余: ${window.Components.formatTime(remaining)}`;
    } else {
      this.dom.timeRemaining.textContent = "预计剩余: 计算中...";
    }
  }

  // ==================== 结果展示 ====================

  /**
   * 显示结果
   */
  showResults(files, completed, failed) {
    this.dom.progressCard.classList.add("hidden");
    this.dom.resultCard.classList.remove("hidden");

    this.dom.statTotal.textContent = files.length;
    this.dom.statCompleted.textContent = completed;
    this.dom.statFailed.textContent = failed;

    const totalDuration = files
      .filter(f => this.fileStatus[f.name]?.result?.duration)
      .reduce((sum, f) => sum + (this.fileStatus[f.name].result.duration || 0), 0);
    this.dom.statTotalDuration.textContent = totalDuration > 0 ? totalDuration.toFixed(0) : "-";

    this.dom.resultFileList.innerHTML = files
      .map(file => window.Components.renderResultItem(file, this.fileStatus[file.name] || {}))
      .join("");
  }

  /**
   * 打开报告文件夹
   */
  openReportsFolder() {
    const exportsPath = "C:\\有用软件\\录音分析工具\\Audio-analysis\\audio-analysis\\backend\\exports";
    navigator.clipboard.writeText(exportsPath).then(() => {
      alert("报告文件夹路径已复制到剪贴板！\n请打开文件资源管理器，粘贴地址栏打开。\n\n路径：" + exportsPath);
    }).catch(() => {
      alert("请手动打开文件夹：\n" + exportsPath);
    });
  }

  /**
   * 重置到初始状态
   */
  resetToStart() {
    this.dom.resultCard.classList.add("hidden");
    this.dom.selectCard.classList.remove("hidden");
    this.renderFileList();
  }

  // ==================== UI 渲染 ====================

  /**
   * 渲染文件列表
   */
  renderFileList() {
    this.dom.fileList.innerHTML = this.allFiles
      .map(file => {
        const status = this.fileStatus[file.name] || {};
        const isSelected = this.selectedFiles.has(file.name);
        return window.Components.renderFileItem(file, status, isSelected);
      })
      .join("");

    this.updateSelectedCount();
  }

  /**
   * 渲染进度列表
   */
  renderProgressList(files) {
    this.dom.progressFileList.innerHTML = files
      .map(file => window.Components.renderProgressItem(file, this.fileStatus[file.name] || {}))
      .join("");
  }

  /**
   * 更新选中计数
   */
  updateSelectedCount() {
    const count = this.selectedFiles.size;
    this.dom.selectedCount.textContent = count;
    this.dom.btnCount.textContent = count;
    this.dom.startBatchBtn.disabled = count === 0;
  }

  // ==================== UI 状态 ====================

  showLoading(show) {
    this.dom.loadingState.classList.toggle("hidden", !show);
    // 只有在显示加载状态时才隐藏其他区域
    if (show) {
      this.dom.fileList.classList.add("hidden");
      this.dom.emptyState.classList.add("hidden");
      this.dom.selectActions.classList.add("hidden");
    }
  }

  showEmpty() {
    this.dom.emptyState.classList.remove("hidden");
    this.dom.fileList.classList.add("hidden");
    this.dom.selectActions.classList.add("hidden");
  }

  showFileList() {
    this.dom.fileList.classList.remove("hidden");
    this.dom.selectActions.classList.remove("hidden");
  }

  showError(msg) {
    this.dom.errorMessage.innerHTML = `<span>⚠️</span><span>${msg}</span>`;
    this.dom.errorMessage.classList.remove("hidden");
  }

  hideError() {
    this.dom.errorMessage.classList.add("hidden");
  }
}

// 初始化应用
window.App = null;
document.addEventListener("DOMContentLoaded", () => {
  window.App = new AudioApp();
});
