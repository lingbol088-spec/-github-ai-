# GitHub AI Key Leak Scanner

扫描 GitHub 公开仓库中泄露的 **AI API 密钥**，覆盖 OpenAI / DeepSeek / 通义千问 / Kimi 等 20+ 家服务商。输出统计报告，供安全研究和媒体报道使用。

## 背景

> 据 [GitGuardian 2023 年报告](https://www.gitguardian.com/state-of-secrets-report)，GitHub 上超过 **300 万个公开仓库** 累计泄露 **1280 万个** 凭证。其中 OpenAI API 密钥泄露同比增长 **1212 倍**，月均 46,441 个——仅有 **1.8%** 的用户在收到提醒后修复了泄露，**91.6%** 的泄露密钥在 5 天后仍然有效。

本项目聚焦 AI 服务商密钥泄露这一增长最快的细分领域，提供免费、开箱即用的扫描方案。

## 快速开始

```bash
pip install -r requirements.txt
python github_key_scanner.py
```

零配置，无需 Token。

## 扫描范围

| 🌍 国外 | 🇨🇳 国内 | 🔁 中转站 |
|---------|---------|-----------|
| OpenAI | DeepSeek | one-api |
| Anthropic | 通义千问 (DashScope) | new-api |
| Google Gemini | 智谱 GLM | chatgpt-next-web |
| Groq | Moonshot Kimi | 自定义中转域名 |
| Cohere | 百川智能 | |
| Mistral | Minimax 海螺 | |
| Together AI | 阶跃星辰 | |
| Replicate | 火山引擎 (豆包) | |
| HuggingFace | 腾讯混元 | |
| Perplexity | | |

## 原理

GitHub Search API 对 `sk-` 等纯密钥模式做了**隐性屏蔽**（返回 0）。本项目改用**文件名 + 赋值语句**策略绕过：

| 策略 | 示例搜索词 |
|------|-----------|
| 搜 `.env` 文件 | `filename:.env OPENAI_API_KEY` |
| 搜配置文件 | `filename:config.json api_key` |
| 搜赋值语句 | `"OPENAI_API_KEY" "sk-" language:python` |
| 搜中转站配置 | `one-api sk- filename:env` |

下载匹配文件后用 20+ 种正则提取全部 AI 密钥格式。

## 使用

```bash
python github_key_scanner.py                    # 无 token，~3 分钟
python github_key_scanner.py --token ghp_xxx    # 有 token 加速
python github_key_scanner.py --fast             # 极速（8 个搜索词）
```

也可通过环境变量：

```bash
set GITHUB_TOKEN=ghp_xxx     # Windows
export GITHUB_TOKEN=ghp_xxx  # Linux / macOS
python github_key_scanner.py
```

## 输出

```
scan_summary.txt   — 可读报告（可直接引用到报道）
scan_result.json   — 结构化数据（密钥仅存 SHA256 hash，不存明文）
```

## 速率

| 模式 | 搜索频率 | 预计 |
|------|---------|------|
| 无 Token | 10 次/分钟 | ~3 分钟 |
| 有 Token | 30 次/分钟 | ~1 分钟 |

遇限速自动等待恢复。

## 安全

- 仅读取公开仓库，不执行任何写操作
- 密钥仅存 SHA256 hash，报告中使用脱敏格式
- Token 通过命令行参数或环境变量传入，**不硬编码**
- 仅供安全研究，请勿滥用

## License

MIT

可以的话可以赞赏一下吗喵

<img width="1456" height="1080" alt="download" src="https://github.com/user-attachments/assets/6d69d203-0e65-4817-9386-14e2131aacfd" />




