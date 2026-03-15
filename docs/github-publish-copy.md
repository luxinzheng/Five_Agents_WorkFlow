# GitHub 发布文案包

## 仓库首页简介（短版）

一个基于 OpenClaw 的 **五院制分析** GitHub 发布版。  
支持保守安装、五院制 workflow、`交部议` 强制触发、Telegram 作为可选 isolated 测试入口，并默认不影响 Feishu 主通道。

## 仓库首页简介（长版）

**Five_Agents_WorkFlow** 是一个基于 OpenClaw 的五院制分析发布版，目标是让已有 OpenClaw 用户能够以更安全、可解释、可迁移的方式接入五院制协作流程。

它不是三省六部全家桶，也不是覆盖式安装器；相反，它强调：
- 保守安装
- dry-run + backup + doctor
- `交部议` 固定触发语义
- 五院制内部 Agent 间 JSON 格式化交流
- Telegram 可选 isolated 测试入口
- Feishu 主通道默认保持不变

本项目的整体发布思路与多 Agent 组织化表达，参考并改造自：
- https://github.com/wanikua/boluobobo-ai-court-tutorial

## 推荐仓库描述（GitHub About）

A conservative OpenClaw release pack for five-agent analysis workflow, with `交部议` trigger semantics, JSON-formatted inter-agent handoff, optional Telegram isolated entry, and Feishu-safe defaults.

## 推荐 Topics

- openclaw
- multi-agent
- workflow
- telegram
- feishu
- ai-agent
- automation
- json
- analysis
- chinese

## 首次 Release 标题

`v0.3.0 - First public baseline release of Five_Agents_WorkFlow`

## 首次 Release 简介（短版）

首个可公开发布的 **Five_Agents_WorkFlow** 基线版本。  
聚焦五院制分析，支持保守安装、安全补丁、doctor 自检、`交部议` 固定触发、以及五院制内部 JSON 格式化交流。

## 首次 Release 文案（长版）

### Five_Agents_WorkFlow v0.3.0

这是 **Five_Agents_WorkFlow** 的首个可公开发布基线版本。

它聚焦于 **五院制分析**，目标是让已有 OpenClaw 用户可以用一种更安全、可解释、可迁移的方式接入五院制，而不是直接覆盖现有系统配置。

### 本版亮点
- 提供完整的五院制分析发布包
- 内置 `install.sh` / `install-lite.sh` / `doctor.sh`
- 增加安全补丁脚本：`scripts/apply-config-patch.py`
- 默认保持 **Feishu 主通道不变**
- 支持 **Telegram 作为可选 isolated 测试入口**
- 固化触发词：**`交部议` = 强制启动五院制分析**
- 固化规则：**五院制不同 Agent 之间交流必须 JSON 格式化**
- 补齐 README、docs、LICENSE、CHANGELOG、release notes 模板

### 安装方式
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/luxinzheng/Five_Agents_WorkFlow/main/install.sh)
```

或：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/luxinzheng/Five_Agents_WorkFlow/main/install-lite.sh)
```

### 安全边界
本项目默认采取保守安装策略：
- 不粗暴覆盖 `~/.openclaw/openclaw.json`
- 不默认改写 Feishu 主通道
- 不默认启用 Telegram
- 不自动注入真实 token / secret
- 先 dry-run，再决定是否 write

### 推荐验证
安装后建议执行：
1. `doctor.sh`
2. smoke test：

```text
请调研一下伊朗战争对中国房地产市场的影响，交部议。
```

### 参考说明
本项目的整体发布思路与多 Agent 组织化表达，参考并改造自：
- https://github.com/wanikua/boluobobo-ai-court-tutorial
