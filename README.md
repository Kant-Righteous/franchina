# [🇫🇷 FranChina｜留法生活小贴士网站](https://franchina.qzz.io/)

[**FranChina**](https://franchina.qzz.io/) 是一个面向中国留法学生的公益型信息站点，  
聚焦 **行前准备、行政手续、生活指南、城市经验** 等高频、刚需主题。

目标只有一句话：

> **把“学长学姐踩过的坑”，整理成清晰、可复用的指南。**

---

## 🌍 项目定位

- 🎓 面向人群：**中国留法学生（本科 / 硕士 / 博士）**
- 🧭 内容类型：操作流程 + 常见问题 + 真实经验
- 🏫 适用范围：**全法国（非单一城市）**
- 💡 原则：真实、可验证、持续更新

---

## 🧱 技术架构

- 文档框架：MkDocs
- 主题：Material for MkDocs
- 内容格式：Markdown
- 部署方式：GitHub Actions → OCI → Nginx
- 本地预览：mkdocs serve

---

## 📂 项目结构

```text
franchina/
├─ docs/                     # 所有内容（Markdown）
├─ .github/workflows/        # CI/CD
│  └─ deploy.yml
├─ mkdocs.yml                # MkDocs 配置
├─ requirements.txt          # Python 依赖
├─ .gitignore
├─ .venv/                    # 本地虚拟环境（不提交）
└─ README.md
```

---

## 🚀 快速开始（本地写作 & 预览）

### 1️⃣ 克隆仓库

```bash
git clone git@github.com:OWNER/franchina.git
cd franchina
```

### 2️⃣ 创建并启用虚拟环境（推荐）

```bash
python -m venv .venv
```

**Windows（PowerShell）**

```powershell
.\.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 3️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 4️⃣ 本地预览

```bash
mkdocs serve
```

浏览器访问：

```
http://127.0.0.1:8000
```

---

## ✍️ 内容协作流程（Contributor）

### 1️⃣ 新建内容分支（禁止直接改 main）

```bash
git checkout -b feature/your-topic
```

示例：

```text
feature/caf-guide
feature/ameli-register
feature/job-cv
```

### 2️⃣ 编写内容

- 所有内容写在 `docs/` 目录
- 使用 Markdown
- 图片放在 `docs/assets/images/`

### 3️⃣ 提交修改

```bash
git add .
git commit -m "content: update CAF guide"
git push origin feature/your-topic
```

### 4️⃣ 提交 Pull Request（PR）

- 目标分支：`main`
- 等待审核
- 合并后自动发布

---

## 🔐 分支与权限策略

- `main` 为受保护分支
- 所有改动必须通过 PR
- 合并到 `main` 后自动触发 CI/CD

---

## 🤝 如何参与

如果你是：

- 在法国学习或生活
- 有真实、可复用的经验
- 愿意把信息整理成清晰指南

欢迎通过 **Pull Request** 参与 FranChina 🙌

> **📝 贡献者声明**  
> 当您向本项目提交 Pull Request 时，即代表您同意将您的贡献内容授权给 FranChina，并同意该内容遵循本项目的 CC BY-NC-SA 4.0 许可协议对外共享。对于您独立撰写的内容，您将保留专属的署名权（在对应页面标注作者）。

---

## 📜 License

本项目文档及内容采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh-hans) 许可协议进行保护。

这意味着您可以自由地阅读、分享和演绎本项目的内容，但必须严格遵守以下条件：
- **署名 (BY)**：必须明确标明来源于 [FranChina](https://franchina.qzz.io)（提供本站的超链接）。
- **非商业性使用 (NC)**：严禁将本站内容用于任何商业目的（包括但不限于留学中介引流、付费咨询素材、商业公众号等）。
- **相同方式共享 (SA)**：如果您基于本网站的内容进行了二次创作或修改，必须采用相同的许可协议对外发布。
