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

## 交付物文案与任务汇报

FranChina 的文档直接服务在法中国留学生。所有用户可见的文档页面（`.md`）、前端组件、PDF 附件、图表、截图及导出文件均只服务产品与留学生业务目标，必须呈现为真实的线上产品内容。

- **禁止暴露思考过程**：严禁把 agent 的思考过程、实现理由、设计推理、调试过程、后续计划写进文档页面或任何交付物中。
- **禁止出现解释型自述文案**：文档与 UI 中严禁出现「我将/我们可以/本页面用于展示/这里会/用于说明/实现了」等以第一人称或助手视角的解释型套话，除非该文本原本就是系统功能性的帮助提示或空状态文案。
- **逻辑与取舍分离**：实现思路、验证方式、限制与技术取舍只允许记录在向用户的对话汇报、代码注释、PR 描述或计划文档中。
- **例外情况**：仅在用户明确要求于交付物中体现「设计说明/工作记录/版本变更」时方可写入。
- **任务交付汇报准则**：向用户汇报任务交付成果时，回复说明必须直接、准确反映最终交付结果（修改了哪些页面、新增了什么内容、验证状态），严禁通篇罗列中间排查、调试与试错的流水账。

## 构建与开发命令

- `python -m venv .venv`：创建本地虚拟环境。
- `pip install -r requirements.txt`：安装 MkDocs 及所需插件。
- `python -m mkdocs serve`：在 `http://127.0.0.1:8000` 启动支持热重载的本地预览。
- `python -m mkdocs build --strict --clean`：执行严格的干净构建，任何警告都会导致失败。
- `python scripts/update_currency.py`：获取远程汇率并重写生成数据，仅在任务明确要求更新汇率时运行。

在 Windows 上优先使用 `.venv/Scripts/python -m mkdocs ...`，确保使用虚拟环境中的插件版本。本地预览也可通过 `.claude/launch.json` 中名为 `mkdocs` 的配置启动。

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

### 排版规范与代码块边界（禁止大黑框）

FranChina 采用 Material for MkDocs 主题，深色代码块在文档中具有强烈的视觉比重。

- **严禁代码块滥用（禁止大黑框）**：严禁使用代码块（` ``` ` 或 `<pre>`）包裹大段常规说明文字、办事指南步骤、材料清单或中法文对照内容。
- **标准排版规范**：
  - 普通文本一律使用标准 Markdown 段落、无序列表（`-`）、有序列表（`1.`）或表格排版。
  - 需要强调、提示或折叠补充的内容，必须使用 Material 提供的提示块（Admonitions，如 `!!! note "提示标题"`、`!!! warning "注意事项"`、`???+ tip "折叠补充"`），严禁为了“外框视觉”而滥用代码块。
- **代码块的适用边界**：代码块（` ``` `）仅严格用于展示真实可执行的代码、脚本、配置文件片段或终端命令行（如 `python -m mkdocs serve`）。

### 标题锚点

`toc` 扩展未配置 `slugify`，纯中文标题的锚点按出现顺序自动编号为 `_1`、`_2`……，增删或调整标题会改变后续锚点。

- 需要被站内或外部链接定位的小节，必须写显式锚点，例如 `## 购票与打卡 {#bus-validation}`。
- 不得链接到 `#_3` 这类自动编号锚点。
- 修改已有显式锚点前，先全局搜索 `#锚点名` 的引用并同步更新。

## 页面元数据与搜索引擎优化

浏览器标题、搜索结果摘要和社交分享卡片由页面 front matter 与 `overrides/main.html` 共同生成。新增或修改页面时：

- **`description` 必填**：除首页外，每个页面都在 front matter 中填写 `description`，概括本页实际覆盖的内容，长度约 30～90 个字符，过长会在搜索结果中被截断；不得写正文中没有的信息或空泛宣传语。
- **网页标题来源**：`<title>` 优先使用 front matter 的 `title`，否则使用 `mkdocs.yml` 中的导航名，而不是正文 H1。导航名较通用或在多个城市重复时（如「本地交通」「生活圈」「城市简介」），必须添加带城市名的 `title`，例如 `title: 里昂本地交通`；导航文字保持不变。
- **H1 自明**：正文 H1 脱离导航也应能看懂，城市专区页面的 H1 包含城市名，例如 `# 图卢兹本地交通`。全站的网页标题和 H1 均不应重复。
- **模板输出**：`overrides/main.html` 负责 og/twitter 分享标签，并在首页输出 `WebSite` JSON-LD 声明站点名；修改该模板时不得删除这些输出。
- **验证文件**：`docs/` 根目录下的 `google*.html`、`baidu_verify_*.html`、`5054bc86….txt`（微信验证）和 `robots.txt` 用于搜索引擎与平台验证，不得删除、移动或改名。

## 编码风格与命名约定

内容应使用简洁、可验证的中文。Markdown 标题按层级递进，不要跳级。新页面文件名采用小写 kebab-case，例如 `docs/pages/life/health-insurance.md`；不要在未更新全部引用时重命名现有混合大小写路径。修改 CSS 前先查找并复用 `docs/stylesheets/core/variables.css` 中的变量。Python 使用四空格缩进和 `snake_case` 命名。

## 无痕改动原则

文档与代码修改后必须不留痕迹，呈现出“天然如此”的整洁工程状态。

- **不留修改痕迹**：除非有特别需要，改动后严禁在 Markdown 正文、HTML、CSS 或脚本中添加类似 `<!-- modified by agent -->`、`/* 修复某某bug */` 等表明“这是为什么改的/这是谁改的”自述注释或标记。
- **只呈现最终结果**：最好的改动是看起来像没改过一样自然。不需要在文件内部解释改动本身，只保留修改后的最终正确状态。

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

严格构建的 INFO 输出也需留意：页面未加入 `nav`、Markdown 中使用 `/assets/...` 绝对链接等提示不会导致构建失败，但同样属于需要处理的问题。`minify` 插件会去掉 HTML 属性的引号，在 `site/` 中核对输出时应搜索 `name=description`、`type=application/ld+json` 这类无引号写法。

验证完成后应汇报修改文件、运行命令、通过项、未验证内容和遗留风险。

## Git、提交与 Pull Request

- 未经明确要求，不得执行 `git commit`、`git push`、合并分支或创建 PR。
- 提交建议前运行 `git status --short` 和 `git diff --check`。
- 存在删除记录时，不得盲目执行 `git add .`。
- 提交信息采用简洁的 Conventional Commits 风格前缀，如 `docs:`、`fix:`、`feat:` 和 `chore:`；每个提交只处理一个主题，例如 `docs: 更新巴黎交通指南`。
- 使用 `feature/caf-guide` 这类主题分支，并向 `main` 提交 PR。
- PR 应说明改动目的、列出受影响页面和已执行的校验、关联相关 Issue；涉及可见布局或样式变化时附截图。
- 开 PR 前先合并最新的 `origin/main` 并重新执行严格构建；不得 rebase 或强制推送已推送的分支。
- 仓库惯例使用 squash 合并，合并后的提交标题形如 `docs: 补全页面摘要 (#52)`。合并他人提交的 PR 前须获得用户对该 PR 的单独确认。
- GitHub CLI 安装在 `C:\Program Files\GitHub CLI\gh.exe`；在 Bash 中 `gh` 可能不在 `PATH`，此时使用完整路径。

### 换行符与 GitHub Desktop

- 仓库启用 `core.autocrlf=true`，工作区文件可能同时存在 LF 和 CRLF。脚本批量修改时应按字节读写或保留原有换行符；Python 在 Windows 上使用 `write_text` 会把 `\n` 写成 CRLF。提交前用 `git diff --stat` 确认没有出现整文件改动。
- 用户同时使用 GitHub Desktop，它在切换分支时会把未提交的改动自动存入名为 `!!GitHub_Desktop<分支名>` 的 stash。若发现改动“消失”，先运行 `git stash list` 核对，用 `git stash apply` 恢复并确认无误后再 `git stash drop`，不得重做或丢弃这些改动。
