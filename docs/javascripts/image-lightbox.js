/*
 * 图片灯箱：点击指向图片文件的图片链接时，以全屏浮层打开原图，
 * 点击浮层任意位置或按 Esc 关闭。事件委托挂载在 document 上，
 * 与 Material instant navigation（局部换页）兼容。
 */
(function () {
  var IMAGE_RE = /\.(png|jpe?g|gif|webp|avif|svg)([?#]|$)/i;
  var overlay = null;
  var prevOverflow = "";

  function ensureOverlay() {
    if (overlay) return overlay;
    var style = document.createElement("style");
    style.textContent =
      ".lightbox{position:fixed;inset:0;z-index:9999;margin:0;background:rgba(0,0,0,.88);" +
      "display:flex;flex-direction:column;align-items:center;justify-content:center;" +
      "padding:16px;cursor:zoom-out}" +
      ".lightbox img{max-width:100%;max-height:calc(100vh - 32px);object-fit:contain;" +
      "box-shadow:0 4px 32px rgba(0,0,0,.5)}" +
      ".lightbox figcaption{margin-top:10px;color:#eee;font-size:.85rem;text-align:center}" +
      "@media (min-width:768px){.lightbox{padding:32px}}" +
      ".lightbox[hidden]{display:none}";
    document.head.appendChild(style);
    overlay = document.createElement("figure");
    overlay.className = "lightbox";
    overlay.hidden = true;
    overlay.innerHTML = '<img alt=""><figcaption></figcaption>';
    document.body.appendChild(overlay);
    overlay.addEventListener("click", close);
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !overlay.hidden) close();
    });
    return overlay;
  }

  function open(link) {
    var img = link.querySelector("img");
    overlay = ensureOverlay();
    overlay.querySelector("img").src = link.href;
    overlay.querySelector("figcaption").textContent = img ? (img.alt || "") : "";
    overlay.querySelector("figcaption").hidden = !img || !img.alt;
    prevOverflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    overlay.hidden = false;
  }

  function close() {
    overlay.hidden = true;
    document.documentElement.style.overflow = prevOverflow;
  }

  document.addEventListener("click", function (event) {
    if (event.defaultPrevented || event.button !== 0 ||
        event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    var link = event.target.closest ? event.target.closest("a[href]") : null;
    if (!link || !IMAGE_RE.test(link.getAttribute("href"))) return;
    if (!link.querySelector("img")) return;
    event.preventDefault();
    open(link);
  });
})();
