# 🇫🇷 FranChina｜留法生活小贴士网站

**FranChina** 是一个面向中国留法学生的公益型信息站点，  
聚焦 **行前准备、行政手续、生活指南、城市经验** 等高频、刚需主题。

目标只有一句话：

> **把“学长学姐踩过的坑”，整理成清晰、可复用的指南。**

---

## 🌍 项目定位

- 🎓 面向人群：**中国留法学生（本科 / 硕士 / 博士）**
- 🧭 内容类型：操作流程 + 常见问题 + 真实经验
- 🏫 适用范围：**全法国（非单一城市）**
- 💡 原则：真实、可验证、持续更新

当前站点形态：  
👉 **基于 MkDocs + Material 主题的静态文档站点**

---

## 🧱 技术架构（简述）

- 文档框架：**MkDocs**
- 主题：**Material for MkDocs**
- 内容格式：Markdown
- 部署方式：GitHub Actions → OCI 服务器 → Nginx
- 本地预览：`mkdocs serve`

📌 **重要原则**  
- 不手动改服务器文件  
- 不直接改线上内容  
- 一切修改都通过 Git + PR

---

## 📂 项目结构

```text
franchina/
├─ docs/                     # 所有内容（Markdown）
│  ├─ index.md               # 首页
│  ├─ about.md               # 项目介绍
│  ├─ preparation/           # 行前准备
│  ├─ arrival/               # 到校 / 落地
│  ├─ life/                  # CAF / 银行 / 住房 / 交通
│  ├─ admin/                 # 签证 / 社保 / 行政
│  ├─ cities/                # 城市经验
│  └─ tips/                  # FAQ / 零散技巧
│
├─ .github/workflows/
│  └─ deploy.yml             # 自动部署（CI/CD）
│
├─ mkdocs.yml                # MkDocs 配置
├─ requirements.txt          # Python 依赖
├─ .venv/                    # 本地虚拟环境（不提交）
└─ README.md
