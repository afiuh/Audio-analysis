---
id: 004
version: 1.0
meta-actions: [R17, M20]
enforce-type: checklist
priority: high
---
## 经验卡片 #004 (Runtime)
- **触发场景：** Windows 系统下初始化 Husky Git 钩子
- **关联元动作：** [R17 绑定], [M20 初始化]
- **问题描述：** Husky pre-commit 脚本在 Windows 上报错 `#!/bin/ssh: No such file`
- **根本原因：** Git 的 CRLF/LF 换行符自动转换破坏了 Shell 脚本的 Shebang 行
- **解决方案：** 
  1. 设置 `git config core.autocrlf input`
  2. 手动将 `.husky/pre-commit` 换行符改为 LF
  3. 或使用 Node.js 脚本替代 Shell 脚本执行钩子逻辑
- **预防规则：** Windows 下配置 Husky 时必须检查换行符，建议使用 Node.js 钩子脚本
- **工具链映射：** 本模板已内置修复配置
- **状态：** ✅ 已入库
- **创建日期：** 2024-01-01
- **审核人：** 陈懿灵
