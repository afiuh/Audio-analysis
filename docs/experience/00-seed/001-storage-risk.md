---
id: 001
version: 1.0
meta-actions: [I15, F12]
enforce-type: lint
priority: high
---
## 经验卡片 #001 (Seed)
- **触发场景：** 所有涉及 localStorage 的操作
- **关联元动作：** [I15 存储], [F12 捕获]
- **预防规则：** 任何 [I15 存储] 元动作必须配对 [F12 捕获]。
- **状态：** ✅ 强制基线
