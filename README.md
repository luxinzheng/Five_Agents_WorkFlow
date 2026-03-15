# 五院制分析 × OpenClaw

> 一个更接近公开发布仓库体验的 **五院制分析** GitHub 发行版。  
> 目标已有 OpenClaw 用户能**安全、保守、可解释地**接入五院制分析。

![OpenClaw](https://img.shields.io/badge/framework-OpenClaw-blue)
![workflow](https://img.shields.io/badge/workflow-five--agent-purple)
![trigger](https://img.shields.io/badge/trigger-%E5%8F%91%E4%B8%89%E7%9C%81%E5%85%AD%E9%83%A8-orange)
![install](https://img.shields.io/badge/install-conservative-green)

---

## 这是什么

这是一个面向 **五院制分析** 的 OpenClaw 发布包，提供：

> 说明：本项目的整体发布思路与多 Agent 组织化表达，参考并改造自：  
> https://github.com/wanikua/boluobobo-ai-court-tutorial

- 五院制分析流程与规则
- 可迁移 skill
- `install.sh` / `install-lite.sh` / `doctor.sh`
- 保守型 `openclaw.json` 补丁脚本（先 dry-run，再 write）
- Telegram 单独接入模板
- Feishu 主通道默认不被改写
- 固定工作流指令：**交部议**

---

## 适合谁

适合：
- 已经在用 OpenClaw，想增量接入五院制的人
- 想把五院制分析打包成可迁移仓库的人
- 想保留 Feishu 主通道，同时把 Telegram 当测试入口的人

不太适合：
- 想一次装完整个复杂多部门王朝系统的人
- 希望安装脚本自动接管所有配置的人
- 不愿意审阅配置补丁和模板说明的人

---

## 一键安装

### 完整安装
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/luxinzheng/Five_Agents_WorkFlow/main/install.sh)
```

### 精简安装（已有 OpenClaw 用户推荐）
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/luxinzheng/Five_Agents_WorkFlow/main/install-lite.sh)
```

### 诊断
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/luxinzheng/Five_Agents_WorkFlow/main/doctor.sh)
```

---

## 安装策略（很重要）

本仓库默认采取**保守安装策略**：

- 不粗暴覆盖 `~/.openclaw/openclaw.json`
- 不默认把 Feishu 切到 `shumiyuan`
- 不默认启用 Telegram
- 不自动注入真实 token / secret

相反，它会：

- 先生成或预览补丁
- 先 dry-run
- 由你决定是否 `--write`
- 写入前做 backup
- 安装后跑 doctor

---

## 核心约定

### 五院制角色
- 枢密院 `shumiyuan`
- 中书省 `zhongshusheng`
- 尚书省 `shangshusheng`
- 门下省 `menxiasheng`
- 都察院 `duchayuan`

### 主/辅通道策略
- **Feishu：主通道，默认保持原状**
- **Telegram：可选测试入口，单独接入**

### 固定工作流指令
- **交部议**
- 含义：**强制启动五院制分析流程**

---

## 最推荐的使用路径

### 路线 A：已有 OpenClaw，想安全增量接入
1. 运行 `install-lite.sh`
2. 看 dry-run 补丁预览
3. 确认无误后执行 `apply-config-patch.py --write`
4. 运行 `doctor.sh`
5. 用 `交部议` 做 smoke test

### 路线 B：想做完整演示/发布
1. 运行 `install.sh`
2. 查看 workspace 模板与 docs
3. 审核 dry-run 补丁
4. 需要时再 `--write`
5. 如要测试 Telegram，再单独加入 isolated binding
6. 保持 Feishu 主通道不变

---

## 推荐 smoke test

```text
请调研一下油价上升对中国房地产市场的影响，交部议。
```

预期结果：
- 枢密院识别 `交部议`
- 中书省规划
- 尚书省执行
- 门下省验收
- 都察院终审
- 枢密院汇总回复

---

## 模板与占位符说明

本仓库中以下内容是**模板占位符**，发布前或使用前需要替换：

- `luxinzheng`
- `Five_Agents_WorkFlow`
- `main`
- `REPLACE_ME`
- `REPLACE_TELEGRAM_DM_ID`

请不要把这些值误认为真实默认配置。

---

## 仓库结构

```text
openclaw-wuyuan-analysis-pack/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── install.sh
├── install-lite.sh
├── doctor.sh
├── scripts/apply-config-patch.py
├── docs/install-prompt.md
├── skills/wuyuan-analysis/
├── templates/openclaw-five-agent.example.json
├── templates/config/telegram-binding.example.json
├── templates/config/trigger-semantics.md
├── templates/workspaces/
├── docs/
└── tests/trigger-cases/
```

---

## 给 AI 助手代装

如果你想让 Claude / ChatGPT / DeepSeek 等助手带你安装，直接使用：

- `docs/install-prompt.md`

里面已经明确：
- 不要粗暴覆盖配置
- 不要动 Feishu 主通道
- Telegram 只做可选 isolated 入口
- 必须保留 `交部议` 语义

---

## 文档索引

- [架构说明](./docs/architecture.md)
- [安装说明](./docs/installation.md)
- [Lite 模式](./docs/lite-mode.md)
- [Telegram 单独接入](./docs/telegram.md)
- [Feishu 主通道策略](./docs/feishu.md)
- [触发语义](./docs/trigger-semantics.md)
- [诊断说明](./docs/doctor.md)
- [安装提示词](./docs/install-prompt.md)
- [升级说明](./docs/upgrade.md)
- [Release Notes 模板](./docs/release-notes-template.md)
- [FAQ](./docs/faq.md)

---

## 发布前检查

发布前至少确认：

- 已替换 `luxinzheng / Five_Agents_WorkFlow / main`
- 已检查模板占位符说明
- 已确认 Feishu 默认不会被误改
- 已确认 Telegram 仍是可选 isolated 入口
- 已运行一次 `doctor.sh`
- 已跑一次 `交部议` smoke test

---

## 一句话定位

**这是一个聚焦“五院制分析”的 OpenClaw GitHub 发布版：更像项目仓库，而不是零散 skill 包。**
