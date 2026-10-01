# FranChina 产品介绍视频

基于 Remotion + React + TypeScript 的 FranChina 新用户介绍短视频（1920×1080，30 fps，约 56 秒）。

- 旁白与字幕时间轴：[narration.md](narration.md)
- 分镜与视觉系统：[storyboard.md](storyboard.md)
- 外挂字幕：[captions.srt](captions.srt)
- 真人录音指南：[recording/README.md](recording/README.md)

## 目录

```text
video/
├── public/
│   ├── audio/          # 分场景旁白 MP3（generate_voiceover.py 生成）与背景音乐 music.mp3
│   ├── brand/          # 站点 Logo（来自 docs/assets/home/）
│   ├── captions/       # captions.srt 副本
│   ├── fonts/          # Noto Sans SC 子集字体 + OFL 许可
│   ├── screenshots/    # franchina.qzz.io 真实页面截图
│   └── sfx/            # Remotion 音效库中的 whoosh / page-turn / switch / mouse-click
├── scripts/
│   ├── generate_voiceover.py   # TTS 或真人录音 → 音频、timeline.json、captions.srt
│   ├── recording_align.py      # 录音停顿检测与稿件对齐
│   ├── voice_processing.py     # 多段录音统一音色与响度
│   ├── capture-screenshots.mjs # 截取站点页面
│   ├── fetch-rates.mjs         # 汇率快照 → src/data/rates.json
│   ├── build_font_subset.py    # 生成子集字体
│   └── render-stills.mjs       # 批量渲染检查帧
├── src/
│   ├── components/     # BrowserFrame、FlowNode、InfoCard、Connector、MapFocus、Caption、CoverArt 等
│   ├── scenes/         # 6 个场景
│   ├── data/           # narration.json（旁白源）、timeline.json（生成）、rates.json
│   ├── theme.ts        # 从站点 CSS 提取的设计令牌
│   ├── timeline.ts     # 场景时间与旁白重点词时间
│   ├── audio.ts        # 背景音乐位置与人声闪避
│   ├── FranChinaPromo.tsx
│   └── Root.tsx
├── media/              # 仓库 README 使用的压缩成片与封面
├── recording/          # 真人录音放这里（原始录音不进 git）
└── tts-cache/          # 逐词时间戳缓存，用于 --no-tts 重建时间轴
```

## 常用命令

```bash
npm i
npm run dev                                   # Remotion Studio 预览
npx remotion render FranChinaPromo out/franchina-promo.mp4 --codec=h264 --crf=18
npx remotion still Cover-16x9 out/covers/cover-16x9.png        # 另有 Cover-3x4、Cover-9x16
```

更新仓库 README 中的成片与封面（压缩到约 9 MB）：

```bash
npx remotion ffmpeg -i out/franchina-promo.mp4 -c:v libx264 -preset slow -crf 26 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 128k media/franchina-promo.mp4
npx remotion still Cover-16x9 media/franchina-cover.png
```

使用真人录音：按 [recording/README.md](recording/README.md) 录好放进 `recording/`，然后运行 `python scripts/generate_voiceover.py --source recording`。脚本按停顿把录音对齐到稿件（不做语音识别），统一响度并裁切成分场景音频，字幕与画面重点词随之对齐。

## 声音

- 旁白：真人录音，流程见 [recording/README.md](recording/README.md)。各段先一起处理：80 Hz 高通、按六段的中位频谱做均衡匹配、轻度压缩、统一到 -20 dBFS 人声电平并限制峰值（需要 `pip install numpy scipy`）。
- 背景音乐：`public/audio/music.mp3`（原曲第 80 秒之后的部分）。`src/audio.ts` 让曲子的自然结尾落在片尾，开头 1.2 秒淡入；旁白前 0.25 秒开始压低到 `ducked`，停顿超过约 0.45 秒回升到 `open`。换曲子后调整 `endSec` 即可。
- 音效：取自 [Remotion 音效库](https://www.remotion.dev/docs/sfx)（可免署名使用；whoosh 为 freesound 上 1bob 的 CC0 作品）。各场景用 `<Sfx>` 让音效最响处落在动画出现的那一帧，音量与提前量在 `src/components/Sfx.tsx` 的 `SOUNDS` 中调整；`showSfx` 设为 `false` 可整体关闭。

修改旁白：编辑 `src/data/narration.json`，然后运行（需要 `pip install edge-tts`）：

```bash
python scripts/generate_voiceover.py
```

脚本会重新生成音频、按实际语音长度重排各场景时长、写出 `timeline.json` 和 `captions.srt`，总时长超过 `maxSeconds`（58 秒）时报错。只调整字幕切分或 `leadIn`/`tail` 而不重新合成语音时，加 `--no-tts`。换声音用 `--voice zh-CN-XiaoxiaoNeural`。

TTS 后端封装在 `TtsProvider` 类中，换成其他服务时实现 `synthesize()`，返回 MP3 数据和逐词时间戳即可。

新增中文文字后需重新生成子集字体：

```bash
python scripts/build_font_subset.py path/to/NotoSansSC[wght].ttf
```

更新截图或汇率快照：

```bash
node scripts/capture-screenshots.mjs           # 默认线上站点，可传 http://127.0.0.1:8000
node scripts/fetch-rates.mjs
```

## 许可

- Remotion 对 3 人以内团队免费，详见 [Remotion License](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)。
- Noto Sans SC 使用 SIL Open Font License 1.1（`public/fonts/OFL.txt`）。
