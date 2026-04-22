// [I16 通信] API 客户端封装模块
/**
 * 封装后端 API 调用，统一处理请求和响应。
 */

const API_BASE_URL = "http://localhost:8000";

/**
 * # [I16 通信] 上传音频文件
 * @param {File} file - 音频文件
 * @returns {Promise<{task_id: string, filename: string}>}
 */
async function uploadAudio(file) {
  // [F12 捕获] 表单构建异常
  try {
    const formData = new FormData();
    formData.append("file", file);

    // [I16 通信] 发送 POST 请求
    const response = await fetch(`${API_BASE_URL}/api/audio/upload`, {
      method: "POST",
      body: formData,
    });

    // [I16 通信] 检查 HTTP 状态
    // [F12 捕获] 网络异常
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `上传失败: ${response.status}`);
    }

    // [M5 转换] 解析响应数据
    const result = await response.json();

    // [I13 渲染] 检查业务状态码
    if (result.code !== 0) {
      throw new Error(result.message);
    }

    return result.data;
  } catch (error) {
    console.error("上传失败:", error);
    throw error;
  }
}

/**
 * # [I16 通信] 查询任务状态
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>}
 */
async function getTaskStatus(taskId) {
  // [F12 捕获] 请求异常
  try {
    // [I16 通信] 发送 GET 请求
    const response = await fetch(`${API_BASE_URL}/api/audio/status/${taskId}`, {
      method: "GET",
    });

    // [I16 通信] 检查 HTTP 状态
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `查询失败: ${response.status}`);
    }

    // [M5 转换] 解析响应数据
    const result = await response.json();

    // [I13 渲染] 检查业务状态码
    if (result.code !== 0) {
      throw new Error(result.message);
    }

    return result.data;
  } catch (error) {
    console.error("查询任务状态失败:", error);
    throw error;
  }
}

/**
 * # [I16 通信] 执行转写和修正
 * @param {string} taskId - 任务ID
 * @returns {Promise<Object>}
 */
async function transcribeAudio(taskId) {
  // [F12 捕获] 请求异常
  try {
    // [I16 通信] 发送 POST 请求
    const response = await fetch(`${API_BASE_URL}/api/audio/transcribe/${taskId}`, {
      method: "POST",
    });

    // [I16 通信] 检查 HTTP 状态
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `转写失败: ${response.status}`);
    }

    // [M5 转换] 解析响应数据
    const result = await response.json();

    // [I13 渲染] 检查业务状态码
    if (result.code !== 0) {
      throw new Error(result.message);
    }

    return result.data;
  } catch (error) {
    console.error("转写失败:", error);
    throw error;
  }
}

/**
 * # [I16 通信] 下载 Markdown 文件
 * @param {string} taskId - 任务ID
 */
function downloadMarkdown(taskId) {
  // [I13 渲染] 触发文件下载
  window.open(`${API_BASE_URL}/api/audio/download/${taskId}`, "_blank");
}

// [I13 渲染] 导出 API 方法
export { uploadAudio, getTaskStatus, transcribeAudio, downloadMarkdown };
