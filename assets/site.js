// K.Z. Pendrake: client-side behaviour for the static site.
// No router: every page is pre-rendered HTML with real URLs.

(function () {
    'use strict';

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    document.addEventListener('DOMContentLoaded', function () {

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
            var pending = Array.prototype.slice.call(revealables);
            var reveal = function (el) {
                el.classList.add('in');
                io.unobserve(el);
            };
            var io = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    // Above the viewport counts too: a restored scroll position
                    // or a fast flick jumps past blocks without ever showing them.
                    var above = entry.boundingClientRect.bottom < 0;
                    if (!entry.isIntersecting && !above) return;
                    var i = pending.indexOf(entry.target);
                    if (i === -1) return;
                    // Everything earlier in the page is above this block, so it
                    // has been scrolled past as well.
                    pending.splice(0, i + 1).forEach(reveal);
                });
            // threshold 0: an excerpt page is one very tall block, and a
            // fraction-of-the-element threshold would never be reached.
            }, { threshold: 0, rootMargin: '0px 0px -8% 0px' });
            pending.forEach(function (el) { io.observe(el); });
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
                if (e.key === 'Enter') {
                    e.preventDefault();
                    var first = results.querySelector('.search-hit');
                    if (first) window.location.href = first.getAttribute('href');
                }
            });
            document.addEventListener('click', function (e) {
                if (!searchBox.contains(e.target)) closeSearch();
            });
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && searchBox.classList.contains('open')) {
                    closeSearch();
                    toggle.focus();
                }
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
        // Each modal moves to <body> first: inside a block that is still sliding
        // in, position:fixed would anchor to that block instead of the window.
        Array.prototype.forEach.call(document.querySelectorAll('.lead-magnet-cta'), function (btn) {
            var banner = btn.closest('.lead-magnet-banner');
            var modal = banner && banner.nextElementSibling;
            if (!modal || !modal.classList.contains('lead-magnet-modal')) return;
            document.body.appendChild(modal);
            btn.addEventListener('click', function () {
                var accountId = btn.dataset.accountId;
                if (!accountId) return;
                modal.classList.add('open');
                var closeBtn = modal.querySelector('.lead-magnet-modal-close');
                if (closeBtn) closeBtn.focus();
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
        document.addEventListener('keydown', function (e) {
            if (e.key !== 'Escape') return;
            Array.prototype.forEach.call(document.querySelectorAll('.lead-magnet-modal.open'), function (m) {
                m.classList.remove('open');
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

    });

})();
