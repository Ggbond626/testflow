# TestFlow - AI 驱动的自动化测试用例生成系统

<div align="center">

![TestFlow Logo](frontend/public/logo.svg)

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Vue](https://img.shields.io/badge/Vue.js-3.x-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-009688.svg)

**TestFlow** 是一个现代化的、基于 AI 智能体的自动化测试用例生成与管理平台。它利用大语言模型（LLM）的能力，将需求文档自动转化为结构清晰、覆盖全面的测试用例，大幅提升测试设计效率。

[功能特性](#-核心功能) • [技术架构](#-技术栈) • [快速开始](#-快速开始) • [许可证](#-许可证)

</div>

---

## 📖 项目简介

TestFlow 旨在解决传统测试用例编写耗时、覆盖率不足的问题。通过内置的智能体工作流（Agent Workflow），系统能够模拟资深测试工程师的思维路径：

1.  **需求分析**：自动拆解复杂需求文档。
2.  **测试点生成**：基于测试理论（等价类、边界值等）生成测试点。
3.  **用例设计**：生成包含详细步骤和预期结果的完整用例。
4.  **智能优化**：自我审查并优化用例质量。

## ✨ 核心功能

### 🤖 AI 智能生成
- **一键生成**：上传需求文档，全自动生成测试用例。
- **智能体协作**：内置需求拆分、测试点生成、用例设计等多个专用智能体。
- **批量优化**：对现有用例进行 AI 批量审查与润色。

### 📁 测试管理
- **层级/列表视图**：支持按模块层级或扁平列表管理用例。
- **Excel/XMind 导入导出**：无缝对接现有工作流。
- **拖拽式管理**：直观的模块与用例管理体验。

### ⚡ 现代化体验
- **极速响应**：基于 FastAPI 的高性能后端。
- **精美 UI**：采用 Element Plus + Tailwind CSS 打造的现代化界面。
- **实时反馈**：异步任务处理，实时展示生成进度。

## 🛠 技术栈

### Backend (后端)
- **Core**: Python 3.8+, FastAPI
- **Database**: SQLite (SQLAlchemy ORM)
- **AI Integration**: OpenAI Compatible API (支持 GPT-4, Claude, 通义千问等)
- **Task Queue**: BackgroundTasks

### Frontend (前端)
- **Core**: Vue 3, TypeScript, Vite
- **UI Framework**: Element Plus
- **Styling**: Tailwind CSS
- **State Management**: Pinia

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- Git

### 1. 克隆项目
```bash
git clone https://github.com/Ggbond626/testflow.git
cd testflow
```

### ⚡ 一键启动 (推荐)

**Windows:**
双击运行根目录下的 `run.bat` 脚本，或在命令行运行：
```bash
.\run.bat
```

**Linux / macOS:**
```bash
chmod +x run.sh stop.sh
./run.sh
```

脚本会自动执行以下操作：
1.  检测系统环境（Python, Node.js）
2.  创建虚拟环境并安装后端依赖
3.  安装前端依赖
4.  启动前后端服务

### 🛑 停止服务
- **Windows**: 直接关闭弹出的命令行窗口。
- **Linux / macOS**: 运行 `./stop.sh`。

### 📦 手动安装 (可选)

如果你更喜欢手动控制每一步，可以参考以下步骤：

#### 1. 后端设置
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

#### 2. 前端设置
```bash
cd ../frontend
npm install
```

#### 3. 启动服务
```bash
# 启动后端
cd ../backend
uvicorn main:app --reload --port 9000

# 启动前端
cd ../frontend
npm run dev
```

访问 http://localhost:3000 即可开始使用 TestFlow。

## 📄 许可证

本项目采用 **[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)** (署名-非商业性使用 4.0 国际) 许可证。

❌ **禁止用于商业用途**：您不得将本项目或其衍生作品用于商业目的（如销售、付费服务等）。
✅ **允许个人学习与研究**：您可以自由下载、修改和使用本项目用于学习、研究或非营利性项目。
✅ **署名**：在使用或分发时，必须保留原作者署名。

如果您需要将本项目用于商业用途，请联系作者获取商业授权。

---

## ⭐ Star History

<a href="https://star-history.com/#Ggbond626/testflow&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Ggbond626/testflow&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Ggbond626/testflow&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Ggbond626/testflow&type=Date" />
 </picture>
</a>

---

<div align="center">
Made with ❤️ by TestFlow Team
</div>
