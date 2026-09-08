import mimetypes

# 确保 SVG 具有标准的 MIME 类型，修复 Windows 注册表为 image/svg 时本地预览裂图的问题
mimetypes.add_type("image/svg+xml", ".svg")


def on_startup(command, dirty):
    mimetypes.add_type("image/svg+xml", ".svg")

