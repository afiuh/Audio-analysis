/**
 * Claude 像素艺术吉祥物图标模块
 * 基于 Claude 官方像素艺术 - 橙色小动物看月亮
 */

const PetIcons = {
  // 颜色定义
  colors: {
    pet: '#E07A5F',      // 橙色小动物
    petDark: '#C46A52',  // 深色阴影
    bg: '#1F2937',       // 深蓝灰背景
    moon: '#F3F4F6',     // 月亮白色
    moonDark: '#D1D5DB', // 月亮阴影
    star: '#FEF3C7',     // 星星黄色
    cloud: '#374151',    // 云朵深灰
    cloudLight: '#4B5563'// 云朵浅灰
  },

  // 默认/空闲状态 - 看月亮的小动物
  idle: `
    <svg viewBox="0 0 64 64" class="pet-icon pet-idle">
      <rect width="64" height="64" fill="#1F2937" rx="8"/>
      <!-- 星星 -->
      <rect x="8" y="8" width="2" height="2" fill="#FEF3C7"/>
      <rect x="52" y="12" width="2" height="2" fill="#FEF3C7"/>
      <rect x="44" y="6" width="2" height="2" fill="#FEF3C7"/>
      <!-- 云朵 -->
      <rect x="8" y="16" width="20" height="4" fill="#374151"/>
      <rect x="12" y="12" width="12" height="4" fill="#374151"/>
      <rect x="36" y="28" width="16" height="4" fill="#374151"/>
      <rect x="40" y="24" width="8" height="4" fill="#374151"/>
      <!-- 月亮 (C形) -->
      <rect x="44" y="8" width="12" height="4" fill="#F3F4F6"/>
      <rect x="52" y="12" width="4" height="4" fill="#F3F4F6"/>
      <rect x="52" y="16" width="4" height="4" fill="#F3F4F6"/>
      <rect x="52" y="20" width="4" height="4" fill="#F3F4F6"/>
      <rect x="48" y="24" width="8" height="4" fill="#F3F4F6"/>
      <!-- 月亮阴影 -->
      <rect x="48" y="8" width="4" height="4" fill="#D1D5DB"/>
      <rect x="52" y="12" width="4" height="4" fill="#D1D5DB"/>
      <!-- 小动物身体 -->
      <rect x="16" y="40" width="20" height="12" fill="#E07A5F"/>
      <rect x="12" y="44" width="4" height="8" fill="#E07A5F"/>
      <rect x="36" y="44" width="4" height="8" fill="#E07A5F"/>
      <!-- 腿 -->
      <rect x="16" y="52" width="4" height="4" fill="#C46A52"/>
      <rect x="32" y="52" width="4" height="4" fill="#C46A52"/>
      <!-- 眼睛 -->
      <rect x="20" y="44" width="2" height="2" fill="#1F2937"/>
      <rect x="28" y="44" width="2" height="2" fill="#1F2937"/>
    </svg>
  `,

  // 思考状态 - 小动物思考
  thinking: `
    <svg viewBox="0 0 64 64" class="pet-icon pet-thinking">
      <rect width="64" height="64" fill="#1F2937" rx="8"/>
      <!-- 星星 -->
      <rect x="8" y="8" width="2" height="2" fill="#FEF3C7"/>
      <rect x="52" y="12" width="2" height="2" fill="#FEF3C7"/>
      <!-- 云朵 -->
      <rect x="8" y="16" width="20" height="4" fill="#374151"/>
      <rect x="12" y="12" width="12" height="4" fill="#374151"/>
      <!-- 思考气泡 -->
      <rect x="42" y="8" width="12" height="8" fill="white" rx="1"/>
      <rect x="46" y="16" width="4" height="4" fill="white"/>
      <text x="48" y="14" text-anchor="middle" font-size="6" fill="#1F2937">?</text>
      <!-- 小动物身体 -->
      <rect x="16" y="40" width="20" height="12" fill="#E07A5F"/>
      <rect x="12" y="44" width="4" height="8" fill="#E07A5F"/>
      <rect x="36" y="44" width="4" height="8" fill="#E07A5F"/>
      <!-- 腿 -->
      <rect x="16" y="52" width="4" height="4" fill="#C46A52"/>
      <rect x="32" y="52" width="4" height="4" fill="#C46A52"/>
      <!-- 思考的眼睛 - 眯着 -->
      <rect x="20" y="45" width="4" height="1" fill="#1F2937"/>
      <rect x="28" y="45" width="4" height="1" fill="#1F2937"/>
    </svg>
  `,

  // 工作/处理中状态 - 小动物忙碌
  working: `
    <svg viewBox="0 0 64 64" class="pet-icon pet-working">
      <rect width="64" height="64" fill="#1F2937" rx="8"/>
      <!-- 星星闪烁 -->
      <rect x="8" y="8" width="2" height="2" fill="#FEF3C7">
        <animate attributeName="opacity" values="1;0.3;1" dur="0.5s" repeatCount="indefinite"/>
      </rect>
      <rect x="52" y="12" width="2" height="2" fill="#FEF3C7">
        <animate attributeName="opacity" values="0.3;1;0.3" dur="0.5s" repeatCount="indefinite"/>
      </rect>
      <!-- 云朵 -->
      <rect x="8" y="16" width="20" height="4" fill="#374151"/>
      <rect x="12" y="12" width="12" height="4" fill="#374151"/>
      <!-- 月亮 -->
      <rect x="44" y="8" width="12" height="4" fill="#F3F4F6"/>
      <rect x="52" y="12" width="4" height="4" fill="#F3F4F6"/>
      <rect x="52" y="16" width="4" height="4" fill="#F3F4F6"/>
      <rect x="48" y="24" width="8" height="4" fill="#F3F4F6"/>
      <!-- 小动物身体 - 跳动 -->
      <g transform="translate(0, 0)">
        <animateTransform attributeName="transform" type="translate" values="0,0;0,-2;0,0" dur="0.3s" repeatCount="indefinite"/>
        <rect x="16" y="40" width="20" height="12" fill="#E07A5F"/>
        <rect x="12" y="44" width="4" height="8" fill="#E07A5F"/>
        <rect x="36" y="44" width="4" height="8" fill="#E07A5F"/>
        <!-- 腿 -->
        <rect x="16" y="52" width="4" height="4" fill="#C46A52"/>
        <rect x="32" y="52" width="4" height="4" fill="#C46A52"/>
        <!-- 兴奋的眼睛 - 星星 -->
        <rect x="20" y="44" width="2" height="2" fill="#FEF3C7"/>
        <rect x="28" y="44" width="2" height="2" fill="#FEF3C7"/>
      </g>
      <!-- 处理指示器 -->
      <rect x="50" y="36" width="4" height="4" fill="#34D399">
        <animate attributeName="opacity" values="1;0;1" dur="0.5s" repeatCount="indefinite"/>
      </rect>
    </svg>
  `,

  // 完成/成功状态 - 小动物开心
  happy: `
    <svg viewBox="0 0 64 64" class="pet-icon pet-happy">
      <rect width="64" height="64" fill="#065F46" rx="8"/>
      <!-- 星星闪烁 -->
      <rect x="8" y="8" width="2" height="2" fill="#FCD34D">
        <animate attributeName="opacity" values="1;0.5;1" dur="0.3s" repeatCount="indefinite"/>
      </rect>
      <rect x="52" y="12" width="2" height="2" fill="#FCD34D">
        <animate attributeName="opacity" values="0.5;1;0.5" dur="0.3s" repeatCount="indefinite"/>
      </rect>
      <rect x="44" y="6" width="2" height="2" fill="#FCD34D"/>
      <!-- 月亮变成勾 -->
      <rect x="44" y="12" width="4" height="4" fill="#ECFDF5"/>
      <rect x="48" y="16" width="4" height="4" fill="#ECFDF5"/>
      <rect x="52" y="20" width="4" height="4" fill="#ECFDF5"/>
      <!-- 小动物身体 -->
      <rect x="16" y="40" width="20" height="12" fill="#E07A5F"/>
      <rect x="12" y="44" width="4" height="8" fill="#E07A5F"/>
      <rect x="36" y="44" width="4" height="8" fill="#E07A5F"/>
      <!-- 腿 -->
      <rect x="16" y="52" width="4" height="4" fill="#C46A52"/>
      <rect x="32" y="52" width="4" height="4" fill="#C46A52"/>
      <!-- 开心的眼睛 - 眯着 -->
      <rect x="20" y="45" width="4" height="1" fill="#1F2937"/>
      <rect x="28" y="45" width="4" height="1" fill="#1F2937"/>
      <!-- 腮红 -->
      <rect x="18" y="48" width="2" height="2" fill="#FCA5A5"/>
      <rect x="32" y="48" width="2" height="2" fill="#FCA5A5"/>
    </svg>
  `,

  // 失败/错误状态 - 小动物难过
  error: `
    <svg viewBox="0 0 64 64" class="pet-icon pet-error">
      <rect width="64" height="64" fill="#374151" rx="8"/>
      <!-- 星星变暗 -->
      <rect x="8" y="8" width="2" height="2" fill="#6B7280"/>
      <rect x="52" y="12" width="2" height="2" fill="#6B7280"/>
      <!-- 云朵 -->
      <rect x="8" y="16" width="20" height="4" fill="#4B5563"/>
      <rect x="12" y="12" width="12" height="4" fill="#4B5563"/>
      <!-- X 标记 -->
      <rect x="46" y="10" width="2" height="2" fill="#EF4444"/>
      <rect x="50" y="10" width="2" height="2" fill="#EF4444"/>
      <rect x="48" y="12" width="2" height="2" fill="#EF4444"/>
      <rect x="46" y="14" width="2" height="2" fill="#EF4444"/>
      <rect x="50" y="14" width="2" height="2" fill="#EF4444"/>
      <!-- 小动物身体 - 灰色 -->
      <rect x="16" y="40" width="20" height="12" fill="#9CA3AF"/>
      <rect x="12" y="44" width="4" height="8" fill="#9CA3AF"/>
      <rect x="36" y="44" width="4" height="8" fill="#9CA3AF"/>
      <!-- 腿 -->
      <rect x="16" y="52" width="4" height="4" fill="#6B7280"/>
      <rect x="32" y="52" width="4" height="4" fill="#6B7280"/>
      <!-- 难过的眼睛 -->
      <rect x="20" y="44" width="2" height="2" fill="#1F2937"/>
      <rect x="28" y="44" width="2" height="2" fill="#1F2937"/>
      <!-- 眼泪 -->
      <rect x="20" y="48" width="2" height="2" fill="#60A5FA" opacity="0.7">
        <animate attributeName="opacity" values="0.7;0;0.7" dur="1.5s" repeatCount="indefinite"/>
      </rect>
    </svg>
  `,

  // 加载/等待状态
  loading: `
    <svg viewBox="0 0 64 64" class="pet-icon pet-loading">
      <rect width="64" height="64" fill="#1F2937" rx="8"/>
      <!-- 旋转的星星 -->
      <g transform="rotate(0 32 32)">
        <animateTransform attributeName="transform" type="rotate" from="0 32 32" to="360 32 32" dur="2s" repeatCount="indefinite"/>
        <rect x="8" y="8" width="2" height="2" fill="#FEF3C7"/>
        <rect x="52" y="12" width="2" height="2" fill="#FEF3C7"/>
        <rect x="44" y="6" width="2" height="2" fill="#FEF3C7"/>
      </g>
      <!-- 云朵 -->
      <rect x="8" y="16" width="20" height="4" fill="#374151"/>
      <rect x="12" y="12" width="12" height="4" fill="#374151"/>
      <!-- 月亮 -->
      <rect x="44" y="8" width="12" height="4" fill="#F3F4F6"/>
      <rect x="52" y="12" width="4" height="4" fill="#F3F4F6"/>
      <rect x="52" y="16" width="4" height="4" fill="#F3F4F6"/>
      <rect x="48" y="24" width="8" height="4" fill="#F3F4F6"/>
      <!-- 小动物身体 -->
      <rect x="16" y="40" width="20" height="12" fill="#E07A5F"/>
      <rect x="12" y="44" width="4" height="8" fill="#E07A5F"/>
      <rect x="36" y="44" width="4" height="8" fill="#E07A5F"/>
      <!-- 腿 -->
      <rect x="16" y="52" width="4" height="4" fill="#C46A52"/>
      <rect x="32" y="52" width="4" height="4" fill="#C46A52"/>
      <!-- 眨眼的眼睛 -->
      <rect x="20" y="44" width="2" height="2" fill="#1F2937">
        <animate attributeName="height" values="2;0.5;2" dur="2s" repeatCount="indefinite"/>
      </rect>
      <rect x="28" y="44" width="2" height="2" fill="#1F2937">
        <animate attributeName="height" values="2;0.5;2" dur="2s" repeatCount="indefinite"/>
      </rect>
      <!-- 加载圆环 -->
      <rect x="30" y="56" width="4" height="4" fill="none" stroke="#E07A5F" stroke-width="1">
        <animateTransform attributeName="transform" type="rotate" from="0 32 58" to="360 32 58" dur="1s" repeatCount="indefinite"/>
      </rect>
    </svg>
  `,

  /**
   * 获取图标
   */
  getIcon(status = 'idle', filename = '') {
    switch (status) {
      case 'processing':
      case 'working':
        return this.working;
      case 'thinking':
        return this.thinking;
      case 'completed':
      case 'happy':
        return this.happy;
      case 'failed':
      case 'error':
        return this.error;
      case 'loading':
        return this.loading;
      default:
        return this.idle;
    }
  },

  getFileIcon(filename, status = 'idle') {
    return this.getIcon(status, filename);
  }
};

window.PetIcons = PetIcons;
