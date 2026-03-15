# Five_Agents_WorkFlow v0.3.0

## 概述
这是 **Five_Agents_WorkFlow** 的首个可公开发布基线版本。  
它聚焦于 **五院制分析**，目标是让已有 OpenClaw 用户可以用一种更安全、可解释、可迁移的方式接入五院制，而不是直接覆盖现有系统配置。

本项目的整体发布思路与多 Agent 组织化表达，参考并改造自：
- https://github.com/wanikua/boluobobo-ai-court-tutorial

## 本版亮点
- 提供完整的五院制分析发布包
- 内置 `install.sh` / `install-lite.sh` / `doctor.sh`
- 增加安全补丁脚本：`scripts/apply-config-patch.py`
- 默认保持 **Feishu 主通道不变**
- 支持 **Telegram 作为可选 isolated 测试入口**
- 固化触发词：**`交部议` = 强制启动五院制分析**
- 固化规则：**五院制不同 Agent 之间交流必须 JSON 格式化**
- 补齐 README、docs、LICENSE、CHANGELOG、release notes 模板

## 安装方式
### 完整安装
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/luxinzheng/Five_Agents_WorkFlow/main/install.sh)
```

### 精简安装
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/luxinzheng/Five_Agents_WorkFlow/main/install-lite.sh)
```

### 诊断
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/luxinzheng/Five_Agents_WorkFlow/main/doctor.sh)
```

## 安全边界
本项目默认采取保守安装策略：
- 不粗暴覆盖 `~/.openclaw/openclaw.json`
- 不默认改写 Feishu 主通道
- 不默认启用 Telegram
- 不自动注入真实 token / secret
- 先 dry-run，再决定是否 write

## 推荐验证
安装后建议执行：
1. `doctor.sh`
2. 一次 smoke test：

```text
请调研一下油价上升对中国房地产市场的影响，交部议。
```

## 适用场景
适合：
- 已有 OpenClaw 用户增量接入五院制
- 想把五院制分析打包成可迁移 GitHub 项目的人
- 想保留 Feishu 主通道、把 Telegram 作为测试入口的人

不适合：
- 希望一键接管全部现有 OpenClaw 配置的人
- 希望默认获得完整多部门“王朝系统”的人

## 已知说明
- 模板文件中仍保留示例占位符，例如 `REPLACE_ME`、`REPLACE_TELEGRAM_DM_ID`，但已在文件中明确标注为模板位。
- 若你 fork 本仓库，请同步检查 README 与模板中的仓库地址是否仍指向你的实际 GitHub 路径。
