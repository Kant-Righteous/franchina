(() => {
  let cleanup = () => {};
  let mountFrame = 0;

  function setupScene(scene) {
    if (!scene) return () => {};

    const controller = new AbortController();
    const options = { signal: controller.signal };
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    const pointer = matchMedia('(hover: hover) and (pointer: fine)');
    let frame = 0;

    function reset() {
      cancelAnimationFrame(frame);
      scene.style.setProperty('--scene-x', '0px');
      scene.style.setProperty('--scene-y', '0px');
    }

    scene.addEventListener('pointermove', event => {
      if (motion.matches || !pointer.matches || event.pointerType !== 'mouse') return;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const bounds = scene.getBoundingClientRect();
        scene.style.setProperty('--scene-x', `${((event.clientX - bounds.left) / bounds.width - 0.5) * 14}px`);
        scene.style.setProperty('--scene-y', `${((event.clientY - bounds.top) / bounds.height - 0.5) * 12}px`);
      });
    }, options);
    scene.addEventListener('pointerleave', reset, options);
    motion.addEventListener('change', reset, options);
    pointer.addEventListener('change', reset, options);

    return () => {
      reset();
      controller.abort();
    };
  }

  function setupHome(article) {
    const hero = article?.querySelector('.tx-hero');
    if (!hero) return () => {};

    const controller = new AbortController();
    const options = { signal: controller.signal };
    const pointer = matchMedia('(hover: hover) and (pointer: fine)');
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    const badges = new Map([...hero.querySelectorAll('[data-home-badge-target]')]
      .map(badge => [badge.dataset.homeBadgeTarget, badge]));
    const entry = article.querySelector('.home-entry');
    entry?.querySelectorAll('[data-home-badge]').forEach(card => {
      const badge = badges.get(card.dataset.homeBadge);
      if (!badge) return;
      const sync = () => badge.classList.toggle('is-related',
        card.matches(':focus-within') || (pointer.matches && card.matches(':hover')));
      ['pointerenter', 'pointerleave', 'focusin', 'focusout'].forEach(event => {
        card.addEventListener(event, sync, options);
      });
      pointer.addEventListener('change', sync, options);
      sync();
    });

    const closing = article.querySelector('.home-closing');
    let observer;
    const reveal = () => {
      closing?.classList.remove('is-reveal-pending');
      observer?.disconnect();
    };
    if (closing && !motion.matches && 'IntersectionObserver' in window) {
      observer = new IntersectionObserver(entries => {
        if (entries.some(entry => entry.isIntersecting)) reveal();
      }, { threshold: 0.1 });
      observer.observe(closing);
      closing.classList.add('is-reveal-pending');
    }
    motion.addEventListener('change', reveal, options);

    return () => {
      controller.abort();
      reveal();
      badges.forEach(badge => badge.classList.remove('is-related'));
    };
  }

  function setupReading(article) {
    if (!article || article.querySelector('.tx-hero')) return () => {};

    const controller = new AbortController();
    const signal = controller.signal;
    const on = (node, event, handler, options = {}) => {
      node.addEventListener(event, handler, { ...options, signal });
    };
    const images = [...article.querySelectorAll('img')].filter(image => {
      return !image.closest('a, button') && !image.matches('.twemoji, .emojione');
    });
    const wrappers = [...article.querySelectorAll('.md-typeset__scrollwrap')];
    const originals = new Map([...images, ...wrappers].map(node => [
      node,
      new Map(['tabindex', 'role', 'aria-label'].map(name => [name, node.getAttribute(name)]))
    ]));
    let layoutFrame = 0;

    function restoreAttributes(node) {
      originals.get(node).forEach((value, name) => {
        if (value === null) node.removeAttribute(name);
        else node.setAttribute(name, value);
      });
    }

    function updateTables() {
      wrappers.forEach(wrapper => {
        const overflow = wrapper.scrollWidth > wrapper.clientWidth + 1;
        wrapper.classList.toggle('is-overflowing', overflow);
        if (overflow) {
          wrapper.tabIndex = 0;
          wrapper.setAttribute('role', 'region');
          wrapper.setAttribute('aria-label', '表格，可左右滚动查看完整内容');
        } else {
          restoreAttributes(wrapper);
        }
      });
    }

    function scheduleTables() {
      cancelAnimationFrame(layoutFrame);
      layoutFrame = requestAnimationFrame(updateTables);
    }

    const tableObserver = new ResizeObserver(scheduleTables);
    wrappers.forEach(wrapper => {
      tableObserver.observe(wrapper);
      const table = wrapper.querySelector('table');
      if (table) tableObserver.observe(table);
    });
    on(article, 'toggle', scheduleTables, { capture: true });
    on(window, 'resize', scheduleTables);
    updateTables();

    let closeViewer = () => {};
    let removeViewer = () => {};
    let openImage = () => {};

    function createViewer() {
      const viewer = document.createElement('dialog');
      viewer.className = 'image-viewer';
      viewer.setAttribute('aria-labelledby', 'image-viewer-title');
      viewer.innerHTML = `
        <div class="image-viewer__header">
          <h2 class="image-viewer__title" id="image-viewer-title">查看图片</h2>
          <div class="image-viewer__controls">
            <button type="button" data-viewer-action="fit" aria-label="适应窗口">适应</button>
            <button type="button" data-viewer-action="out" aria-label="缩小图片">−</button>
            <button type="button" data-viewer-action="in" aria-label="放大图片">+</button>
            <button type="button" data-viewer-action="close" aria-label="关闭图片">×</button>
          </div>
        </div>
        <div class="image-viewer__viewport">
          <div class="image-viewer__canvas"><img alt="" draggable="false"></div>
        </div>`;
      document.body.append(viewer);

      const viewport = viewer.querySelector('.image-viewer__viewport');
      const canvas = viewer.querySelector('.image-viewer__canvas');
      const image = canvas.querySelector('img');
      const title = viewer.querySelector('.image-viewer__title');
      const zoomIn = viewer.querySelector('[data-viewer-action=in]');
      const zoomOut = viewer.querySelector('[data-viewer-action=out]');
      const fitButton = viewer.querySelector('[data-viewer-action=fit]');
      const pointers = new Map();
      let trigger = null;
      let scale = 1;
      let fitScale = 1;
      let naturalWidth = 1;
      let naturalHeight = 1;
      let previousOverflow = '';
      let active = false;
      let pinch = null;
      let pan = null;

      function measureViewer() {
        const headerHeight = viewer.querySelector('.image-viewer__header').getBoundingClientRect().height;
        viewer.style.setProperty('--viewer-header', `${headerHeight}px`);
        fitScale = Math.max(0.01, Math.min(
          (viewport.clientWidth - 24) / naturalWidth,
          (viewport.clientHeight - 24) / naturalHeight,
          1
        ));
      }

      function draw() {
        const width = naturalWidth * scale;
        const height = naturalHeight * scale;
        canvas.style.width = `${Math.max(viewport.clientWidth, width)}px`;
        canvas.style.height = `${Math.max(viewport.clientHeight, height)}px`;
        image.style.width = `${width}px`;
        image.style.height = `${height}px`;
        zoomOut.disabled = scale <= fitScale + 0.001;
        zoomIn.disabled = scale >= 4;
        fitButton.textContent = `${Math.round(scale * 100)}%`;
      }

      function zoomTo(next, clientX, clientY) {
        const bounds = viewport.getBoundingClientRect();
        const x = clientX === undefined ? viewport.clientWidth / 2 : clientX - bounds.left;
        const y = clientY === undefined ? viewport.clientHeight / 2 : clientY - bounds.top;
        const offsetX = Math.max(0, (viewport.clientWidth - naturalWidth * scale) / 2);
        const offsetY = Math.max(0, (viewport.clientHeight - naturalHeight * scale) / 2);
        const imageX = (viewport.scrollLeft + x - offsetX) / scale;
        const imageY = (viewport.scrollTop + y - offsetY) / scale;
        scale = Math.max(fitScale, Math.min(4, next));
        draw();
        viewport.scrollLeft = imageX * scale + Math.max(0, (viewport.clientWidth - naturalWidth * scale) / 2) - x;
        viewport.scrollTop = imageY * scale + Math.max(0, (viewport.clientHeight - naturalHeight * scale) / 2) - y;
      }

      function fit() {
        measureViewer();
        scale = fitScale;
        draw();
        viewport.scrollLeft = 0;
        viewport.scrollTop = 0;
      }

      function release(restoreFocus = true) {
        if (!active) return;
        active = false;
        document.documentElement.style.overflow = previousOverflow;
        pointers.clear();
        pinch = null;
        pan = null;
        viewport.classList.remove('is-dragging');
        if (restoreFocus && trigger?.isConnected) trigger.focus({ preventScroll: true });
        trigger = null;
      }

      closeViewer = () => {
        if (viewer.open) viewer.close();
        release(false);
      };
      removeViewer = () => viewer.remove();
      openImage = async source => {
        if (viewer.open || !source.isConnected) return;
        trigger = source;
        title.textContent = source.alt || '查看图片';
        image.alt = source.alt;
        image.src = source.currentSrc || source.src;
        naturalWidth = source.naturalWidth || source.width || 1;
        naturalHeight = source.naturalHeight || source.height || 1;
        previousOverflow = document.documentElement.style.overflow;
        document.documentElement.style.overflow = 'hidden';
        active = true;
        viewer.showModal();
        fit();
        viewer.querySelector('[data-viewer-action=close]').focus({ preventScroll: true });
        try {
          await image.decode();
        } catch {
          if (active) closeViewer();
          return;
        }
        if (viewer.open && trigger === source) {
          naturalWidth = image.naturalWidth || naturalWidth;
          naturalHeight = image.naturalHeight || naturalHeight;
          fit();
        }
      };

      on(viewer, 'close', () => release());
      on(viewer, 'click', event => {
        const action = event.target.closest('[data-viewer-action]')?.dataset.viewerAction;
        if (action === 'close') viewer.close();
        else if (action === 'fit') fit();
        else if (action === 'in') zoomTo(scale * 1.4);
        else if (action === 'out') zoomTo(scale / 1.4);
        else if (event.target === viewer) {
          const bounds = viewer.getBoundingClientRect();
          if (event.clientX < bounds.left || event.clientX > bounds.right ||
              event.clientY < bounds.top || event.clientY > bounds.bottom) viewer.close();
        }
      });
      on(viewer, 'keydown', event => {
        if (event.key === '+' || event.key === '=') {
          event.preventDefault();
          zoomTo(scale * 1.4);
        } else if (event.key === '-') {
          event.preventDefault();
          zoomTo(scale / 1.4);
        } else if (event.key === '0') {
          event.preventDefault();
          fit();
        }
      });
      on(viewport, 'wheel', event => {
        if (!event.ctrlKey) return;
        event.preventDefault();
        zoomTo(scale * Math.exp(-event.deltaY * 0.005), event.clientX, event.clientY);
      }, { passive: false });
      on(viewport, 'dblclick', event => {
        event.preventDefault();
        zoomTo(scale > fitScale + 0.01 ? fitScale : Math.min(4, Math.max(1, fitScale * 2)), event.clientX, event.clientY);
      });

      function startGesture() {
        const points = [...pointers.values()];
        if (points.length >= 2) {
          pinch = {
            distance: Math.max(1, Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y)),
            scale
          };
          pan = null;
        } else {
          pinch = null;
          pan = points[0] || null;
        }
      }

      on(viewport, 'pointerdown', event => {
        if (event.pointerType === 'mouse' && event.button !== 0) return;
        event.preventDefault();
        pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
        viewport.setPointerCapture(event.pointerId);
        viewport.classList.add('is-dragging');
        startGesture();
      });
      on(viewport, 'pointermove', event => {
        if (!pointers.has(event.pointerId)) return;
        const point = { x: event.clientX, y: event.clientY };
        pointers.set(event.pointerId, point);
        const points = [...pointers.values()];
        if (points.length >= 2 && pinch) {
          const distance = Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
          zoomTo(pinch.scale * distance / pinch.distance,
            (points[0].x + points[1].x) / 2, (points[0].y + points[1].y) / 2);
        } else if (pan) {
          viewport.scrollLeft += pan.x - point.x;
          viewport.scrollTop += pan.y - point.y;
          pan = point;
        }
      });
      const endGesture = event => {
        pointers.delete(event.pointerId);
        startGesture();
        if (!pointers.size) viewport.classList.remove('is-dragging');
      };
      on(viewport, 'pointerup', endGesture);
      on(viewport, 'pointercancel', endGesture);
      on(window, 'resize', () => {
        if (viewer.open) fit();
      });
    }

    images.forEach(image => {
      image.setAttribute('data-image-viewer', '');
      image.tabIndex = 0;
      image.setAttribute('role', 'button');
      image.setAttribute('aria-label', `${image.alt || '图片'}，点击放大`);
      const show = () => {
        if (!document.querySelector('.image-viewer')) createViewer();
        openImage(image);
      };
      on(image, 'click', show);
      on(image, 'keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          show();
        }
      });
    });

    return () => {
      closeViewer();
      controller.abort();
      tableObserver.disconnect();
      cancelAnimationFrame(layoutFrame);
      removeViewer();
      images.forEach(image => {
        image.removeAttribute('data-image-viewer');
        restoreAttributes(image);
      });
      wrappers.forEach(wrapper => {
        wrapper.classList.remove('is-overflowing');
        restoreAttributes(wrapper);
      });
    };
  }

  function initialize() {
    cleanup();
    cancelAnimationFrame(mountFrame);
    mountFrame = requestAnimationFrame(() => {
      const stopScene = setupScene(document.querySelector('.tx-hero__image'));
      const article = document.querySelector('.md-content__inner');
      const stopHome = setupHome(article);
      const stopReading = setupReading(article);
      cleanup = () => {
        stopScene();
        stopHome();
        stopReading();
      };
    });
  }

  if (typeof document$ !== 'undefined') document$.subscribe(initialize);
  else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, { once: true });
  else initialize();
})();
