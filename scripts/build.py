#!/usr/bin/env python3
"""
Static site generator for the K.Z. Pendrake author site.
Reads data.js / synopsis / books / news from this directory and writes a
fully pre-rendered, hash-free static site into dist/.

Usage:  python scripts/build.py
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import render as R
import markdown_lite as MD

BASE = Path(__file__).resolve().parent.parent  # kzpendrake/
DIST = BASE / 'dist'
UI_LANGS = ['en', 'bg']


# ─────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────

def load_author_data():
    text = (BASE / 'data.js').read_text(encoding='utf-8')
    m = re.search(r'const\s+authorData\s*=\s*(\{.*\})\s*;?\s*$', text, re.DOTALL)
    if not m:
        raise ValueError('Cannot locate authorData object in data.js')
    obj = m.group(1)
    try:
        return json.loads(obj)
    except json.JSONDecodeError:
        pass

    # Tolerant fallback for hand-edited JS (unquoted keys, comments, trailing commas).
    strings = []

    def save_template(match):
        content = match.group(1)
        content = content.replace('\\', '\\\\').replace('"', '\\"')
        content = content.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '').replace('\t', '\\t')
        strings.append(f'"{content}"')
        return f'\x02{len(strings) - 1}\x02'

    obj = re.sub(r'`([^`]*)`', save_template, obj, flags=re.DOTALL)

    def save_str(match):
        strings.append(match.group(0))
        return f'\x02{len(strings) - 1}\x02'

    obj = re.sub(r'"(?:[^"\\]|\\.)*"', save_str, obj)
    obj = re.sub(r'//[^\n]*', '', obj)
    obj = re.sub(r'(?<!["\w\x02])([a-zA-Z_$][a-zA-Z0-9_$]*)(\s*):', r'"\1"\2:', obj)
    obj = re.sub(r',(\s*[}\]])', r'\1', obj)
    for i, s_val in enumerate(strings):
        obj = obj.replace(f'\x02{i}\x02', s_val)
    return json.loads(obj)


def clip(text, limit=160):
    """A meta description cut mid-word reads like a glitch in the search result.
    Cut at the last whole word instead, and say so with an ellipsis."""
    text = ' '.join(str(text or '').split())
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    space = cut.rfind(' ')
    if space > limit * 0.6:
        cut = cut[:space]
    return cut.rstrip(' ,;:.\u2014-') + '\u2026'


def strip_tags(html_str):
    """Meta descriptions are plain text. The author intro carries a link."""
    return ' '.join(re.sub(r'<[^>]+>', '', html_str or '').split())


def read_text(relpath):
    p = BASE / relpath
    return p.read_text(encoding='utf-8') if p.exists() else ''


EN_MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
             'August', 'September', 'October', 'November', 'December']
BG_MONTHS = ['януари', 'февруари', 'март', 'април', 'май', 'юни', 'юли',
             'август', 'септември', 'октомври', 'ноември', 'декември']


def format_date(date_str, ui_lang):
    try:
        y, mo, d = date_str[:10].split('-')
        months = BG_MONTHS if ui_lang == 'bg' else EN_MONTHS
        month = months[int(mo) - 1]
        return f'{int(d)} {month} {y}' if ui_lang == 'bg' else f'{month} {int(d)}, {y}'
    except Exception:
        return date_str


def slugify(stem):
    slug = re.sub(r'[^a-z0-9]+', '-', stem.lower()).strip('-')
    return slug or 'article'


def load_news():
    """Returns {ui_lang: [ {slug, title, author, date_raw, date_fmt, content_html, excerpt}, ... newest first ]}"""
    index_path = BASE / 'news' / 'index.json'
    filenames = json.loads(index_path.read_text(encoding='utf-8')) if index_path.exists() else []
    result = {lang: [] for lang in UI_LANGS}
    for fname in filenames:
        stem = fname[:-3] if fname.endswith('.md') else fname
        slug = slugify(stem)
        date_raw = fname[:10]
        for lang in UI_LANGS:
            p = BASE / 'news' / lang / fname
            if not p.exists():
                continue
            metadata, content = MD.parse_frontmatter(p.read_text(encoding='utf-8'))
            words = content.split()
            excerpt = ' '.join(words[:30]) + ('...' if len(words) > 30 else '')
            result[lang].append({
                'slug': slug,
                'title': metadata.get('title') or stem,
                'author': metadata.get('author') or 'K.Z. Pendrake',
                'date_raw': date_raw,
                'date_fmt': format_date(date_raw, lang),
                'content_html': MD.to_html(content),
                'excerpt': excerpt,
            })
    for lang in UI_LANGS:
        result[lang].reverse()  # newest first, matching original site behaviour
    return result


# ─────────────────────────────────────────────────────────────────────────
# OUTPUT HELPERS
# ─────────────────────────────────────────────────────────────────────────

SITEMAP = []


def write_page(path, html_str, priority=0.5, lastmod=None, hreflangs=None):
    rel = path.strip('/')
    target_dir = (DIST / rel) if rel else DIST
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / 'index.html').write_text(html_str, encoding='utf-8')
    SITEMAP.append((R.BASE_URL + path, priority, lastmod, hreflangs))


def _git_file_dates():
    """Last commit date for every tracked file, from a single pass over the
    history. File timestamps cannot be used: a fresh clone - which is what the
    GitHub Actions build works from - stamps every file with the time of the
    checkout, so mtimes would report the whole site as changed on every deploy.
    Returns {} when git is unavailable or there is no history yet, and then
    pages simply carry no lastmod, which is the honest answer."""
    try:
        out = subprocess.run(['git', 'log', '--name-only', '--format=%cs'],
                             cwd=BASE, capture_output=True, text=True, timeout=120)
    except Exception:
        return {}
    if out.returncode != 0:
        return {}
    dates, current = {}, None
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', line):
            current = line
        elif current:
            dates.setdefault(line, current)  # git log is newest first
    return dates


GIT_DATES = {}


def source_date(*relpaths):
    """Date a page's source last changed, as YYYY-MM-DD, taken from the commit
    that touched it. A made-up lastmod is worse than none: Google stops trusting
    the whole sitemap once it catches one."""
    stamps = [GIT_DATES[rel.replace('\\', '/')] for rel in relpaths
              if rel and rel.replace('\\', '/') in GIT_DATES]
    return max(stamps) if stamps else None


def iter_all_books(data):
    for s in data.get('series', []):
        for b in s.get('books', []):
            yield b
    for b in data.get('novels', []):
        yield b
    for b in data.get('short_stories', []):
        yield b


def search_index(data):
    """Flat list of every book in every language it exists in — one entry per
    edition, so a German title leads to the German page. Read by assets/site.js."""
    entries = []

    def add(book, series_titles=None):
        for lang, d in sorted(book.get('i18n', {}).items()):
            if not d.get('title'):
                continue
            e = {'t': d['title'], 'l': lang, 'u': R.book_path(book['id'], lang)}
            if d.get('genre'):
                e['g'] = d['genre']
            if d.get('cover'):
                e['c'] = '/' + d['cover'].lstrip('/')
            if series_titles:
                st = series_titles.get(lang) or series_titles.get('en')
                if st:
                    e['s'] = st
            entries.append(e)

    for s in data.get('series', []):
        titles = {l: v.get('title') for l, v in s.get('i18n', {}).items() if v.get('title')}
        for b in s.get('books', []):
            add(b, titles)
    for b in data.get('novels', []):
        add(b)
    for b in data.get('short_stories', []):
        add(b)
    return entries


def teaser_from(relpath, limit=190):
    """First sentences of the synopsis, cut at a word boundary."""
    text = ' '.join(read_text(relpath).split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    return cut[:cut.rfind(' ')].rstrip(' ,;:—-') + '…'


def store_entries(data):
    """Every edition the author sells directly, in ALL_LANGS order then by title."""
    entries = []

    def add(book, series_titles=None):
        for lang, d in book.get('i18n', {}).items():
            url = (d.get('creem_checkout_url') or '').strip()
            price = str(d.get('price') or '').strip()
            if not d.get('direct_sale_active') or not url or not price:
                continue
            entries.append({
                'id': book['id'],
                'lang': lang,
                'title': d.get('title', ''),
                'cover': d.get('cover'),
                'genre': d.get('genre'),
                'series': (series_titles or {}).get(lang) or (series_titles or {}).get('en'),
                'price': price,
                'url': url,
                'teaser': teaser_from(d['synopsis']) if d.get('synopsis') else '',
                'has_excerpt': bool(d.get('excerpt')),
            })

    for s in data.get('series', []):
        titles = {l: v.get('title') for l, v in s.get('i18n', {}).items() if v.get('title')}
        for b in s.get('books', []):
            add(b, titles)
    for b in data.get('novels', []):
        add(b)
    for b in data.get('short_stories', []):
        add(b)
    entries.sort(key=lambda e: (R.ALL_LANGS.index(e['lang']) if e['lang'] in R.ALL_LANGS else 99,
                                e.get('series') or '', e['title']))
    return entries


def same_route_switch(path_fn, *args):
    return {'en': path_fn('en', *args), 'bg': path_fn('bg', *args)}


def book_lang_switch(book, id_):
    i18n = book['i18n']
    return {
        'en': R.book_path(id_, 'en') if 'en' in i18n else R.home_path('en'),
        'bg': R.book_path(id_, 'bg') if 'bg' in i18n else R.home_path('bg'),
    }


# ─────────────────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────────────────

def _clean_dist():
    import time
    if not DIST.exists():
        return
    for attempt in range(5):
        try:
            shutil.rmtree(DIST)
            return
        except PermissionError:
            time.sleep(0.3 * (attempt + 1))
    # Last resort: remove what we can, ignore stubborn locked files (e.g. AV scanner).
    shutil.rmtree(DIST, ignore_errors=True)


# Crawlers that fetch a page to answer someone's question right now, and cite
# the source back to them. These are the ones that send readers here.
AI_SEARCH_AGENTS = [
    'OAI-SearchBot',        # OpenAI - the index behind ChatGPT search
    'ChatGPT-User',         # OpenAI - fetched because a user asked for this page
    'Claude-SearchBot',     # Anthropic - search index
    'Claude-User',          # Anthropic - fetched on a user's request
    'PerplexityBot',        # Perplexity - index
    'Perplexity-User',      # Perplexity - fetched on a user's request
    'DuckAssistBot',        # DuckDuckGo
    'MistralAI-User',       # Mistral
    'YouBot',               # You.com
    'Meta-ExternalFetcher', # Meta - fetched on a user's request
]

# Crawlers that collect text for training. K.Z. Pendrake allows these; to change
# that, move a name out of this list and give it Disallow: / instead.
AI_TRAINING_AGENTS = [
    'GPTBot',               # OpenAI
    'ClaudeBot',            # Anthropic
    'Google-Extended',      # Google - Gemini and Vertex AI
    'Applebot-Extended',    # Apple Intelligence
    'meta-externalagent',   # Meta
    'CCBot',                # Common Crawl, which most others are built from
    'Amazonbot',            # Amazon
    'Bytespider',           # ByteDance
    'cohere-ai',            # Cohere
]

# Ordinary search engines. Gemini's answers lean on Google's index, so
# Googlebot matters for AI answers as much as Google-Extended does.
SEARCH_AGENTS = ['Googlebot', 'Googlebot-Image', 'bingbot', 'Applebot', 'DuckDuckBot']


def robots_txt():
    """Every crawler answered by name. A wildcard Allow says the same thing, but
    naming them makes the policy readable and makes changing one a one-line edit."""
    out = ['# robots.txt - kzpendrake.com',
           '# Everything on this site is open to every crawler listed below.',
           '',
           'User-agent: *',
           'Allow: /',
           '']
    for heading, agents in (
        ('AI assistants that answer questions and cite the page', AI_SEARCH_AGENTS),
        ('AI crawlers that collect text for training', AI_TRAINING_AGENTS),
        ('Search engines', SEARCH_AGENTS),
    ):
        out.append(f'# {heading}')
        for agent in agents:
            out.append(f'User-agent: {agent}')
            out.append('Allow: /')
        out.append('')
    out.append(f'Sitemap: {R.BASE_URL}/sitemap.xml')
    out.append('')
    return '\n'.join(out)


def build():
    _clean_dist()
    DIST.mkdir(parents=True, exist_ok=True)

    data = load_author_data()
    news = load_news()

    # Stamp style.css / site.js with a content hash, so a returning reader
    # is never left running a cached copy from before the last change.
    for kind, path in (('css', BASE / 'style.css'), ('js', BASE / 'assets' / 'site.js')):
        R.ASSET_V[kind] = hashlib.md5(path.read_bytes()).hexdigest()[:8]

    GIT_DATES.update(_git_file_dates())

    shop = store_entries(data)
    R.STORE_ACTIVE = bool(shop)

    # ---- site-language pages (en / bg) ----
    for ui in UI_LANGS:
        latest_news_html = ''
        if news[ui]:
            latest = news[ui][0]
            latest_news_html = R.render_news_excerpt_block(ui, latest['title'], latest['excerpt'], latest['slug'])
        body = R.render_homepage(data, ui, latest_news_html, R.render_store_band(shop, ui))
        write_page(R.home_path(ui), R.layout(
            data, lang=ui, path=R.home_path(ui),
            title=R.site_title(data, ui),
            description=clip(strip_tags(data['meta'][ui]['intro'])),
            body_html=body, active_nav_base='/', body_class='home',
            jsonld=[R.jsonld_website(data, ui), R.jsonld_person(data, ui)],
            nav_lang_switch=same_route_switch(lambda l: R.home_path(l)),
        ), 1.0)

        body = R.render_library_hub(data, ui)
        write_page(R.library_path(ui), R.layout(
            data, lang=ui, path=R.library_path(ui),
            title=f"{R.UI_STRINGS[ui]['the_library']} | {R.author_name(data, ui)}",
            description=R.UI_STRINGS[ui]['desc_library'],
            body_html=body, active_nav_base='library/',
            nav_lang_switch=same_route_switch(lambda l: R.library_path(l)),
        ), 0.9)

        for kind, sub in (('novels', 'novels'), ('short_stories', 'stories')):
            body = R.render_book_list_page(data, ui, kind)
            write_page(R.library_path(ui, sub), R.layout(
                data, lang=ui, path=R.library_path(ui, sub),
                title=f"{R.UI_STRINGS[ui]['standalone_novels'] if sub == 'novels' else R.UI_STRINGS[ui]['short_stories']} | {R.author_name(data, ui)}",
                description=R.UI_STRINGS[ui]['desc_novels' if sub == 'novels' else 'desc_stories'],
                body_html=body, active_nav_base='library/',
                nav_lang_switch=same_route_switch(lambda l, s=sub: R.library_path(l, s)),
            ), 0.6)

        for series in data.get('series', []):
            sd = series['i18n'].get(ui) or series['i18n'].get('en') or {}
            body = R.render_series_page(data, series, ui)
            write_page(R.series_path(series['id'], ui), R.layout(
                data, lang=ui, path=R.series_path(series['id'], ui),
                title=f"{sd.get('title', series['id'])} | {R.author_name(data, ui)}",
                description=clip(sd.get('series_synopsis')) or R.UI_STRINGS[ui]['desc_library'],
                body_html=body,
                nav_lang_switch=same_route_switch(lambda l, sid=series['id']: R.series_path(sid, l)),
            ), 0.7)

        about_photo = data['meta'].get('photo') or 'images/common/author-placeholder.jpg'
        bio_txt = read_text(f'synopsis/{ui}/about.txt')
        bio_html = MD.bio_html(bio_txt)
        body = R.render_about_page(data, ui, bio_html, about_photo)
        write_page(R.about_path(ui), R.layout(
            data, lang=ui, path=R.about_path(ui),
            title=f"{R.UI_STRINGS[ui]['about_the_author']} | {R.author_name(data, ui)}",
            description=clip(bio_txt) or R.UI_STRINGS[ui]['desc_about'],
            body_html=body, active_nav_base='about/', og_type='profile',
            jsonld=R.jsonld_person(data, ui, bio_txt),
            nav_lang_switch=same_route_switch(lambda l: R.about_path(l)),
        ), 0.8)

        body = R.render_contact_page(ui)
        write_page(R.contact_path(ui), R.layout(
            data, lang=ui, path=R.contact_path(ui),
            title=f"{R.UI_STRINGS[ui]['get_in_touch']} | {R.author_name(data, ui)}",
            description=R.UI_STRINGS[ui]['contact_intro'],
            body_html=body, active_nav_base='contact/',
            nav_lang_switch=same_route_switch(lambda l: R.contact_path(l)),
        ), 0.7)

        body = R.render_news_list_page(ui, news[ui])
        write_page(R.news_path(ui), R.layout(
            data, lang=ui, path=R.news_path(ui),
            title=f"{R.UI_STRINGS[ui]['news_and_updates']} | {R.author_name(data, ui)}",
            description=R.UI_STRINGS[ui]['desc_news'],
            body_html=body, active_nav_base='news/',
            nav_lang_switch=same_route_switch(lambda l: R.news_path(l)),
        ), 0.8)

        for article in news[ui]:
            other_lang_has_it = any(a['slug'] == article['slug'] for a in news['bg' if ui == 'en' else 'en'])
            switch = {
                'en': R.news_article_path(article['slug'], 'en') if (ui == 'en' or other_lang_has_it) else R.news_path('en'),
                'bg': R.news_article_path(article['slug'], 'bg') if (ui == 'bg' or other_lang_has_it) else R.news_path('bg'),
            }
            body = R.render_news_article_page(ui, article, article['content_html'])
            write_page(R.news_article_path(article['slug'], ui), R.layout(
                data, lang=ui, path=R.news_article_path(article['slug'], ui),
                title=f"{article['title']} | {R.author_name(data, ui)}",
                description=clip(article['excerpt']),
                body_html=body, active_nav_base='news/', og_type='article',
                jsonld=R.jsonld_article(data, ui, article),
                nav_lang_switch=switch,
            ), 0.5, lastmod=article.get('date_raw') or None)

        title, priv_body = MD.privacy_html(read_text(f'synopsis/{ui}/privacy-policy.txt'))
        body = R.render_privacy_page(ui, title or R.UI_STRINGS[ui]['privacy_policy'], priv_body)
        write_page(R.privacy_path(ui), R.layout(
            data, lang=ui, path=R.privacy_path(ui),
            title=f"{R.UI_STRINGS[ui]['privacy_policy']} | {R.author_name(data, ui)}",
            description=R.UI_STRINGS[ui]['desc_privacy'],
            body_html=body,
            nav_lang_switch=same_route_switch(lambda l: R.privacy_path(l)),
        ), 0.3)

        if shop:
            write_page(R.store_path(ui), R.layout(
                data, lang=ui, path=R.store_path(ui),
                title=f"{R.UI_STRINGS[ui]['store']} | {R.author_name(data, ui)}",
                description=clip(R.UI_STRINGS[ui]['store_intro']),
                body_html=R.render_store_page(shop, ui), active_nav_base='store/',
                nav_lang_switch=same_route_switch(lambda l: R.store_path(l)),
            ), 0.8)

        title, terms_body = MD.privacy_html(read_text(f'synopsis/{ui}/terms-of-service.txt'))
        body = R.render_terms_page(ui, title or R.UI_STRINGS[ui]['terms_of_service'], terms_body)
        write_page(R.terms_path(ui), R.layout(
            data, lang=ui, path=R.terms_path(ui),
            title=f"{R.UI_STRINGS[ui]['terms_of_service']} | {R.author_name(data, ui)}",
            description=R.UI_STRINGS[ui]['desc_terms'],
            body_html=body,
            nav_lang_switch=same_route_switch(lambda l: R.terms_path(l)),
        ), 0.3)

    # ---- content-language pages (book / excerpt) ----
    series_of = {}
    for s in data.get('series', []):
        for b in s.get('books', []):
            series_of[b['id']] = s

    for book in iter_all_books(data):
        bid = book['id']
        i18n = book['i18n']
        langs_here = sorted(i18n.keys())
        hreflangs = [(l, R.BASE_URL + R.book_path(bid, l)) for l in langs_here]
        switch = book_lang_switch(book, bid)

        for lang in langs_here:
            bdata = i18n[lang]
            synopsis_txt = read_text(bdata['synopsis']) if bdata.get('synopsis') else ''
            synopsis_html = MD.synopsis_html(synopsis_txt)
            series = series_of.get(bid)
            body = R.render_book_detail(data, book, lang, synopsis_html, series)
            write_page(R.book_path(bid, lang), R.layout(
                data, lang=lang, path=R.book_path(bid, lang),
                title=f"{bdata['title']} | {R.author_name(data, lang)}",
                description=clip(synopsis_txt) or bdata['title'],
                og_image=bdata.get('cover') or 'images/common/cover-placeholder.jpg',
                body_html=body, hreflangs=hreflangs, nav_lang_switch=switch,
                og_type='book',
                jsonld=[R.jsonld_book(data, book, lang, synopsis_txt, series),
                        R.book_breadcrumbs(data, book, lang, series)],
            ), 0.6, lastmod=source_date(bdata.get('synopsis')), hreflangs=hreflangs)

            if bdata.get('excerpt'):
                excerpt_txt = read_text(bdata['excerpt'])
                excerpt_html = MD.to_html(excerpt_txt)
                body = R.render_excerpt_page(book, lang, excerpt_html)
                s_ui = R.UI_STRINGS[R.ui_lang_of(lang)]
                excerpt_desc = f"{s_ui['excerpt_from']} „{bdata['title']}“. " + \
                               ' '.join(synopsis_txt.split())
                write_page(R.excerpt_path(bid, lang), R.layout(
                    data, lang=lang, path=R.excerpt_path(bid, lang),
                    title=f"{s_ui['excerpt_from']} {bdata['title']} | {R.author_name(data, lang)}",
                    description=clip(excerpt_desc),
                    og_image=bdata.get('cover') or 'images/common/cover-placeholder.jpg',
                    body_html=body, hreflangs=hreflangs, nav_lang_switch=switch,
                    jsonld=R.book_breadcrumbs(data, book, lang, series,
                                              leaf=s_ui['read_excerpt_short']),
                ), 0.5, lastmod=source_date(bdata.get('excerpt')))

    # ---- static assets ----
    for name in ('images', 'style.css'):
        src = BASE / name
        if src.is_dir():
            shutil.copytree(src, DIST / name, dirs_exist_ok=True)
        elif src.exists():
            shutil.copy2(src, DIST / name)

    (DIST / 'assets').mkdir(exist_ok=True)
    shutil.copy2(BASE / 'assets' / 'site.js', DIST / 'assets' / 'site.js')

    (DIST / 'search-index.json').write_text(
        json.dumps(search_index(data), ensure_ascii=False, separators=(',', ':')),
        encoding='utf-8')

    (DIST / 'CNAME').write_text('kzpendrake.com\n', encoding='utf-8')
    (DIST / '404.html').write_text(R.layout(
        data, lang='en', path='/',
        title=f"404 | {R.author_name(data, 'en')}",
        description='Page not found',
        body_html=R.render_404_page('en'),
        nav_lang_switch=same_route_switch(lambda l: R.home_path(l)),
    ), encoding='utf-8')

    (DIST / 'robots.txt').write_text(
        robots_txt(), encoding='utf-8'
    )

    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                   '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
                   ' xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for url, priority, lastmod, hreflangs in SITEMAP:
        row = [f'    <url><loc>{url}</loc>']
        if lastmod:
            row.append(f'<lastmod>{lastmod}</lastmod>')
        row.append(f'<priority>{priority}</priority>')
        if hreflangs:
            for code, alt in hreflangs:
                row.append(f'<xhtml:link rel="alternate" hreflang="{R.bcp47(code)}" href="{alt}"/>')
            default = dict(hreflangs).get('en') or hreflangs[0][1]
            row.append(f'<xhtml:link rel="alternate" hreflang="x-default" href="{default}"/>')
        row.append('</url>')
        sitemap_xml.append(''.join(row))
    sitemap_xml.append('</urlset>')
    (DIST / 'sitemap.xml').write_text('\n'.join(sitemap_xml), encoding='utf-8')

    print(f'Built {len(SITEMAP)} pages into {DIST}')


if __name__ == '__main__':
    build()
