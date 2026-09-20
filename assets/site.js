// K.Z. Pendrake — client-side behaviour for the static site.
// No router: every page is pre-rendered HTML with real URLs.

(function () {
    'use strict';

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    document.addEventListener('DOMContentLoaded', function () {

        /* ── Header: solid once the hero is behind you ─────────────── */
        var header = document.getElementById('site-header');
        if (header) {
            var onScroll = function () {
                header.classList.toggle('solid', window.scrollY > 40);
            };
            onScroll();
            window.addEventListener('scroll', onScroll, { passive: true });
        }

        /* ── Mobile menu ───────────────────────────────────────────── */
        var hamburger = document.querySelector('.hamburger');
        var mobileMenu = document.getElementById('mobile-menu');
        if (hamburger && mobileMenu) {
            var closeMenu = function () {
                hamburger.setAttribute('aria-expanded', 'false');
                mobileMenu.classList.remove('open');
                document.body.style.overflow = '';
                setTimeout(function () {
                    if (!mobileMenu.classList.contains('open')) mobileMenu.hidden = true;
                }, 450);
            };
            hamburger.addEventListener('click', function () {
                var open = hamburger.getAttribute('aria-expanded') === 'true';
                if (open) { closeMenu(); return; }
                mobileMenu.hidden = false;
                void mobileMenu.offsetWidth;   // flush layout so the fade has a start value
                mobileMenu.classList.add('open');
                hamburger.setAttribute('aria-expanded', 'true');
                document.body.style.overflow = 'hidden';
            });
            mobileMenu.addEventListener('click', function (e) {
                if (e.target.closest('a')) closeMenu();
            });
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && mobileMenu.classList.contains('open')) closeMenu();
            });
        }

        /* ── Scroll reveal ─────────────────────────────────────────── */
        var revealables = document.querySelectorAll('.rv:not(.in)');
        if (reduceMotion || !('IntersectionObserver' in window)) {
            Array.prototype.forEach.call(revealables, function (el) { el.classList.add('in'); });
        } else {
            var io = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('in');
                        io.unobserve(entry.target);
                    }
                });
            // threshold 0: an excerpt page is one very tall block, and a
            // fraction-of-the-element threshold would never be reached.
            }, { threshold: 0, rootMargin: '0px 0px -8% 0px' });
            Array.prototype.forEach.call(revealables, function (el) { io.observe(el); });
        }

        /* ── Book search ───────────────────────────────────────────── */
        // The index holds every edition in every language, so a German title
        // leads to the German page. Loaded once, on first use.
        var searchBox = document.querySelector('.nav-search');
        if (searchBox) {
            var toggle = searchBox.querySelector('.search-toggle');
            var panel = searchBox.querySelector('.search-panel');
            var input = searchBox.querySelector('.search-input');
            var results = searchBox.querySelector('.search-results');
            var noneText = results.dataset.none;
            // The site's own code for this page's language ("se"), not the one the
            // crawler reads off <html lang> ("sv") — the index is keyed the site's way.
            var pageLang = document.documentElement.dataset.siteLang
                || document.documentElement.lang || 'en';
            var index = null, loading = null;

            var CYR = { 'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y',
                'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
                'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sht', 'ъ': 'a', 'ь': '', 'ю': 'yu', 'я': 'ya' };

            // Fold everything to bare latin letters: Hüterin -> huterin, ß -> ss,
            // Наследницата -> naslednicata. Lets a reader type without diacritics.
            var fold = function (s) {
                return (s || '').toLowerCase()
                    .replace(/ß/g, 'ss')
                    .normalize('NFD').replace(/\p{M}/gu, '')
                    .split('').map(function (c) { return (c in CYR ? CYR[c] : c); }).join('')
                    .replace(/[^a-z0-9]+/g, ' ')
                    // ts and c are the same sound in transliteration: naslednitsa = naslednica
                    .replace(/ts/g, 'c')
                    .trim();
            };

            var loadIndex = function () {
                if (index) return Promise.resolve(index);
                if (!loading) {
                    loading = fetch('/search-index.json')
                        .then(function (r) { return r.json(); })
                        .then(function (data) {
                            index = data.map(function (e) {
                                return Object.assign({}, e, {
                                    _t: fold(e.t), _s: fold(e.s), _g: fold(e.g)
                                });
                            });
                            return index;
                        })
                        .catch(function () { index = []; return index; });
                }
                return loading;
            };

            var rank = function (entry, q) {
                var score;
                if (entry._t.indexOf(q) === 0) score = 0;
                else if (entry._t.indexOf(' ' + q) !== -1) score = 1;
                else if (entry._t.indexOf(q) !== -1) score = 2;
                else if (entry._s && entry._s.indexOf(q) !== -1) score = 3;
                else if (entry._g && entry._g.indexOf(q) !== -1) score = 4;
                else return null;
                return score * 2 + (entry.l === pageLang ? 0 : 1);
            };

            var render = function (q) {
                var folded = fold(q);
                if (folded.length < 2) { results.hidden = true; results.innerHTML = ''; return; }
                var hits = [];
                (index || []).forEach(function (e) {
                    var s = rank(e, folded);
                    if (s !== null) hits.push([s, e]);
                });
                hits.sort(function (a, b) { return a[0] - b[0] || a[1].t.localeCompare(b[1].t); });
                results.hidden = false;
                if (!hits.length) {
                    results.innerHTML = '<p class="search-empty">' + noneText + '</p>';
                    return;
                }
                results.innerHTML = hits.slice(0, 8).map(function (pair) {
                    var e = pair[1];
                    var cover = e.c ? '<img src="' + e.c + '" alt="">' : '';
                    var series = e.s ? '<span class="search-series">' + e.s + '</span>' : '';
                    return '<a class="search-hit" href="' + e.u + '">' + cover +
                        '<span class="search-hit-text"><span class="search-title">' + e.t + '</span>' +
                        series + '</span><span class="search-lang">' + e.l.toUpperCase() + '</span></a>';
                }).join('');
            };

            var openSearch = function () {
                searchBox.classList.add('open');
                panel.classList.add('open');
                toggle.setAttribute('aria-expanded', 'true');
                input.focus();
                loadIndex().then(function () { if (input.value) render(input.value); });
            };
            var closeSearch = function () {
                searchBox.classList.remove('open');
                panel.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
                results.hidden = true;
            };

            toggle.addEventListener('click', function () {
                if (searchBox.classList.contains('open')) closeSearch(); else openSearch();
            });
            input.addEventListener('input', function () {
                loadIndex().then(function () { render(input.value); });
            });
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') { closeSearch(); toggle.focus(); }
                if (e.key === 'Enter') {
                    e.preventDefault();
                    var first = results.querySelector('.search-hit');
                    if (first) window.location.href = first.getAttribute('href');
                }
            });
            document.addEventListener('click', function (e) {
                if (!searchBox.contains(e.target)) closeSearch();
            });
        }

        /* ── Cookie banner ─────────────────────────────────────────── */
        var banner = document.getElementById('cookie-banner');
        var acceptBtn = document.getElementById('cookie-accept-btn');
        if (banner && acceptBtn) {
            var stored = null;
            try { stored = localStorage.getItem('cookiesAccepted'); } catch (err) { stored = 'true'; }
            if (!stored) setTimeout(function () { banner.classList.add('show'); }, 1200);
            acceptBtn.addEventListener('click', function () {
                try { localStorage.setItem('cookiesAccepted', 'true'); } catch (err) { /* private mode */ }
                banner.classList.remove('show');
            });
        }

        /* ── Lead-magnet banners ───────────────────────────────────── */
        // Our own modal opens instantly (no provider trigger delay); Sender.net
        // is loaded on demand, only on click, and renders its embedded form
        // into the modal once ready.
        Array.prototype.forEach.call(document.querySelectorAll('.lead-magnet-cta'), function (btn) {
            btn.addEventListener('click', function () {
                var accountId = btn.dataset.accountId;
                var banner = btn.closest('.lead-magnet-banner');
                var modal = banner && banner.nextElementSibling;
                if (!accountId || !modal || !modal.classList.contains('lead-magnet-modal')) return;
                modal.classList.add('open');
                var holder = modal.querySelector('[data-sender-form-id]');
                var formId = holder && holder.dataset.senderFormId;
                if (window.senderForms) {
                    if (formId) window.senderForms.render(formId);
                    return;
                }
                (function (s, e, n, d, er) {
                    s['Sender'] = er;
                    s[er] = s[er] || function () { (s[er].q = s[er].q || []).push(arguments); };
                    s[er].l = 1 * new Date();
                    s[er].on = function (event, callback) {
                        s[er].listeners = s[er].listeners || {};
                        (s[er].listeners[event] = s[er].listeners[event] || []).push(callback);
                    };
                    var a = e.createElement(n);
                    var m = e.getElementsByTagName(n)[0];
                    a.async = 1;
                    a.src = d;
                    a.onload = function () { if (formId) window.senderForms.render(formId); };
                    m.parentNode.insertBefore(a, m);
                })(window, document, 'script', 'https://cdn.sender.net/accounts_resources/universal.js', 'sender');
                window.sender(accountId);
            });
        });

        Array.prototype.forEach.call(document.querySelectorAll('.lead-magnet-modal'), function (modal) {
            var close = modal.querySelector('.lead-magnet-modal-close');
            if (close) close.addEventListener('click', function () { modal.classList.remove('open'); });
            modal.addEventListener('click', function (e) {
                if (e.target === modal) modal.classList.remove('open');
            });
        });

        /* ── Contact form ──────────────────────────────────────────── */
        // Shares the same Google Form inbox as the author's other two sites —
        // the message body is tagged with the site of origin so replies can tell
        // them apart in one shared response sheet.
        var form = document.getElementById('contact-form');
        if (form) {
            form.addEventListener('submit', function (e) {
                e.preventDefault();
                var statusDiv = document.getElementById('form-status');
                var lang = document.documentElement.lang === 'bg' ? 'bg' : 'en';
                var sendingText = lang === 'bg' ? 'Изпращане…' : 'Sending…';
                var okText = lang === 'bg'
                    ? 'Благодаря! Съобщението беше изпратено.'
                    : 'Thank you! Your message has been sent.';
                var errText = lang === 'bg'
                    ? 'Възникна грешка. Моля, опитайте отново.'
                    : 'An error occurred. Please try again.';
                statusDiv.className = '';
                statusDiv.textContent = sendingText;

                var formData = new FormData(form);
                var name = formData.get('name');
                var email = formData.get('email');
                var message = '[K.Z.Pendrake website] ' + formData.get('message');
                var formUrl = 'https://docs.google.com/forms/d/e/1FAIpQLSd6oAve7uoiaXMJWWukyYHWEZQgGTJxPgCpV40E-f3mCNkQtw/formResponse'
                    + '?entry.1843393081=' + encodeURIComponent(name)
                    + '&entry.1799285576=' + encodeURIComponent(email)
                    + '&entry.530113389=' + encodeURIComponent(message);

                fetch(formUrl, { method: 'POST', mode: 'no-cors' })
                    .then(function () {
                        statusDiv.textContent = okText;
                        statusDiv.className = 'ok';
                        form.reset();
                    })
                    .catch(function () {
                        statusDiv.textContent = errText;
                        statusDiv.className = 'err';
                    });
            });
        }

        /* ── Hero orrery ───────────────────────────────────────────── */
        initOrrery();
    });


    /* ═══════════════════════════════════════════════════════════════
       The homepage hero: a brass orrery low on the frame, a field of
       stars above it, both drifting with the pointer and the scroll.
       Pure canvas — no video file, no library, a few kilobytes.
       ═══════════════════════════════════════════════════════════════ */
    function initOrrery() {
        var cv = document.getElementById('orrery');
        if (!cv) return;
        var cx = cv.getContext('2d');
        if (!cx) return;

        var W = 0, H = 0, DPR = 1;
        var stars = [], rings = [];
        var t = 0, mx = 0, my = 0, tx = 0, ty = 0, scrollK = 0;
        var running = true;

        function build() {
            DPR = Math.min(window.devicePixelRatio || 1, 2);
            W = cv.clientWidth; H = cv.clientHeight;
            if (!W || !H) return;
            cv.width = Math.round(W * DPR);
            cv.height = Math.round(H * DPR);
            cx.setTransform(DPR, 0, 0, DPR, 0, 0);

            var count = Math.min(Math.round(W * H / 3400), 520);
            stars = [];
            for (var i = 0; i < count; i++) {
                stars.push({
                    x: Math.random() * W,
                    y: Math.random() * H,
                    r: 0.3 + Math.random() * 1.25,
                    a: 0.2 + Math.random() * 0.6,
                    tw: Math.random() * 6.3,
                    ts: 0.005 + Math.random() * 0.014,
                    z: 0.3 + Math.random() * 0.7
                });
            }

            var R = Math.max(W * 0.42, Math.min(W, H) * 0.52);
            rings = [
                { r: R * 0.30, sp: 0.42, n: 1, sz: 3.4, c: '#e8cf84', ecc: 0.22 },
                { r: R * 0.48, sp: -0.27, n: 1, sz: 2.6, c: '#c9a227', ecc: 0.22 },
                { r: R * 0.70, sp: 0.17, n: 2, sz: 2.2, c: '#c86b7a', ecc: 0.22 },
                { r: R * 0.95, sp: -0.11, n: 1, sz: 3.0, c: '#9aa6c4', ecc: 0.22 }
            ];
        }

        function paintBackground() {
            var bg = cx.createRadialGradient(W * 0.5, H * 0.80, 0, W * 0.5, H * 0.80, Math.max(W, H) * 0.95);
            bg.addColorStop(0, '#101d42');
            bg.addColorStop(0.5, '#0a1430');
            bg.addColorStop(1, '#050c1f');
            cx.fillStyle = bg;
            cx.fillRect(0, 0, W, H);
        }

        function paintStars(animated) {
            for (var i = 0; i < stars.length; i++) {
                var s = stars[i];
                var a = s.a;
                var x = s.x, y = s.y;
                if (animated) {
                    s.tw += s.ts;
                    a = s.a * (0.5 + 0.5 * Math.sin(s.tw));
                    x = s.x + tx * 22 * s.z;
                    y = s.y + ty * 22 * s.z - scrollK * 170 * s.z;
                    y = ((y % H) + H) % H;
                }
                cx.fillStyle = 'rgba(240,233,216,' + a + ')';
                cx.beginPath();
                cx.arc(x, y, s.r, 0, 7);
                cx.fill();
            }
        }

        function paintOrrery(ox, oy) {
            cx.save();
            cx.translate(ox, oy);

            // brass rays
            var RR = Math.min(W, H) * 0.72;
            for (var i = 0; i < 48; i++) {
                var a = i * (Math.PI * 2 / 48) + t * 0.02;
                var len = RR * (0.55 + 0.45 * Math.abs(Math.sin(i * 1.7 + t * 0.5)));
                cx.strokeStyle = 'rgba(201,162,39,' + (i % 4 ? 0.045 : 0.11) + ')';
                cx.lineWidth = i % 4 ? 1 : 1.4;
                cx.beginPath();
                cx.moveTo(Math.cos(a) * RR * 0.14, Math.sin(a) * RR * 0.14 * 0.30);
                cx.lineTo(Math.cos(a) * len, Math.sin(a) * len * 0.30);
                cx.stroke();
            }

            // orbits and bodies
            for (var j = 0; j < rings.length; j++) {
                var r = rings[j];
                cx.strokeStyle = 'rgba(201,162,39,.22)';
                cx.lineWidth = 1;
                cx.beginPath();
                cx.ellipse(0, 0, r.r, r.r * r.ecc, 0, 0, 7);
                cx.stroke();
                for (var k = 0; k < r.n; k++) {
                    var ang = t * r.sp + k * (Math.PI * 2 / r.n);
                    var px = Math.cos(ang) * r.r;
                    var py = Math.sin(ang) * r.r * r.ecc;
                    cx.fillStyle = r.c;
                    cx.beginPath(); cx.arc(px, py, r.sz, 0, 7); cx.fill();
                    cx.globalAlpha = 0.20;
                    cx.beginPath(); cx.arc(px, py, r.sz * 5, 0, 7); cx.fill();
                    cx.globalAlpha = 1;
                }
            }

            // the sun at the centre of the machine
            var halo = Math.min(W, H) * 0.20;
            var sg = cx.createRadialGradient(0, 0, 0, 0, 0, halo);
            sg.addColorStop(0, 'rgba(232,207,132,.42)');
            sg.addColorStop(0.35, 'rgba(201,162,39,.16)');
            sg.addColorStop(1, 'rgba(201,162,39,0)');
            cx.fillStyle = sg;
            cx.beginPath(); cx.arc(0, 0, halo, 0, 7); cx.fill();

            var core = Math.min(W, H) * 0.045;
            var cg = cx.createRadialGradient(0, 0, 0, 0, 0, core);
            cg.addColorStop(0, 'rgba(255,244,214,.92)');
            cg.addColorStop(0.55, 'rgba(232,207,132,.42)');
            cg.addColorStop(1, 'rgba(201,162,39,0)');
            cx.fillStyle = cg;
            cx.beginPath(); cx.arc(0, 0, core, 0, 7); cx.fill();
            cx.strokeStyle = 'rgba(232,207,132,.55)';
            cx.lineWidth = 1;
            cx.beginPath(); cx.arc(0, 0, core, 0, 7); cx.stroke();

            cx.restore();
        }

        function paintCorners() {
            var m = 34, L = 56;
            cx.strokeStyle = 'rgba(201,162,39,.30)';
            cx.lineWidth = 1;
            var pts = [[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]];
            for (var i = 0; i < pts.length; i++) {
                var x = pts[i][0], y = pts[i][1], sx = pts[i][2], sy = pts[i][3];
                cx.beginPath();
                cx.moveTo(x + sx * L, y); cx.lineTo(x, y); cx.lineTo(x, y + sy * L);
                cx.stroke();
                cx.beginPath();
                cx.moveTo(x + sx * (L * 0.55), y + sy * 10);
                cx.lineTo(x + sx * 10, y + sy * 10);
                cx.lineTo(x + sx * 10, y + sy * (L * 0.55));
                cx.stroke();
            }
        }

        function frame() {
            if (!running) return;
            t += 0.006;
            tx += (mx - tx) * 0.04;
            ty += (my - ty) * 0.04;
            cx.clearRect(0, 0, W, H);
            paintBackground();
            paintStars(true);
            paintOrrery(W * 0.5 + tx * 26, H * 0.80 + ty * 18 - scrollK * 110);
            paintCorners();
            requestAnimationFrame(frame);
        }

        function paintStill() {
            cx.clearRect(0, 0, W, H);
            paintBackground();
            paintStars(false);
            paintOrrery(W * 0.5, H * 0.80);
            paintCorners();
        }

        window.addEventListener('resize', function () {
            build();
            if (reduceMotion) paintStill();
        });
        window.addEventListener('pointermove', function (e) {
            mx = (e.clientX / window.innerWidth - 0.5) * 2;
            my = (e.clientY / window.innerHeight - 0.5) * 2;
        }, { passive: true });
        window.addEventListener('scroll', function () {
            scrollK = Math.min(window.scrollY / window.innerHeight, 1);
            // Once the hero is off screen there is nothing to animate.
            var wasRunning = running;
            running = !reduceMotion && window.scrollY < window.innerHeight * 1.2;
            if (running && !wasRunning) requestAnimationFrame(frame);
        }, { passive: true });

        build();
        if (reduceMotion) { running = false; paintStill(); } else { frame(); }
    }
})();
