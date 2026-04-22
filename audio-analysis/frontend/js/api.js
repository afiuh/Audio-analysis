/**
 * API 调用模块
 * 封装所有与后端的通信
 */

const API_BASE = "http://localhost:8000/api/audio";

/**
 * 获取监控文件夹中的文件列表
 */
async function getFileList() {
  const response = await fetch(`${API_BASE}/folder/files`);
  return response.json();
}

/**
 * 创建处理任务
 */
async function createTask(filename) {
  const response = await fetch(
    `${API_BASE}/folder/process?filename=${encodeURIComponent(filename)}`,
    { method: "POST" }
  );
  return response.json();
}

/**
 * 执行转写
 */
async function transcribe(taskId) {
  const response = await fetch(`${API_BASE}/transcribe/${taskId}`, {
    method: "POST"
  });
  return response.json();
}

/**
 * 获取任务进度
 */
async function getProgress(taskId) {
  const response = await fetch(`${API_BASE}/progress/${taskId}`);
  return response.json();
}

/**
 * 获取任务状态（包含最终结果）
 */
async function getStatus(taskId) {
  const response = await fetch(`${API_BASE}/status/${taskId}`);
  return response.json();
}

/**
 * 下载报告
 */
function downloadReport(taskId) {
  window.open(`${API_BASE}/download/${taskId}`, "_blank");
}

// 导出模块
window.AudioAPI = {
  getFileList,
  createTask,
  transcribe,
  getProgress,
  getStatus,
  downloadReport
};
