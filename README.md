# 🚀 个人AI学习助理 (Personal AI Learning Assistant)

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions Status](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY/actions/workflows/daily_digest.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY/actions)
[![Made with Gemini API](https://img.shields.io/badge/Made%20with-Gemini%20API-00758F.svg)](https://ai.google.dev/)

一个高度自动化、智能化的AI信息处理系统。它能每日自动抓取最新的AI领域文章和GitHub热门项目，利用Google Gemini API进行深度、个性化的分析解读，并将最终生成的精华速报精准推送到你的微信。



---

### 💡 项目背景

作为一名人工智能专业的学生，我每天都面临着海量的信息洪流：前沿论文、技术博客、开源项目层出不穷。如何高效地筛选出真正有价值的信息，并将其与我的专业知识体系相结合，成为了一个核心痛点。

这个项目旨在解决这一问题。它不仅仅是一个信息聚合器，更是一个**智能学习伙伴**。它利用自动化技术代替了繁琐的信息搜集工作，并通过强大的大型语言模型（LLM）将原始信息转化为**针对AI学习者量身定制的、结构化的、可操作的知识**。

---

### ✨ 核心功能

*   **📰 多源信息聚合**: 自动从多个高质量信源获取最新动态。
    *   **AI文章**: 从“机器之心”等科技媒体API获取最新文章。
    *   **开源项目**: 实时抓取GitHub Trending上最热门的Python项目。

*   **🧠 AI驱动的深度分析**:
    *   **个性化视角**: 使用精心设计的**Prompt**，指令Gemini API扮演“AI技术导师”的角色，从**在校学生**的视角进行深入浅出的解读。
    *   **结构化输出**: 将分析结果整理成包含**核心摘要、技术要点、学习价值、实践建议**等模块的Markdown格式报告，清晰易读。

*   **📲 自动化与精准推送**:
    *   **无人值守**: 基于 **GitHub Actions** 实现每日定时自动运行，完全无需人工干预。
    *   **即时送达**: 通过 **PushPlus** 将每日生成的精华速报直接推送到微信，方便随时随地学习。

*   **🛡️ 健壮的爬虫策略**:
    *   综合运用 **API请求 (`Requests`)**、**HTML解析 (`BeautifulSoup`)** 和 **浏览器自动化 (`Selenium`)**，有效应对静态和动态加载的各类网页，保证了数据获取的稳定性。

---

### 🔧 工作流程

本项目的工作流清晰、高效，形成了一个完整的数据处理闭环：

`GitHub Actions (定时触发)` -> `数据获取 (API/爬虫)` -> `内容提取 (Selenium/BS4)` -> `Gemini API (深度分析)` -> `格式化报告` -> `PushPlus (微信推送)`

---

### 🛠️ 技术栈

| 技术                  | 用途                                                         |
| --------------------- | ------------------------------------------------------------ |
| **编程语言**          | `Python 3.9+`                                                |
| **AI 核心**           | `google-generativeai` (调用 Google Gemini API)               |
| **数据采集**          | `Requests`, `BeautifulSoup4`, `Selenium`                     |
| **自动化与CI/CD**     | `GitHub Actions`                                             |
| **消息推送**          | `PushPlus` (微信消息推送服务)                                |

---

### 🚀 快速开始

#### 1. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

#### 2. 创建并激活虚拟环境 (推荐)

这可以确保项目的依赖库与你的全局Python环境隔离。

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

---

### 🔑 环境配置

为了让项目正常运行，你需要配置两个关键的API密钥。本项目通过**环境变量**来安全地管理这些密钥。

#### 1. 获取密钥

*   `GEMINI_API_KEY`: 前往 [Google AI Studio](https://ai.google.dev/) 获取。
*   `PUSHPLUS_TOKEN`: 前往 [PushPlus官网](http://www.pushplus.plus/) 获取。

#### 2. 配置密钥

*   **本地测试**:
    在你的终端中设置环境变量。
    ```bash
    # macOS / Linux
    export GEMINI_API_KEY="你的Gemini密钥"
    export PUSHPLUS_TOKEN="你的PushPlus令牌"

    # Windows (CMD)
    setx GEMINI_API_KEY "你的Gemini密钥"
    setx PUSHPLUS_TOKEN "你的PushPlus令牌"
    # (注意：Windows需要重启终端才能生效)
    ```

*   **GitHub Actions 部署 (重要!)**:
    1.  在你的GitHub仓库页面，进入 `Settings` -> `Secrets and variables` -> `Actions`。
    2.  点击 `New repository secret`。
    3.  创建两个新的Secret：
        *   `GEMINI_API_KEY`: 值为你的Gemini密钥。
        *   `PUSHPLUS_TOKEN`: 值为你的PushPlus令牌。

---

### ▶️ 如何运行

*   **本地手动运行**:
    配置好本地环境变量后，直接运行 `main.py` 即可触发一次完整的流程。
    ```bash
    python main.py
    ```

*   **自动化部署**:
    当你将代码推送到GitHub仓库后，GitHub Actions将根据 `.github/workflows/daily_digest.yml` 文件中的 `cron` 表达式，自动在设定的时间执行脚本。你无需做任何额外操作。

---

### 🗺️ 未来蓝图

这个项目还有巨大的扩展潜力，以下是一些计划中的功能：

- [ ] **引入更多信源**: 如 arXiv 每日论文、顶级AI公司技术博客 (通过RSS)。
- [ ] **数据持久化**: 引入 SQLite 数据库，用于存储历史推送、避免重复，并为未来的数据分析做准备。
- [ ] **增强交互性**: 实现通过微信发送关键词，触发特定主题的信息抓取与分析。
- [ ] **Web看板**: 使用 Flask 或 FastAPI 搭建一个简单的Web界面，用于展示和检索历史速报。

---
> 如果你觉得这个项目对你有帮助，欢迎点一个 ⭐ Star！
