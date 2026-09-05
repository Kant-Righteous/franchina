# [🇫🇷 FranChina｜留法生活指南](https://franchina.qzz.io/)

[**FranChina**](https://franchina.qzz.io/) 是由图卢兹中国学者学生联合会（UCECF-ST）主办、面向中国留法学生的公益型信息站点。立足图卢兹，服务全法留学生，聚焦 **行前准备、行政手续、生活指南、城市经验、反诈提醒** 等高频刚需主题。

> **把“学长学姐踩过的坑”，整理成清晰、可复用的指南。**

---

## 🌍 项目定位

- 🎓 **面向人群**：中国留法学生（本科 / 硕士 / 博士 / 交换生 / 访问学者）
- 🧭 **内容类型**：权威操作流程 + 官方材料核验 + 真实生活经验 + 本地生活圈
- 🏫 **适用范围**：覆盖全法通用政策，并设有图卢兹及各大重点城市深度专区
- 💡 **核心原则**：一手来源、真实可靠、可验证、持续更新

---

## 🧭 内容板块

| 栏目 | 涵盖内容 |
| :--- | :--- |
| **✈️ 赴法之前** | 行李打包建议、办理护照、出生公证与双认证、法国签证申请指南 |
| **🛬 抵法之后** | 抵法首周待办清单、居留办理与生效（VLS-TS / 居留卡）、法国医保（Ameli）注册、CAF 房屋补助申请 |
| **生活指南** | 银行开户与管理、市内与城际交通（自行车/公交/地铁/高铁/机票）、手机通讯卡办理、住房租赁流程、医疗就诊与报销、残障学生支持、留学生专属 AI 福利等 |
| **🛡️ 反诈提醒** | 租房诈骗套路识别、二手交易与私下换汇风险、冒充公检法及物流电信诈骗防范 |
| **📍 城市专区** | **图卢兹专区**（城市简介、Tisséo 交通深度解读、学联服务与本地生活圈）；**城市指南**（巴黎、里昂、马赛等城市生活与出行指南） |
| **🛠️ 实用工具** | 在线实时汇率计算器、紧急求助电话速查、法文紧急呼叫沟通指南、全法各地学联及驻法使领馆联络方式 |

---

## 🧱 技术架构

- **静态站点框架**：[MkDocs](https://www.mkdocs.org/) + [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)，配合 HTML Minify 压缩与响应式自定义样式覆盖（`overrides/` 与 `stylesheets/`）
- **远程服务扩展**：[FranChina Remote MCP](mcp/README.md)（基于 FastMCP 构建），提供汇率查询等能力，支持 Cloudflare Access 与多用户 API Key 双模式鉴权
- **自动化流水线**：GitHub Actions
  - `ci.yml`：严格构建检查（`--strict`）、代码风格与安全策略审查
  - `deploy.yml`：主分支自动同步部署至生产服务器并联动 Cloudflare 刷新 CDN 缓存
  - `deploy_mcp.yml`：远程 MCP 服务的容器化构建、健康检查轮询与热更新发布
  - `update_currency.yml`：定时抓取官方参考汇率并自动提交更新
- **生产基础设施**：Oracle Cloud Infrastructure (OCI) + Nginx + Cloudflare（边缘缓存、SSL、DDoS 防护与 Access 隧道）

---

## 📂 项目结构

```text
franchina/
├─ .github/
│  └─ workflows/             # GitHub Actions 自动化工作流 (CI、部署、MCP、汇率更新)
├─ docs/                     # 站点 Markdown 内容与前端静态资源
│  ├─ assets/                # 图片、PDF 指南、图表及静态数据
│  ├─ pages/                 # 各栏目文档源文件 (admin / life / cities / help / etc.)
│  ├─ stylesheets/           # 模块化样式 (core / layout / pages)
│  └─ index.md               # 站点首页
├─ mcp/                      # FranChina Remote MCP 独立服务 (服务端、认证与单测)
├─ overrides/                # Material 主题模版深度定制与覆盖
├─ scripts/                  # 构建钩子与自动化维护脚本 (汇率抓取 / 缓存刷新 / 安全检查)
├─ AGENTS.md                 # 仓库协作指南与开发规约
├─ mkdocs.yml                # MkDocs 核心站点配置与导航映射
├─ requirements.txt          # Python 构建依赖清单
└─ README.md                 # 项目说明文档
```

---

## 🚀 快速开始（本地写作 & 预览）

### 1️⃣ 克隆仓库

```bash
git clone https://github.com/OWNER/franchina.git
cd franchina
```

### 2️⃣ 配置 Python 虚拟环境

```bash
python -m venv .venv
```

**Windows (PowerShell)**：

```powershell
.\.venv\Scripts\activate
```

**macOS / Linux**：

```bash
source .venv/bin/activate
```

### 3️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 4️⃣ 启动本地预览

```bash
python -m mkdocs serve
```

本地服务启动后，在浏览器访问：`http://127.0.0.1:8000` 即可实时热重载预览。

### 5️⃣ 构建严格校验

在提交内容前，推荐执行严格模式构建校验，确保无死链或语法告警：

```bash
python -m mkdocs build --strict --clean
```

> 💡 如需开发或调试远程 MCP 汇率服务，请进入 `mcp/` 目录并参阅 [mcp/README.md](mcp/README.md)。

---

## ✍️ 内容协作流程（Contributor）

欢迎在法学长学姐、学联成员及热心同学共同参与 FranChina 的内容建设！

### 1️⃣ 新建分支

禁止直接向 `main` 分支提交代码。请根据修改类型检出规范分支：

```bash
git checkout -b feature/caf-guide
# 或修复类分支: git checkout -b fix/paris-metro-rates
```

### 2️⃣ 编写与规范

- 内容源文件统一存放在 `docs/pages/` 对应子目录下；
- 遵循一手官方信息优先原则，注明办理时限、材料要求及核验日期；
- 图片等静态资源按分类存放于 `docs/assets/` 下；
- 保持相对路径引用与大小写一致。详细规约请查阅 [AGENTS.md](AGENTS.md)。

### 3️⃣ 提交修改

提交前请确认本地严格构建与差异校验通过：

```bash
git diff --check
git commit -m "docs: 更新 CAF 申请指引与材料清单"
```

提交信息建议采用约定式提交前缀（`docs:`、`fix:`、`feat:`、`chore:`）。

### 4️⃣ 提交 Pull Request（PR）

- 目标分支：`main`；
- 提交 PR 后，GitHub Actions 将自动运行完整 CI 检查；
- 审核合并后，自动化流水线将自动部署上线。

---

## 🤝 贡献者声明

当您向本项目提交 Pull Request 时，即代表您同意将您的贡献内容授权给 FranChina，并同意该内容遵循本项目的 CC BY-NC-SA 4.0 许可协议对外共享。对于您独立撰写的内容，您将保留专属的署名权（在对应页面标注作者）。

---

## 📜 许可证

本项目文档及原创内容采用 [CC BY-NC-SA 4.0 (知识共享署名-非商业性使用-相同方式共享 4.0 国际许可协议)](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans) 进行保护。

您可以自由地阅读、分享和演绎本项目的内容，但必须遵守以下条件：

- **署名 (BY)**：必须明确标明来源于 [FranChina](https://franchina.qzz.io)（提供本站的超链接）。
- **非商业性使用 (NC)**：严禁将本站内容用于任何商业目的（包括但不限于留学中介商业引流、付费咨询素材、商业公众号等）。
- **相同方式共享 (SA)**：如果您基于本网站的内容进行了二次创作或修改，必须采用相同的许可协议对外发布。
