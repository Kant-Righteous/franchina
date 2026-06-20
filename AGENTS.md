# Repository Guidelines

## 项目结构与模块组织

FranChina 是基于 MkDocs 的中文文档站点。用户内容位于 `docs/pages/`，按 `admin/`、`life/`、`cities/` 等主题分类。图片、PDF、JSON 数据和图表存放在 `docs/assets/`。共享样式按职责拆分到 `docs/stylesheets/core/`、`layout/` 和 `pages/`。站点导航、主题、插件及 Markdown 扩展统一配置在 `mkdocs.yml`。自动化工作流位于 `.github/workflows/`，辅助脚本位于 `scripts/`。

## Agent 执行规则

### 任务启动前

除纯解释、单行文字修改或明显的小型修复外，修改文件前应给出 2～3 个可行方案，并说明：

- 每个方案的大致范围；
- 推荐方案及理由；
- 是否使用多智能体；
- 是否创建 worktree；
- 是否调用额外 Skill；
- 预计运行时间；
- 预计 Token 消耗。

小型文档修改默认使用单智能体、当前分支，不创建 worktree，不调用无关 Skill。不得为简单任务主动扩大范围。

### 沟通语言

除代码、命令、路径、配置键和专有名词外，默认使用中文沟通、解释和汇报。

## 构建与开发命令

- `python -m venv .venv`：创建本地虚拟环境。
- `pip install -r requirements.txt`：安装 MkDocs 及所需插件。
- `python -m mkdocs serve`：在 `http://127.0.0.1:8000` 启动支持热重载的本地预览。
- `python -m mkdocs build --strict --clean`：执行严格的干净构建，任何警告都会导致失败。
- `python scripts/update_currency.py`：获取远程汇率并重写生成数据，仅在任务明确要求更新汇率时运行。

## 内容研究与事实核验

FranChina 面向在法中国留学生。签证、居留、医保、CAF、税务、银行、交通、医疗、学校注册、费用、资格和办理期限均属于可能变化的信息。修改此类内容时：

- 必须核验当前有效信息，不得仅依赖模型记忆。
- 优先使用法国政府、公共机构、学校、运营机构和服务提供方的一手官方来源。
- 明确区分法国全国规则、城市地方规则和个人经验。
- 无法确认的内容应标注不确定性，不得补写为确定事实。
- 保留必要的法语机构名、表单名、菜单名和按钮名，并提供中文解释。
- 涉及金额、时限、申请资格或材料清单时，记录最后核验日期。
- 不得把个案经验写成适用于所有人的结论。
- 外部链接使用描述性文字，避免仅以“点击这里”作为链接文本。

## Markdown 与资源链接

- Markdown 页面、图片和附件优先使用相对于当前 `.md` 源文件的路径。
- 链接目标必须真实存在，目录名和大小写必须与仓库一致。
- 新增、移动或重命名页面后，必须同步更新全部引用和 `mkdocs.yml` 中的 `nav`。
- 原生 HTML 的 `<embed>`、`<iframe>`、`<object>` 应按浏览器最终页面 URL 的解析方式检查。
- 网站部署在域名根目录；嵌入 `docs/assets/` 下的资源时可使用 `/assets/...` 根路径。
- 不得混淆 Markdown 源文件路径、最终构建 URL 和原生 HTML 浏览器路径。

Markdown 附件示例：

```markdown
[下载 PDF](../../../assets/cities/toulouse/transport/example.pdf)
```

原生 HTML 嵌入示例：

```html
<embed src="/assets/cities/toulouse/transport/example.pdf"
       type="application/pdf"
       width="100%"
       height="500px">
```

## 编码风格与命名约定

内容应使用简洁、可验证的中文。Markdown 标题按层级递进，不要跳级。新页面文件名采用小写 kebab-case，例如 `docs/pages/life/health-insurance.md`；不要在未更新全部引用时重命名现有混合大小写路径。修改 CSS 前先查找并复用 `docs/stylesheets/core/variables.css` 中的变量。Python 使用四空格缩进和 `snake_case` 命名。

## 执行边界

- 只修改任务直接涉及的部分，不得无故重写整篇文档或统一改写无关页面。
- 不得擅自改变站点信息架构、导航层级或 URL。
- 不得擅自增加新的生产依赖或 MkDocs 插件。
- 不得批量删除文件。确需删除多个文件时，先列出清单、原因和影响，等待用户确认。
- 发现非预期删除、重命名或大范围格式化时，立即停止并汇报。
- 不得修改或提交 `site/`、`.venv/`、缓存、凭据和部署密钥。
- `scripts/update_currency.py` 会修改生成数据，仅在任务明确要求时运行；不得手工修改脚本生成的数据，除非任务明确要求且已说明原因。

## 验证要求

根据改动范围执行最小充分验证。普通 Markdown 内容修改运行：

```powershell
python -m mkdocs build --strict --clean
git diff --check
git status --short
```

仓库目前没有独立的自动化测试套件或覆盖率门槛，严格构建是必要校验。涉及页面布局、CSS、原生 HTML、PDF、图片或交互效果时，还应运行 `python -m mkdocs serve`，并在浏览器中检查：

- 桌面端和移动端布局；
- 导航、站内链接及修改页面的最终 URL；
- 图片、PDF、附件、表格、提示块和折叠块；
- 浏览器控制台及 MkDocs 终端中的 404。

验证完成后应汇报修改文件、运行命令、通过项、未验证内容和遗留风险。

## Git、提交与 Pull Request

- 未经明确要求，不得执行 `git commit`、`git push`、合并分支或创建 PR。
- 提交建议前运行 `git status --short` 和 `git diff --check`。
- 存在删除记录时，不得盲目执行 `git add .`。
- 提交信息采用简洁的 Conventional Commits 风格前缀，如 `docs:`、`fix:`、`feat:` 和 `chore:`；每个提交只处理一个主题，例如 `docs: 更新巴黎交通指南`。
- 使用 `feature/caf-guide` 这类主题分支，并向 `main` 提交 PR。
- PR 应说明改动目的、列出受影响页面和已执行的校验、关联相关 Issue；涉及可见布局或样式变化时附截图。
