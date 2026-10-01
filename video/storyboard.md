# FranChina 产品介绍短视频 · 分镜

1920×1080 · 30 fps · 56.87 秒。每个场景末尾与下一场景交叉淡入 12 帧。画面元素的出现时间与旁白重点词对齐（`src/data/timeline.json` 中的 `marks`）。

## 视觉系统

所有颜色、圆角、阴影和字体来自 FranChina 站点源码，集中在 `src/theme.ts`：

| 角色 | 取值 | 来源 |
| --- | --- | --- |
| primary | `#000091` | `docs/stylesheets/core/variables.css` `--brand-primary` |
| accent | `#d85b64` / strong `#b9414d` | `--brand-accent` / `--brand-accent-strong` |
| background | `#ffffff` | `--color-page-bg` |
| surface / tint | `#ffffff` / `#f7f9ff` / `#e8edff` | `--color-surface` / `--color-surface-tint` / `--color-info-bg` |
| text / heading / muted | `#3a3a3a` / `#161616` / `#666666` | `--color-text` / `--color-heading` / `--color-text-muted` |
| border | `#dddddd` / soft `#dce5f6` / muted `#e4eaf5` | `--color-border*` |
| card | 12px 圆角、`linear-gradient(160deg,#fff 65%,#f8faff)` | `docs/stylesheets/pages/home.css` `.home-entry__card` |
| 点阵与圆盘 | `#00009128` 点阵、`#e8edff` 径向圆盘 | `home.css` `.scene-grid` / `.scene-disc` |
| 标题装饰 | 蓝 + 珊瑚短线 | `docs/stylesheets/pages/content.css` `h1::after` |
| 字体 | Noto Sans SC；路线标识用等宽字体 | `variables.css` 字体栈、`header.css`、`.route-mark` |

## 场景

### 封面（第 0 帧）

- 第 0 帧即品牌封面：左侧 `CN — ✈ — FR` 路线标识、熊猫 Logo + FranChina 字标、From China to France、「陪你走过留法生活的百宝箱」、四个真实栏目（赴法之前、抵法之后、生活指南、图卢兹专区）和域名；右侧为标出巴黎、里昂、马赛、图卢兹的法国地图与首页 Hero 的三个徽章。
- 停留约 0.6 秒后文字淡出，地图保持不动，直接接入开场镜头。
- 同一组件另导出 16:9、3:4、9:16 三张封面 PNG（`Covers` 文件夹下的 Still），竖版为上文下图。

### 1 · France intro（0.00–8.43 s）

- 承接封面地图，镜头从全法国推进到图卢兹，珊瑚色定位点脉冲。
- 六个生活主题节点沿虚线从图卢兹展开：住房、交通、银行（随「住哪里 / 怎么坐车 / 银行卡怎么开」逐个点亮），随后是行政手续、日常生活、汇率。
- 封面文字淡出后，左上角保留首页 Hero 的 `CN — ✈ — FR` 路线标识。

### 2 · Information chaos（8.43–16.93 s）

- 八张卡片从画面四周进入并轻微漂浮：法语网页、留学交流群、旧经验帖、收藏夹、PDF、租房群、地图等通用信息来源，不使用任何第三方品牌。
- 念到「网站 / 群聊 / 帖子」时对应卡片轻微放大并描边。
- 念到「最新的」时旧帖日期变成警示色，四周出现问号。

### 3 · FranChina reveal（16.93–29.93 s）

- 散乱卡片向中心汇聚并消失，熊猫 Logo、FranChina 字标和「From China to France」在「FranChina」出声时首次出现。
- Logo 收到左上角，变为页头锁定组合加标语。
- 左侧三张阶段卡片沿用首页「从这里开始」入口结构：01 赴法之前（办理签证、办理公证）、02 抵法之后（办理居留、办理医保、办理房补）、03 生活指南（办理银行卡、交通出行、反诈提醒），子项随旁白逐个出现。
- 右侧浏览器窗口依次切换真实页面截图：首页 → 办理签证 → 办理居留 → 租房防骗 → 首页「从这里开始」。
- 连线把当前阶段连到浏览器，结尾一条蓝珊瑚进度线依次扫过三张卡片。

### 4 · Toulouse focus（29.93–41.43 s）

- 地图从全法国推进到图卢兹，再移到画面左侧，标出「法国第四大城市」「12 万+ 大学生」（出自 `docs/pages/toulouse/index.md`）。
- 顶部展示图卢兹专区的真实导航：城市简介、本地交通、生活圈、治安指南、餐厅卫生查询、图卢兹学联。
- 四张卡片按旁白出现，每张都是对应页面的真实截图裁切：本地交通（Tisséo 票种表）、治安指南（治安分区总览图）、餐厅卫生查询（卫生检查结果地图）、图卢兹学联（秋季迎新见面会，配 UCECF-ST 页面截图）。
- 图卢兹定位点与当前卡片之间的连线带脉冲点。

### 5 · Exchange rate（41.43–49.93 s）

- 标题卡沿用站内页面 H1 样式：小工具 · 汇率计算器，标注「每日更新」和数据日期。
- EUR → CNY、USD → CNY 两张大号汇率卡，数字先滚动到实时汇率。
- 念到「多来源汇率」时，右侧出现来源对比表：实时汇率、中国银行、工商银行、兴业银行、银联、支付宝；选中行依次切换，左侧大数字随之平滑变化。
- 数值为 2026-10-01 线上汇率计算器数据快照（`src/data/rates.json`），底部注明「汇率仅供参考」。

### 6 · Outro（49.93–56.87 s）

- 首页截图缩小淡出，画面只留浅蓝圆盘。
- 熊猫 Logo、FranChina、From China to France 依次出现；随后是标语「陪你走过留法生活的百宝箱」和 `franchina.qzz.io`。
- 最后约 3.2 秒静止停留。

## 声音

- 旁白：真人录音，分场景对齐；字幕与画面重点词跟随录音中的停顿。
- 背景音乐：开头淡入，旁白时自动压低，片尾 Logo 停留时自然收尾。
- 旁白处理：六段录音统一音色与响度，听起来像同一次录制。
- 音效（Remotion 音效库，峰值约 -19 dB，低于人声）：镜头推进、卡片汇聚、片尾收束用 whoosh；主题节点、阶段卡片、图卢兹卡片出现用 mouseClick；浏览器换页用 pageTurn；旧帖标记、进度扫过、汇率来源切换用 uiSwitch。

## 改成 9:16

- 所有尺寸都按 `u = min(width, height) / 1080` 缩放，地图镜头、节点、截图位置由 `useVideoConfig()` 计算。
- 改竖版时，在 `Root.tsx` 注册一个 1080×1920 的 Composition，再调整各场景顶部的布局常量（主要是 Scene 3/4/5 的左右两栏改为上下两栏）。
