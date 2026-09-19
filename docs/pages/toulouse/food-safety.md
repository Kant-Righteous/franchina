# 餐厅卫生查询

## 餐厅卫生检查结果地图
以下是图卢兹全部受监管食品场所的**官方卫生检查记录**：蓝色圆圈是数量汇总，点开放大，店铺圆点的颜色就是最近一次检查结论。数据实时来自法国农业部 [Alim'confiance](https://alimconfiance.agriculture.gouv.fr/) 平台。

<div class="map-shell">
    <div id="toulouse-map"></div>
    <div class="map-legend" id="map-legend" role="button" tabindex="0" aria-label="图例" aria-expanded="true">
        <span class="map-legend-toggle" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 18 18"><circle cx="5.5" cy="5.5" r="3" fill="#18753c"/><circle cx="12.5" cy="5.5" r="3" fill="#0063cb"/><circle cx="5.5" cy="12.5" r="3" fill="#e2760b"/><circle cx="12.5" cy="12.5" r="3" fill="#ce0500"/></svg>
        </span>
        <div class="map-legend-body">
            <div class="row"><span class="dot" style="background:#18753c;"></span>Très satisfaisant</div>
            <div class="row"><span class="dot" style="background:#0063cb;"></span>Satisfaisant</div>
            <div class="row"><span class="dot" style="background:#e2760b;"></span>À améliorer</div>
            <div class="row"><span class="dot" style="background:#ce0500;"></span>À corriger de manière urgente</div>
        </div>
    </div>
</div>
<p class="map-error" id="map-error" hidden></p>

## 四个等级的含义

| 结论                                                                                | 含义            |
| --------------------------------------------------------------------------------- | ------------- |
| <span class="hygiene-chip hygiene-chip--green">Très satisfaisant</span>           | 无违规或仅轻微违规     |
| <span class="hygiene-chip hygiene-chip--blue">Satisfaisant</span>                 | 有违规但不严重       |
| <span class="hygiene-chip hygiene-chip--orange">À améliorer</span>                | 责令限期整改，会复查    |
| <span class="hygiene-chip hygiene-chip--red">À corriger de manière urgente</span> | 可能危害健康，可被勒令停业 |

!!! tip "门口没贴海报 ≠ 没被检查"
    检查结论海报由店家**自愿**张贴，线上查询才是可靠途径。小店常以公司注册名（raison sociale）登记，搜招牌名找不到就换关键词试试。

## 吃坏肚子了怎么办

症状严重先就医（危及生命拨 **15 / 112**），保留就诊单据；随后经官方平台 [SignalConso](https://signal.conso.gouv.fr/) 在线举报。同桌多人先后出现呕吐腹泻，很可能是聚集性食物中毒，应尽快联系上加龙省 **DDPP 31**（05 34 45 34 45，<ddpp@haute-garonne.gouv.fr>）。就医与报销流程见[医疗健康指南](../life/health.md)。

---

<p style="font-size: 0.85em; color: #999; text-align: center; margin-top: 2rem;">地图与查询数据来自法国农业部 Alim'confiance 官方开放数据平台， © OpenStreetMap。最后核验：2026-09-17</p>

<script>
(function () {
    var API = 'https://dgal.opendatasoft.com/api/explore/v2.1/catalog/datasets/export_alimconfiance/records';
    var OFFICIAL = 'https://alimconfiance.agriculture.gouv.fr/';
    var LIB_BASE = '/assets/toulouse/food-safety/';
    var SELECT = 'app_libelle_etablissement,adresse_activite,code_postal,libelle_commune,synthese_eval_sanit,app_code_synthese_eval_sanit,date_inspection,siret,code_ua,geores,filtre';
    var VERDICT = {
        1: ['Très satisfaisant', 'hygiene-chip--green'],
        2: ['Satisfaisant', 'hygiene-chip--blue'],
        3: ['À améliorer', 'hygiene-chip--orange'],
        4: ['À corriger de manière urgente', 'hygiene-chip--red']
    };
    var TYPE_LABELS = {
        'Restaurants': '餐厅',
        'Supermarchés/alimentation générale': '超市',
        'Métiers de bouche': '食品店',
        'Restauration collective': '集体食堂',
        'Producteurs fermiers': '农场直销',
        '其他': '其他'
    };

    var container = document.getElementById('toulouse-map');
    if (!container) return;

    /* 图例：PC 默认展开，小屏默认折叠，点击切换 */
    var legend = document.getElementById('map-legend');
    if (legend) {
        var setLegendOpen = function (open) {
            legend.classList.toggle('is-open', open);
            legend.setAttribute('aria-expanded', open ? 'true' : 'false');
        };
        setLegendOpen(window.matchMedia('(min-width: 700px)').matches);
        legend.addEventListener('click', function () {
            setLegendOpen(!legend.classList.contains('is-open'));
        });
        legend.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setLegendOpen(!legend.classList.contains('is-open'));
            }
        });
    }

    function showMapError() {
        var box = document.getElementById('map-error');
        if (box) {
            box.textContent = '地图数据加载失败，请刷新重试，或直接访问官方源站查询。';
            box.hidden = false;
        }
    }

    function loadStyle(href) {
        return new Promise(function (resolve, reject) {
            var link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            link.onload = resolve;
            link.onerror = reject;
            document.head.appendChild(link);
        });
    }

    function loadScript(src) {
        return new Promise(function (resolve, reject) {
            var s = document.createElement('script');
            s.src = src;
            s.onload = resolve;
            s.onerror = reject;
            document.body.appendChild(s);
        });
    }

    loadStyle(LIB_BASE + 'leaflet.css')
        .then(function () { return loadScript(LIB_BASE + 'leaflet.js'); })
        .then(function () { return loadStyle(LIB_BASE + 'MarkerCluster.css'); })
        .then(function () { return loadScript(LIB_BASE + 'leaflet.markercluster.js'); })
        .then(init)
        .catch(showMapError);

    function init() {
        var map = L.map('toulouse-map', { scrollWheelZoom: false }).setView([43.6047, 1.4442], 12);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        map.on('focus', function () { map.scrollWheelZoom.enable(); });
        map.on('blur', function () { map.scrollWheelZoom.disable(); });

        var HOME_VIEW = [43.6047, 1.4442], HOME_ZOOM = 12;
        var resetView = function () { map.setView(HOME_VIEW, HOME_ZOOM); };
        var ResetControl = L.Control.extend({
            options: { position: 'topleft' },
            onAdd: function () {
                var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                L.DomEvent.disableClickPropagation(div);
                var a = L.DomUtil.create('a', 'map-reset', div);
                a.title = '还原初始视图';
                a.setAttribute('role', 'button');
                a.setAttribute('aria-label', '还原初始视图');
                a.tabIndex = 0;
                a.innerHTML = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#3a3a3a" stroke-width="2"><circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="2.6" fill="#3a3a3a" stroke="none"/></svg>';
                a.setAttribute('style', 'display:flex;align-items:center;justify-content:center;width:30px;height:30px;padding:0;line-height:1;cursor:pointer;');
                L.DomEvent.on(a, 'click', function (e) {
                    L.DomEvent.preventDefault(e);
                    L.DomEvent.stop(e);
                    resetView();
                });
                L.DomEvent.on(a, 'keydown', function (e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        L.DomEvent.preventDefault(e);
                        resetView();
                    }
                });
                return div;
            }
        });
        map.addControl(new ResetControl());

        var clusterGroup = L.markerClusterGroup({
            showCoverageOnHover: false,
            maxClusterRadius: 55,
            iconCreateFunction: function (c) {
                return L.divIcon({
                    html: '<div class="clu">' + c.getChildCount() + '</div>',
                    className: '',
                    iconSize: [40, 40]
                });
            }
        });
        map.addLayer(clusterGroup);

        function esc(s) {
            return String(s == null ? '' : s).replace(/[&<>"']/g, function (ch) {
                return { '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#39;' }[ch];
            });
        }

        function typeOf(item) {
            return (item.filtre && item.filtre[0]) || '其他';
        }

        function markerFor(item) {
            var code = item.app_code_synthese_eval_sanit;
            var verdict = VERDICT[code] || [item.synthese_eval_sanit || '—', 'hygiene-chip--blue'];
            var marker = L.marker([item.geores.lat, item.geores.lon], {
                icon: L.divIcon({
                    className: '',
                    html: '<div class="vdot vdot--' + code + '"></div>',
                    iconSize: [17, 17],
                    iconAnchor: [8, 8]
                })
            });
            var date = item.date_inspection ? String(item.date_inspection).slice(0, 10) : '';
            /* 餐厅类可直达官方详情；其余类型官方站点按类型加载记录，深链接易落空，改链数据接口结果 */
            var isRestaurant = typeOf(item) === 'Restaurants';
            var detailUrl = isRestaurant
                ? OFFICIAL + '?siret=' + encodeURIComponent(item.siret || '')
                : API + '?where=' + encodeURIComponent('siret="' + (item.siret || '') + '"');
            var detailLabel = isRestaurant ? '官方详情 ↗' : '官方API结果 ↗';
            var html = '<div class="pop-name">' + esc(item.app_libelle_etablissement) + '</div>'
                + '<div class="pop-addr">' + esc([item.adresse_activite, item.code_postal, item.libelle_commune].filter(Boolean).join(', ')) + '</div>'
                + '<span class="hygiene-chip ' + verdict[1] + '">' + esc(verdict[0]) + '</span>'
                + (date ? ' <span style="font-size:12px;color:#666;">检查于 ' + date + '</span>' : '')
                + '<div class="pop-links">'
                + '<a href="' + detailUrl + '" target="_blank" rel="noopener">' + detailLabel + '</a>'
                + '</div>';
            marker.bindPopup(L.popup({ maxWidth: 320 }).setContent(html));
            return marker;
        }

        function applyFilter(items, activeType) {
            clusterGroup.clearLayers();
            clusterGroup.addLayers(items.filter(function (f) {
                return activeType === '全部' || typeOf(f) === activeType;
            }).map(markerFor));
        }

        function buildFilters(items) {
            var counts = {};
            items.forEach(function (f) {
                var t = typeOf(f);
                counts[t] = (counts[t] || 0) + 1;
            });
            /* 「全部」固定最左；其余按数量从多到少从左到右排；「其他」固定最右 */
            var cats = Object.keys(counts).filter(function (t) { return t !== '其他'; });
            cats.sort(function (a, b) { return counts[b] - counts[a]; });
            var order = ['全部'].concat(cats);
            if (counts['其他']) order.push('其他');
            var bar = document.createElement('div');
            bar.className = 'map-filters';
            order.forEach(function (t) {
                var n = t === '全部' ? items.length : counts[t];
                var btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'map-filter' + (t === '全部' ? ' active' : '');
                btn.title = t === '全部' ? '' : t;
                btn.innerHTML = esc(TYPE_LABELS[t] || t) + ' <span class="n">' + n + '</span>';
                btn.addEventListener('click', function () {
                    Array.prototype.forEach.call(bar.children, function (b) { b.classList.remove('active'); });
                    btn.classList.add('active');
                    applyFilter(items, t);
                });
                bar.appendChild(btn);
            });
            container.parentNode.insertBefore(bar, container);
        }

        var allItems = [];
        function fetchPage(offset) {
            var params = new URLSearchParams({
                where: 'libelle_commune="Toulouse"',
                select: SELECT,
                limit: '100',
                offset: String(offset),
                order_by: 'date_inspection desc'
            });
            return fetch(API + '?' + params.toString()).then(function (res) { return res.json(); });
        }

        /* 逐页取全量记录，再按商户去重（同一商户保留最近一次检查） */
        var fetched = 0;
        fetchPage(0).then(function step(data) {
            var total = data.total_count || 0;
            var rows = data.results || [];
            fetched += rows.length;
            rows.forEach(function (r) {
                var f = r.fields || r;
                if (f.geores && f.geores.lon) allItems.push(f);
            });
            if (fetched < total && rows.length > 0) {
                return fetchPage(fetched).then(step);
            }
            var seen = {};
            allItems = allItems.filter(function (f) {
                if (!f.code_ua) return true;
                if (seen[f.code_ua]) return false;
                seen[f.code_ua] = true;
                return true;
            });
            buildFilters(allItems);
            applyFilter(allItems, '全部');
        }).catch(showMapError);
    }
})();
</script>
