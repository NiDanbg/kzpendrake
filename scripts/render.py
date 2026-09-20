"""
Pure, dependency-free HTML template functions for the K.Z. Pendrake SSG build.
No DOM, no fetch — every function takes plain data and returns an HTML string.
"""
import html as _html
import json as _json
import datetime as _dt
import re as _re

BASE_URL = "https://kzpendrake.com"
GA_ID = ''  # GA4 measurement id; empty disables the tag
SENDER_ACCOUNT_ID = "ed72b4b7a59839"
SUPPORT_EMAIL = "contact@kzpendrake.com"

# Short content hashes for style.css / assets/site.js, filled in by build.py.
# They ride along as ?v=… so a returning reader never runs a stale script.
ASSET_V = {'css': '', 'js': ''}


def asset_v(kind):
    return ('?v=' + ASSET_V[kind]) if ASSET_V.get(kind) else ''

ALL_LANGS = ['bg', 'en', 'de', 'fr', 'it', 'nl', 'es', 'pt', 'se']

# The site calls Swedish "se" in its folders, but "se" is Northern Sami to a
# search engine. Everything a crawler reads - <html lang>, hreflang, og:locale -
# goes out as the real code; the folder names stay as they are.
BCP47 = {'se': 'sv'}

OG_LOCALES = {'bg': 'bg_BG', 'en': 'en_US', 'de': 'de_DE', 'fr': 'fr_FR', 'it': 'it_IT',
              'nl': 'nl_NL', 'es': 'es_ES', 'pt': 'pt_PT', 'se': 'sv_SE'}


def bcp47(lang):
    return BCP47.get(lang, lang)

UI_LANGS = ['en', 'bg']

NAV_LABELS = {
    'en': [('/', 'Home'), ('library/', 'The Library'), ('store/', 'Bookshop'), ('news/', 'News'),
           ('about/', 'About'), ('contact/', 'Contact')],
    'bg': [('/', 'Начало'), ('library/', 'Библиотека'), ('store/', 'Книжарница'), ('news/', 'Новини'),
           ('about/', 'За автора'), ('contact/', 'Контакти')],
}

UI_STRINGS = {
    'en': {
        'synopsis_not_available': 'Synopsis not available.',
        'available_on': 'Available on',
        'no_links_lang': 'Links for this language are not available yet.',
        'synopsis': 'Synopsis',
        'read_excerpt': 'Read Excerpt',
        'latest_works': 'Latest Works',
        'welcome': 'Welcome to my worlds',
        'explore_library': 'Explore the Full Library',
        'latest_news': 'Latest News',
        'read_all_news': 'Read all news',
        'the_library': 'The Library',
        'explore_series': 'Explore the Series',
        'other_works': 'Other Works',
        'standalone_novels': 'Standalone Novels',
        'short_stories': 'Short Stories',
        'books_in_series': 'Books in this series',
        'in_progress': 'In Progress',
        'news_and_updates': 'News and Updates',
        'no_news': 'No news yet. Stay tuned!',
        'about_the_author': 'About the Author',
        'get_in_touch': 'Get in Touch',
        'contact_intro': 'For business inquiries, media requests, or just to say hello, please use the form below.',
        'name': 'Name', 'email': 'Email', 'message': 'Message', 'send_message': 'Send Message',
        'back': 'Back', 'excerpt_from': 'Excerpt from',
        'not_found': 'Page not found',
        'privacy_policy': 'Privacy Policy',
        'terms_of_service': 'Terms of Service',
        'customer_support': 'Customer support',
        'search': 'Search',
        'store': 'Bookshop',
        'store_intro': 'These editions come straight from the author, without a middleman. The download link arrives the moment the payment goes through.',
        'store_note': 'Payment and invoicing are handled by Creem, the Merchant of Record for these orders. Books are delivered as EPUB files. The details are in the {terms}.',
        'store_heading': 'Buy direct from the author',
        'store_cta': 'Visit the bookshop',
        'editions_in': 'Editions in',
        'read_excerpt_short': 'Read excerpt',
        'search_placeholder': 'Search for a book…',
        'search_none': 'Nothing found',
        'by': 'by',
        'cookie_text': 'We use cookies to enhance your experience and for analytics. By continuing to browse, you agree to our <a href="/privacy-policy/">Privacy Policy</a>.',
        'cookie_accept': 'Accept',
        'get_gift': 'Get it free',
        'desc_library': 'Every novel and short story by K.Z. Pendrake, with the series they belong to and the languages each one is published in.',
        'desc_novels': 'The standalone novels of K.Z. Pendrake - comic fantasy and science fiction outside the Quibbletown books.',
        'desc_stories': 'Short stories by K.Z. Pendrake, set in the worlds the novels open up.',
        'desc_news': 'Releases, translations and what K.Z. Pendrake is working on next.',
        'desc_about': 'K.Z. Pendrake writes comic fantasy and science fiction. Who is behind the pen name and how the books came about.',
        'desc_privacy': 'What this site collects, why, and how to have it removed.',
        'desc_terms': 'Copyright, third-party retailers and what you may do with the books.',
        'skip_to_content': 'Skip to content',
        'main_menu': 'Main menu',
        'footer_line': 'Comic fantasy and science fiction.',
        'tagline': 'Dragons with opinions. Spaceships with attitude problems. Heroes who would rather be somewhere else.',
        'hero_eyebrow': 'Fantasy & Science Fiction',
        'scroll': 'Scroll',
        'read_more': 'Read more',
        'series': 'Series',
        'enter_series': 'Enter the series',
        'books_count': 'books',
        'view_all': 'View all',
        'editions': 'Editions',
        'or_write_to': 'Or write straight to',
        'legal': 'Legal',
        'nothing_here': 'Nothing here yet.',
        'library_lead': 'Every book, the series it belongs to, and the languages it has been published in.',
        'not_found_lead': 'This page has drifted out of orbit. The books are still where you left them.',
        'back_home': 'Back to the homepage',
        'sec_books_over': 'The Books',
        'sec_series_over': 'The Series',
        'sec_author_over': 'The Author',
        'sec_news_over': 'Dispatches',
        'sec_contact_over': 'Correspondence',
        'sec_shop_over': 'The Bookshop',
    },
    'bg': {
        'synopsis_not_available': 'Няма налична анотация.',
        'available_on': 'Налично в',
        'no_links_lang': 'Все още няма линкове за този език.',
        'synopsis': 'Анотация',
        'read_excerpt': 'Прочети откъс',
        'latest_works': 'Най-нови творби',
        'welcome': 'Добре дошли в Моите светове',
        'explore_library': 'Разгледай цялата библиотека',
        'latest_news': 'Последни новини',
        'read_all_news': 'Прочети всички новини',
        'the_library': 'Библиотека',
        'explore_series': 'Разгледай поредиците',
        'other_works': 'Други творби',
        'standalone_novels': 'Самостоятелни романи',
        'short_stories': 'Разкази',
        'books_in_series': 'Книги в поредицата',
        'in_progress': 'В процес',
        'news_and_updates': 'Новини и събития',
        'no_news': 'Все още няма новини. Очаквайте скоро!',
        'about_the_author': 'За автора',
        'get_in_touch': 'Свържете се с мен',
        'contact_intro': 'За бизнес запитвания, медийни покани или просто да кажете "здравей", моля, използвайте формата по-долу.',
        'name': 'Име', 'email': 'Имейл', 'message': 'Съобщение', 'send_message': 'Изпрати съобщение',
        'back': 'Назад', 'excerpt_from': 'Откъс от',
        'not_found': 'Страницата не е намерена',
        'privacy_policy': 'Политика за поверителност',
        'terms_of_service': 'Общи условия',
        'customer_support': 'Обслужване на клиенти',
        'search': 'Търсене',
        'store': 'Книжарница',
        'store_intro': 'Книги, които се продават направо от автора, без посредник. Линкът за изтегляне идва в мига, в който плащането мине.',
        'store_note': 'Плащането и фактурите минават през Creem, продавач по договор за тези поръчки. Книгите се доставят във формат EPUB. Подробностите са в {terms}.',
        'store_heading': 'Купи директно от автора',
        'store_cta': 'Към книжарницата',
        'editions_in': 'Издания на',
        'read_excerpt_short': 'Прочети откъс',
        'search_placeholder': 'Търсене на книга…',
        'search_none': 'Няма намерено',
        'by': 'от',
        'cookie_text': 'Използваме "бисквитки", за да подобрим вашето преживяване и за анализи. Продължавайки, вие се съгласявате с нашата <a href="/bg/privacy-policy/">Политика за поверителност</a>.',
        'cookie_accept': 'Приемам',
        'get_gift': 'Вземи безплатно',
        'desc_library': 'Всички романи и разкази на K.Z. Pendrake, поредиците, към които принадлежат, и езиците, на които излизат.',
        'desc_novels': 'Самостоятелните романи на K.Z. Pendrake - хумористично фентъзи и научна фантастика извън книгите за Куибълтаун.',
        'desc_stories': 'Разкази на K.Z. Pendrake, разположени в световете на романите.',
        'desc_news': 'Нови заглавия, преводи и над какво работи K.Z. Pendrake в момента.',
        'desc_about': 'K.Z. Pendrake пише хумористично фентъзи и научна фантастика. Кой стои зад псевдонима и как се раждат книгите.',
        'desc_privacy': 'Какво събира този сайт, защо и как да поискате данните си да бъдат изтрити.',
        'desc_terms': 'Авторски права, външни книжарници и какво може да правите с книгите.',
        'skip_to_content': 'Към съдържанието',
        'main_menu': 'Главно меню',
        'footer_line': 'Хумористично фентъзи и научна фантастика.',
        'tagline': 'Дракони с мнение. Космически кораби с проблеми в характера. Герои, които предпочитат да са другаде.',
        'hero_eyebrow': 'Фентъзи и научна фантастика',
        'scroll': 'Надолу',
        'read_more': 'Прочети повече',
        'series': 'Поредица',
        'enter_series': 'Влез в поредицата',
        'books_count': 'книги',
        'view_all': 'Виж всички',
        'editions': 'Издания',
        'or_write_to': 'Или пишете направо на',
        'legal': 'Правила',
        'nothing_here': 'Тук още няма нищо.',
        'library_lead': 'Всяка книга, поредицата, към която принадлежи, и езиците, на които е издадена.',
        'not_found_lead': 'Тази страница е излязла от орбита. Книгите са там, където ги оставихте.',
        'back_home': 'Към началната страница',
        'sec_books_over': 'Книгите',
        'sec_series_over': 'Поредиците',
        'sec_author_over': 'Авторът',
        'sec_news_over': 'Новини',
        'sec_contact_over': 'Кореспонденция',
        'sec_shop_over': 'Книжарницата',
    },
}


# Direct-sale button, one label per book language (the chrome stays en/bg, the book does not).
BUY_DIRECT_LABELS = {
    'bg': 'Купи директно от автора за {price}',
    'en': 'Buy direct from the author for {price}',
    'de': 'Direkt vom Autor kaufen für {price}',
    'fr': "Acheter directement à l'auteur pour {price}",
    'it': "Acquista direttamente dall'autore per {price}",
    'nl': 'Koop rechtstreeks bij de auteur voor {price}',
    'es': 'Compra directamente al autor por {price}',
    'pt': 'Compre diretamente ao autor por {price}',
    'se': 'Köp direkt av författaren för {price}',
}

# (decimal separator, layout) per language. Prices are in euro;   keeps
# the amount and the symbol on the same line.
PRICE_FORMATS = {
    'bg': (',', '{amount} €'),
    'en': ('.', '€{amount}'),
    'de': (',', '{amount} €'),
    'fr': (',', '{amount} €'),
    'it': (',', '{amount} €'),
    'nl': (',', '€ {amount}'),
    'es': (',', '{amount} €'),
    'pt': (',', '{amount} €'),
    'se': (',', '{amount} €'),
}


# Short form of the same button, for the bookshop rows where the price stands on its own.
BUY_DIRECT_SHORT = {
    'bg': 'Купи директно',
    'en': 'Buy direct',
    'de': 'Direkt kaufen',
    'fr': 'Acheter directement',
    'it': 'Acquista direttamente',
    'nl': 'Direct kopen',
    'es': 'Compra directa',
    'pt': 'Compra direta',
    'se': 'Köp direkt',
}

# Names of the book languages, in each of the two chrome languages.
LANG_NAMES = {
    'en': {'bg': 'Bulgarian', 'en': 'English', 'de': 'German', 'fr': 'French', 'it': 'Italian',
           'nl': 'Dutch', 'es': 'Spanish', 'pt': 'Portuguese', 'se': 'Swedish'},
    'bg': {'bg': 'български', 'en': 'английски', 'de': 'немски', 'fr': 'френски', 'it': 'италиански',
           'nl': 'нидерландски', 'es': 'испански', 'pt': 'португалски', 'se': 'шведски'},
}

# Set by build.py: False hides the bookshop from the menu, the footer and the
# homepage, so nothing ever points at an empty shelf.
STORE_ACTIVE = False


# Each language's own name for itself. One list serves all nine editions, which
# beats keeping nine names in nine languages.
LANG_AUTONYMS = {
    'bg': 'български', 'en': 'English', 'de': 'Deutsch', 'fr': 'Français',
    'it': 'Italiano', 'nl': 'Nederlands', 'es': 'Español', 'pt': 'Português',
    'se': 'Svenska',
}

# The plain statement of what a book is, in the language of the book. A reader
# infers it from the cover; a language model has to read it written down.
# Every part is optional - the sentence is assembled from whatever data exists.
BOOK_FACTS = {
    'bg': {'base': '„{title}“ е {genre} от {author}.',
           'series_n': ' Книга {n} от поредицата „{series}“.',
           'series': ' Част от поредицата „{series}“.',
           'published': ' Издадена през {year} г.',
           'publisher': ' Издател: {publisher}.',
           'isbn': ' ISBN {isbn}.',
           'langs': ' Издания на: {langs}.'},
    'en': {'base': '“{title}” is {article}{genre} by {author}.',
           'article': 'a ',
           'series_n': ' Book {n} of the {series} series.',
           'series': ' Part of the {series} series.',
           'published': ' Published in {year}.',
           'publisher': ' Publisher: {publisher}.',
           'isbn': ' ISBN {isbn}.',
           'langs': ' Editions in: {langs}.'},
    'de': {'base': '„{title}“ ist {article}{genre} von {author}.',
           'article': 'ein ',
           'series_n': ' Band {n} der Reihe „{series}“.',
           'series': ' Teil der Reihe „{series}“.',
           'published': ' Erschienen {year}.',
           'publisher': ' Verlag: {publisher}.',
           'isbn': ' ISBN {isbn}.',
           'langs': ' Ausgaben auf: {langs}.'},
    'fr': {'base': '« {title} » est {article}{genre} de {author}.',
           'article': 'un ',
           'series_n': ' Tome {n} de la série « {series} ».',
           'series': ' Fait partie de la série « {series} ».',
           'published': ' Publié en {year}.',
           'publisher': ' Éditeur : {publisher}.',
           'isbn': ' ISBN {isbn}.',
           'langs': ' Éditions en : {langs}.'},
    'it': {'base': '«{title}» è {article}{genre} di {author}.',
           'article': 'un ',
           'series_n': ' Libro {n} della serie «{series}».',
           'series': ' Fa parte della serie «{series}».',
           'published': ' Pubblicato nel {year}.',
           'publisher': ' Editore: {publisher}.',
           'isbn': ' ISBN {isbn}.',
           'langs': ' Edizioni in: {langs}.'},
    'nl': {'base': '“{title}” is {article}{genre} van {author}.',
           'article': 'een ',
           'series_n': ' Deel {n} van de reeks “{series}”.',
           'series': ' Onderdeel van de reeks “{series}”.',
           'published': ' Verschenen in {year}.',
           'publisher': ' Uitgever: {publisher}.',
           'isbn': ' ISBN {isbn}.',
           'langs': ' Edities in: {langs}.'},
    'es': {'base': '«{title}» es {article}{genre} de {author}.',
           'article': 'un ',
           'series_n': ' Libro {n} de la serie «{series}».',
           'series': ' Forma parte de la serie «{series}».',
           'published': ' Publicado en {year}.',
           'publisher': ' Editorial: {publisher}.',
           'isbn': ' ISBN {isbn}.',
           'langs': ' Ediciones en: {langs}.'},
    'pt': {'base': '«{title}» é {article}{genre} de {author}.',
           'article': 'um ',
           'series_n': ' Livro {n} da série «{series}».',
           'series': ' Faz parte da série «{series}».',
           'published': ' Publicado em {year}.',
           'publisher': ' Editora: {publisher}.',
           'isbn': ' ISBN {isbn}.',
           'langs': ' Edições em: {langs}.'},
    'se': {'base': '”{title}” är {article}{genre} av {author}.',
           'article': 'en ',
           'series_n': ' Bok {n} i serien ”{series}”.',
           'series': ' Del av serien ”{series}”.',
           'published': ' Utgiven {year}.',
           'publisher': ' Förlag: {publisher}.',
           'isbn': ' ISBN {isbn}.',
           'langs': ' Utgåvor på: {langs}.'},
}


# Articles a genre may already carry. "Una historia satírica de burocracia
# mágica" is a whole phrase, not a bare genre noun, so the template must not
# put a second article in front of it.
GENRE_ARTICLES = {
    'en': r"(a|an|the)\b", 'de': r"(ein|eine|einer)\b", 'fr': r"(un|une)\b",
    'it': r"(un|uno|una|un')", 'nl': r"(een)\b", 'es': r"(un|una|unos|unas)\b",
    'pt': r"(um|uma)\b", 'se': r"(en|ett)\b",
}


def genre_has_article(lang, genre):
    import re as _re
    pattern = GENRE_ARTICLES.get(lang)
    return bool(pattern and _re.match(pattern, genre, _re.IGNORECASE))


def genre_article(lang, genre, default):
    """The article to put before the genre, or nothing when it brings its own."""
    if genre_has_article(lang, genre):
        return ''
    if lang == 'en' and genre[:1].lower() in 'aeiou':
        return 'an '
    return default


def short_genre(genre):
    """Genre fields are catalogue strings - "Urban Fantasy, Supernatural Thriller".
    A sentence needs the first part, spelled the way the author typed it:
    lowercasing turns a name like Urban Fantasy into something that reads wrong."""
    import re as _re
    return _re.split(r'[/,;]', str(genre or ''))[0].strip()


def year_of(date_str):
    """First four digits of whatever the admin panel holds: 2026-03-14, 03/2026, 2026."""
    import re as _re
    m = _re.search(r'\d{4}', str(date_str or ''))
    return m.group(0) if m else ''


def series_title_for(series, lang):
    if not series:
        return ''
    ui = ui_lang_of(lang)
    sd = series['i18n'].get(lang) or series['i18n'].get(ui) or series['i18n'].get('en') or {}
    return sd.get('title', '')


def book_facts_sentence(data, book, lang, series=None):
    """One sentence stating what this book is, built from whatever data exists.
    Empty when there is not even a genre to state."""
    bdata = book['i18n'].get(lang) or {}
    tpl = BOOK_FACTS.get(lang, BOOK_FACTS['en'])
    genre = short_genre(bdata.get('genre'))
    if not genre or not bdata.get('title'):
        return ''
    article = genre_article(lang, genre, tpl.get('article', ''))
    if genre_has_article(lang, genre):
        # The genre carries its own article. It was typed as a standalone label,
        # so it starts with a capital; mid-sentence that reads like a title.
        genre = genre[0].lower() + genre[1:]
    out = tpl['base'].format(title=bdata['title'], genre=genre,
                             author=author_name(data, lang), article=article)
    stitle = series_title_for(series, lang)
    if stitle:
        if lang == 'en':
            # The English template supplies the article, so a series called
            # "The Age of the Fallen" must not bring its own.
            import re as _re
            stitle = _re.sub(r'^the\s+', '', stitle, flags=_re.IGNORECASE)
        pos = book.get('position')
        out += (tpl['series_n'].format(n=pos, series=stitle) if pos
                else tpl['series'].format(series=stitle))
    year = year_of(bdata.get('published'))
    if year:
        out += tpl['published'].format(year=year)
    if bdata.get('publisher'):
        out += tpl['publisher'].format(publisher=bdata['publisher'])
    if bdata.get('isbn'):
        out += tpl['isbn'].format(isbn=bdata['isbn'])
    others = [LANG_AUTONYMS[l] for l in ALL_LANGS
              if l in book.get('i18n', {}) and book['i18n'][l].get('title')]
    if len(others) > 1:
        out += tpl['langs'].format(langs=', '.join(others))
    return out


def render_book_facts(data, book, lang, series=None):
    text = book_facts_sentence(data, book, lang, series)
    return f'<p class="book-facts">{esc(text)}</p>' if text else ''


def esc(s):
    return _html.escape(str(s or ''), quote=True)


def ui_lang_of(lang):
    """Chrome language for a given content language: en/bg map to themselves, everything else -> en."""
    return lang if lang in UI_LANGS else 'en'


def prefix(lang):
    return '' if lang == 'en' else f'/{lang}'


def home_path(lang):
    return prefix(lang) + '/'


def library_path(lang, sub=''):
    return prefix(lang) + '/library/' + (sub + '/' if sub else '')


def series_path(sid, lang):
    return prefix(lang) + f'/series/{sid}/'


def book_path(bid, lang):
    return prefix(lang) + f'/book/{bid}/'


def excerpt_path(bid, lang):
    return prefix(lang) + f'/excerpt/{bid}/'


def about_path(lang):
    return prefix(lang) + '/about/'


def contact_path(lang):
    return prefix(lang) + '/contact/'


def news_path(lang):
    return prefix(lang) + '/news/'


def news_article_path(slug, lang):
    return prefix(lang) + f'/news/{slug}/'


def privacy_path(lang):
    return prefix(lang) + '/privacy-policy/'


def terms_path(lang):
    return prefix(lang) + '/terms-of-service/'


def store_path(lang):
    return prefix(lang) + '/store/'


def site_title(data, lang):
    ui = ui_lang_of(lang)
    return data['meta'][ui]['siteTitle']


def author_name(data, lang):
    ui = ui_lang_of(lang)
    return data['meta'][ui]['name']


def find_book_by_id(data, bid):
    """Return (book, kind, series_id) or (None, None, None)."""
    for s in data.get('series', []):
        for b in s.get('books', []):
            if b['id'] == bid:
                return b, 'series', s['id']
    for b in data.get('novels', []):
        if b['id'] == bid:
            return b, 'novel', None
    for b in data.get('short_stories', []):
        if b['id'] == bid:
            return b, 'story', None
    return None, None, None


# ─────────────────────────────────────────────────────────────────────────
# STRUCTURED DATA (JSON-LD)
# ─────────────────────────────────────────────────────────────────────────

def abs_url(path):
    """Site-root-relative path or asset path -> absolute URL."""
    return BASE_URL + '/' + str(path or '').lstrip('/')


def person_ref(data, lang):
    """The author, as one node every other node can point at."""
    ui = ui_lang_of(lang)
    node = {
        '@type': 'Person',
        '@id': BASE_URL + '/#author',
        'name': author_name(data, lang),
        'url': abs_url(about_path(ui)),
    }
    photo = (data.get('meta') or {}).get('photo')
    if photo:
        node['image'] = abs_url(photo)
    return node


def jsonld_website(data, lang):
    ui = ui_lang_of(lang)
    return {
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        '@id': BASE_URL + '/#website',
        'name': site_title(data, ui),
        'url': abs_url(home_path(ui)),
        'inLanguage': bcp47(ui),
        'publisher': person_ref(data, ui),
    }


def jsonld_person(data, lang, bio_text=''):
    ui = ui_lang_of(lang)
    node = dict(person_ref(data, ui), **{'@context': 'https://schema.org'})
    bio = ' '.join((bio_text or '').split())
    if bio:
        node['description'] = bio[:300]
    node['jobTitle'] = 'Author' if ui == 'en' else 'Писател'
    return node


def jsonld_book(data, book, lang, synopsis_text='', series=None):
    """One node per language edition, because each edition has its own title,
    cover and - where the author sells it himself - its own price."""
    bdata = book['i18n'].get(lang) or {}
    node = {
        '@context': 'https://schema.org',
        '@type': 'Book',
        'name': bdata.get('title', ''),
        'url': abs_url(book_path(book['id'], lang)),
        'author': person_ref(data, lang),
        'inLanguage': bcp47(lang),
        'bookFormat': 'https://schema.org/EBook',
    }
    if bdata.get('genre'):
        node['genre'] = bdata['genre']
    if bdata.get('published'):
        node['datePublished'] = str(bdata['published'])
    if bdata.get('isbn'):
        node['isbn'] = str(bdata['isbn'])
    if bdata.get('publisher'):
        node['publisher'] = {'@type': 'Organization', 'name': bdata['publisher']}
    if book.get('position'):
        node['position'] = book['position']
    abstract = book_facts_sentence(data, book, lang, series)
    if abstract:
        node['abstract'] = abstract
    if bdata.get('cover'):
        node['image'] = abs_url(bdata['cover'])
    syn = ' '.join((synopsis_text or '').split())
    if syn:
        node['description'] = syn[:300]
    if series:
        ui = ui_lang_of(lang)
        sd = series['i18n'].get(lang) or series['i18n'].get(ui) or series['i18n'].get('en') or {}
        if sd.get('title'):
            node['isPartOf'] = {
                '@type': 'BookSeries',
                'name': sd['title'],
                'url': abs_url(series_path(series['id'], ui)),
            }
    url = (bdata.get('creem_checkout_url') or '').strip()
    price = str(bdata.get('price') or '').strip()
    if bdata.get('direct_sale_active') and url and price:
        node['offers'] = {
            '@type': 'Offer',
            'price': price,
            'priceCurrency': 'EUR',
            'availability': 'https://schema.org/InStock',
            'url': url,
        }
    links = [l for l in book.get('links', []) if l.get('lang', '').lower() == lang.lower() and l.get('url')]
    if links:
        node['sameAs'] = [l['url'] for l in links]
    return node


def jsonld_article(data, lang, article):
    ui = ui_lang_of(lang)
    node = {
        '@context': 'https://schema.org',
        '@type': 'Article',
        'headline': article.get('title', ''),
        'url': abs_url(news_article_path(article['slug'], ui)),
        'author': person_ref(data, ui),
        'publisher': person_ref(data, ui),
        'inLanguage': bcp47(ui),
    }
    if article.get('date_raw'):
        node['datePublished'] = article['date_raw']
    if article.get('excerpt'):
        node['description'] = article['excerpt'][:300]
    return node


def jsonld_breadcrumbs(items):
    """items: list of (name, site-root-relative path)."""
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': name, 'item': abs_url(path)}
            for i, (name, path) in enumerate(items, start=1)
        ],
    }


def book_breadcrumbs(data, book, lang, series=None, leaf=None):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    bdata = book['i18n'].get(lang) or {}
    items = [(author_name(data, ui), home_path(ui)), (s['the_library'], library_path(ui))]
    if series:
        sd = series['i18n'].get(lang) or series['i18n'].get(ui) or series['i18n'].get('en') or {}
        if sd.get('title'):
            items.append((sd['title'], series_path(series['id'], ui)))
    items.append((bdata.get('title', book['id']), book_path(book['id'], lang)))
    if leaf:
        items.append((leaf, excerpt_path(book['id'], lang)))
    return jsonld_breadcrumbs(items)


# ─────────────────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────────────────

def layout(data, *, lang, path, title, description, body_html,
           og_image='images/common/social-share.jpg', hreflangs=None,
           active_nav_base=None, nav_lang_switch=None,
           og_type='website', jsonld=None, body_class=''):
    """
    lang: content/page language (drives <html lang>)
    path: this page's site-root-relative path, e.g. '/book/foo/'
    hreflangs: list of (hreflang_code, absolute_url) for <link rel=alternate>
    active_nav_base: which nav item should be marked active ('/', 'library/', ...)
    nav_lang_switch: {'en': url_or_None, 'bg': url_or_None} for the EN|BG switcher
    og_type: 'website', 'book', 'article', 'profile'
    jsonld: one schema.org dict, or a list of them
    body_class: extra class on <body> ('home' turns the header transparent)
    """
    ui = ui_lang_of(lang)
    depth = path.strip('/').count('/') + 1 if path != '/' else 0
    root = '../' * depth if depth else './'
    canonical = BASE_URL + path

    hreflang_tags = ''
    locale_alt_tags = ''
    if hreflangs:
        tags = [f'<link rel="alternate" hreflang="{bcp47(code)}" href="{url}">'
                for code, url in hreflangs]
        # Whoever does not match any of the listed languages lands on the English
        # edition; without x-default Google picks one for them.
        default = dict(hreflangs).get('en') or hreflangs[0][1]
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{default}">')
        hreflang_tags = '\n    '.join(tags)
        locale_alt_tags = '\n    '.join(
            f'<meta property="og:locale:alternate" content="{OG_LOCALES[code]}">'
            for code, _ in hreflangs if code != lang and code in OG_LOCALES
        )

    jsonld_tags = ''
    if jsonld:
        blocks = jsonld if isinstance(jsonld, list) else [jsonld]
        jsonld_tags = '\n    '.join(
            '<script type="application/ld+json">'
            + _json.dumps(b, ensure_ascii=False, separators=(',', ':'))
            + '</script>'
            for b in blocks
        )

    # Analytics only ships when there is an id to ship it to.
    ga_tags = ''
    if GA_ID:
        ga_tags = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
       window.dataLayer = window.dataLayer || [];
       function gtag(){{dataLayer.push(arguments);}}
       gtag('js', new Date());
       gtag('config', '{GA_ID}');
    </script>"""

    nav_items = ''
    menu_items = ''
    for href, label in NAV_LABELS[ui]:
        if href == 'store/' and not STORE_ACTIVE:
            continue
        is_active = (href == '/' and active_nav_base == '/') or \
                    (href != '/' and active_nav_base and active_nav_base.startswith(href))
        # Language-aware: the BG chrome must stay inside /bg/, not fall back to the EN pages.
        nav_href = prefix(ui) + '/' + href.lstrip('/')
        active = ' active' if is_active else ''
        nav_items += f'<li><a href="{nav_href}" class="nav-link{active}">{esc(label)}</a></li>'
        menu_items += f'<li><a href="{nav_href}" class="menu-link{active}">{esc(label)}</a></li>'

    lang_switch_html = ''
    if nav_lang_switch:
        parts = []
        for code in ('en', 'bg'):
            url = nav_lang_switch.get(code)
            label = code.upper()
            if ui == code:
                parts.append(f'<span class="on">{label}</span>')
            elif url:
                parts.append(f'<a href="{url}">{label}</a>')
        lang_switch_html = '<span class="sep">&#183;</span>'.join(parts)

    strings = UI_STRINGS[ui]
    year = _dt.date.today().year
    footer_nav = ''.join(
        f'<li><a href="{prefix(ui)}/{href.lstrip("/")}">{esc(label)}</a></li>'
        for href, label in NAV_LABELS[ui]
        if not (href == 'store/' and not STORE_ACTIVE)
    )

    return f"""<!DOCTYPE html>
<html lang="{bcp47(lang)}" data-site-lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{esc(title)}</title>

    <meta name="description" content="{esc(description)}">
    <meta name="author" content="K.Z. Pendrake">
    <meta name="theme-color" content="#0a1430">

    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:image" content="{BASE_URL}/{og_image.lstrip('/')}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:type" content="{og_type}">
    <meta property="og:site_name" content="{esc(site_title(data, ui))}">
    <meta property="og:locale" content="{OG_LOCALES.get(lang, 'en_US')}">
    {locale_alt_tags}

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(description)}">
    <meta name="twitter:image" content="{BASE_URL}/{og_image.lstrip('/')}">

    <link rel="canonical" href="{canonical}">
    {hreflang_tags}

    {jsonld_tags}

    <link rel="apple-touch-icon" sizes="180x180" href="{root}images/common/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="{root}images/common/favicons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="{root}images/common/favicons/favicon-16x16.png">
    <link rel="manifest" href="{root}images/common/favicons/site.webmanifest">

    {ga_tags}

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Jost:wght@200;300;400;500;600&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{root}style.css{asset_v('css')}">
</head>
<body class="{esc(body_class)}">
<a class="skip-link" href="#main-content">{esc(strings['skip_to_content'])}</a>

<header class="site-header" id="site-header">
    <div class="nav">
        <a href="{home_path(ui)}" class="wordmark" aria-label="K.Z. Pendrake">
            {DIAMOND_SVG}
            <span class="wordmark-text">K.Z.&#8202;Pendrake</span>
        </a>

        <nav class="nav-menu" aria-label="{esc(strings['main_menu'])}">
            <ul>{nav_items}</ul>
        </nav>

        <div class="nav-tools">
            <div class="nav-search">
                <button type="button" class="icon-btn search-toggle" aria-label="{esc(strings['search'])}" aria-expanded="false">
                    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.7"
                         stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><line x1="16.5" y1="16.5" x2="21" y2="21"></line></svg>
                </button>
                <div class="search-panel">
                    <input type="search" class="search-input" autocomplete="off" spellcheck="false"
                           placeholder="{esc(strings['search_placeholder'])}" aria-label="{esc(strings['search'])}">
                    <div class="search-results" data-none="{esc(strings['search_none'])}" hidden></div>
                </div>
            </div>
            <div class="lang-switcher">{lang_switch_html}</div>
            <button class="hamburger" aria-label="{esc(strings['main_menu'])}" aria-expanded="false">
                <span class="bar"></span><span class="bar"></span><span class="bar"></span>
            </button>
        </div>
    </div>
</header>

<div class="mobile-menu" id="mobile-menu" hidden>
    <div class="mobile-menu-inner">
        <ul>{menu_items}</ul>
        <div class="mobile-menu-lang">{lang_switch_html}</div>
    </div>
</div>

<main id="main-content">
{body_html}
</main>

<footer class="site-footer">
    <div class="footer-rule">{RULE_SVG}</div>
    <div class="container footer-grid">
        <div class="footer-brand">
            <a href="{home_path(ui)}" class="wordmark footer-wordmark">{DIAMOND_SVG}<span class="wordmark-text">K.Z.&#8202;Pendrake</span></a>
            <p class="footer-line">{esc(strings['footer_line'])}</p>
        </div>
        <nav class="footer-nav" aria-label="{esc(strings['main_menu'])}"><ul>{footer_nav}</ul></nav>
        <div class="footer-contact">
            <p>{esc(strings['customer_support'])}</p>
            <p><a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
        </div>
    </div>
    <div class="container footer-bottom">
        <p>&copy; {year} K.Z. Pendrake</p>
        <p><a href="{privacy_path(ui)}">{esc(strings['privacy_policy'])}</a>
           <span class="sep">&#183;</span>
           <a href="{terms_path(ui)}">{esc(strings['terms_of_service'])}</a>{f'<span class="sep">&#183;</span><a href="{store_path(ui)}">{esc(strings["store"])}</a>' if STORE_ACTIVE else ''}</p>
    </div>
</footer>

<div id="cookie-banner" class="cookie-banner">
    <div class="cookie-content">
        <p id="cookie-text">{strings['cookie_text']}</p>
        <button id="cookie-accept-btn" class="btn btn-small">{esc(strings['cookie_accept'])}</button>
    </div>
</div>

<script src="{root}assets/site.js{asset_v('js')}"></script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────
# DECO FURNITURE
# ─────────────────────────────────────────────────────────────────────────

DIAMOND_SVG = ('<svg class="mark" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.15" '
               'aria-hidden="true"><path d="M16 2l3.2 10.8L30 16l-10.8 3.2L16 30l-3.2-10.8L2 16l10.8-3.2z"/>'
               '<circle cx="16" cy="16" r="3.2"/></svg>')

RULE_SVG = ('<svg viewBox="0 0 260 18" fill="none" stroke="currentColor" stroke-width="1" aria-hidden="true">'
            '<path d="M0 9h108M152 9h108"/>'
            '<path d="M130 2l7 7-7 7-7-7z" fill="currentColor" stroke="none"/>'
            '<path d="M108 9l8-5M152 9l-8-5M108 9l8 5M152 9l-8 5"/></svg>')

CREST_SVG = ('<svg viewBox="0 0 340 22" fill="none" stroke="currentColor" stroke-width="1" aria-hidden="true">'
             '<path d="M0 11h132l12-7 12 7M172 11l12-7 12 7h144"/>'
             '<circle cx="170" cy="11" r="4" fill="currentColor" stroke="none"/></svg>')


def section_head(overline, title, tag='h2'):
    """Numbered rule + title, the repeating unit of every page below the fold."""
    over = f'<span class="sec-over">{esc(overline)}</span>' if overline else ''
    return (f'<div class="sec-head rv">{over}'
            f'<{tag} class="sec-title">{esc(title)}</{tag}>'
            f'<span class="sec-rule"></span></div>')


def page_header(title, overline='', lead='', extra=''):
    """The band under the chrome on every page that is not the homepage."""
    over = f'<p class="ph-over rv">{esc(overline)}</p>' if overline else ''
    lead_html = f'<p class="ph-lead rv" data-d="2">{lead}</p>' if lead else ''
    return f"""
        <section class="page-header">
            <div class="container">
                {over}
                <h1 class="ph-title rv" data-d="1">{esc(title)}</h1>
                <div class="deco-rule rv" data-d="1">{RULE_SVG}</div>
                {lead_html}
                {extra}
            </div>
        </section>"""


# ─────────────────────────────────────────────────────────────────────────
# SHARED PIECES
# ─────────────────────────────────────────────────────────────────────────

def book_card(book, ui_lang, delay=0):
    i18n = book.get('i18n', {})
    display_lang = ui_lang if ui_lang in i18n else 'en'
    bdata = i18n.get(display_lang) or next(iter(i18n.values()), None)
    if not bdata:
        return ''
    title = bdata.get('title', '')
    cover = bdata.get('cover') or 'images/common/cover-placeholder.jpg'
    genre = bdata.get('genre', '')
    pills = ''.join(
        f'<a href="{book_path(book["id"], l)}" class="lang-pill">{l.upper()}</a>'
        for l in i18n
    )
    status = f'<span class="status-tag">{esc(UI_STRINGS[ui_lang]["in_progress"])}</span>' \
        if book.get('status') == 'in-progress' else ''
    href = book_path(book['id'], display_lang)
    d = f' data-d="{delay}"' if delay else ''
    return f"""<article class="book-card rv"{d}>
        <a class="book-card-cover" href="{href}" tabindex="-1" aria-hidden="true">
            <span class="cover-frame"><img src="/{esc(cover)}" alt="" loading="lazy"></span>
        </a>
        <div class="book-card-body">
            {f'<p class="book-card-genre">{esc(genre)}</p>' if genre else ''}
            <h3 class="book-card-title"><a href="{href}">{esc(title)}</a></h3>
            <div class="lang-pills">{pills}</div>
            {status}
        </div>
    </article>"""


def _rel_img(path):
    return '/' + path.lstrip('/') if path else ''


def _strip_trailing_link(html_str):
    """The author intro in data.js ends with its own "Learn more..." link.
    On the homepage that link sits next to a Read more button, so drop it there."""
    return _re.sub(r'\s*<a\b[^>]*>.*?</a>\s*$', '', html_str or '', flags=_re.DOTALL).rstrip()


# ─────────────────────────────────────────────────────────────────────────
# PAGE BODIES
# ─────────────────────────────────────────────────────────────────────────

def render_homepage(data, lang, latest_news_html='', store_band=''):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    meta = data['meta'][ui]
    cards = []
    for i, bid in enumerate(data.get('featured', [])):
        book, _, _ = find_book_by_id(data, bid)
        if book:
            cards.append(book_card(book, ui, delay=min(i + 1, 3)))

    series_cards = ''
    for i, series in enumerate(data.get('series', [])):
        sd = series['i18n'].get(ui) or series['i18n'].get('en') or {}
        img = series.get('seriesImage')
        style = f" style=\"background-image:url('/{esc(img)}')\"" if img else ''
        series_cards += f"""<a class="series-card rv" data-d="{min(i + 1, 3)}" href="{series_path(series['id'], lang)}">
            <span class="series-card-img"{style}></span>
            <span class="series-card-body">
                <span class="series-card-over">{esc(s['series'])}</span>
                <span class="series-card-title">{esc(sd.get('title', series['id']))}</span>
                <span class="series-card-cta">{esc(s['enter_series'])}</span>
            </span>
        </a>"""

    series_block = ''
    if series_cards:
        series_block = f"""<section class="section series-section">
            <div class="container">
                {section_head(s['sec_series_over'], s['explore_series'])}
                <div class="series-grid">{series_cards}</div>
            </div>
        </section>"""

    return f"""
        <section class="hero" id="hero">
            <canvas id="orrery" aria-hidden="true"></canvas>
            <div class="hero-inner">
                <div class="deco-crest rv in">{CREST_SVG}</div>
                <p class="hero-eyebrow rv in" data-d="1">{esc(s['hero_eyebrow'])}</p>
                <h1 class="hero-title rv in" data-d="1">K<span class="dot">.</span>Z<span class="dot">.</span>Pendrake</h1>
                <p class="hero-tagline rv in" data-d="2">{esc(s['tagline'])}</p>
                <div class="deco-rule rv in" data-d="2">{RULE_SVG}</div>
                <div class="hero-cta rv in" data-d="3">
                    <a href="{library_path(lang)}" class="btn btn-solid">{esc(s['explore_library'])}</a>
                    <a href="{about_path(lang)}" class="btn">{esc(s['about_the_author'])}</a>
                </div>
            </div>
            <div class="scroll-cue" aria-hidden="true"><span>{esc(s['scroll'])}</span><span class="line"></span></div>
        </section>

        <section class="section featured-section">
            <div class="container">
                {section_head(s['sec_books_over'], s['latest_works'])}
                <div class="books-grid featured-grid">{''.join(cards)}</div>
                <div class="section-cta rv"><a href="{library_path(lang)}" class="btn">{esc(s['explore_library'])}</a></div>
            </div>
        </section>

        {series_block}

        <section class="section intro-section">
            <div class="container intro-grid">
                <div class="intro-figure rv">
                    <span class="portrait-frame"><img src="/{esc(data['meta'].get('photo', 'images/common/author-placeholder.jpg'))}" alt="{esc(author_name(data, ui))}" loading="lazy"></span>
                </div>
                <div class="intro-body">
                    {section_head(s['sec_author_over'], s['about_the_author'])}
                    <p class="intro-text rv" data-d="1">{_strip_trailing_link(meta['intro'])}</p>
                    <div class="rv" data-d="2"><a href="{about_path(lang)}" class="btn">{esc(s['read_more'])}</a></div>
                </div>
            </div>
        </section>

        {store_band}
        {latest_news_html}"""


def render_news_excerpt_block(lang, article_title, excerpt_text, slug):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    return f"""<section class="section news-teaser-section">
        <div class="container">
            {section_head(s['sec_news_over'], s['latest_news'])}
            <article class="news-teaser rv">
                <h3><a href="{news_article_path(slug, lang)}">{esc(article_title)}</a></h3>
                <p>{esc(excerpt_text)}</p>
                <a href="{news_path(lang)}" class="link-arrow">{esc(s['read_all_news'])}</a>
            </article>
        </div>
    </section>"""


def render_library_hub(data, lang):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    cards = ''
    for i, series in enumerate(data.get('series', [])):
        sd = series['i18n'].get(ui) or series['i18n'].get('en') or {}
        img = series.get('seriesImage')
        style = f" style=\"background-image:url('/{esc(img)}')\"" if img else ''
        count = len(series.get('books', []))
        cards += f"""<a class="series-card rv" data-d="{min(i + 1, 3)}" href="{series_path(series['id'], lang)}">
            <span class="series-card-img"{style}></span>
            <span class="series-card-body">
                <span class="series-card-over">{count} {esc(s['books_count'])}</span>
                <span class="series-card-title">{esc(sd.get('title', series['id']))}</span>
                <span class="series-card-cta">{esc(s['enter_series'])}</span>
            </span>
        </a>"""

    shelves = ''
    for i, (sub, key) in enumerate((('novels', 'standalone_novels'), ('stories', 'short_stories'))):
        shelves += f"""<a class="shelf-card rv" data-d="{i + 1}" href="{library_path(lang, sub)}">
            <span class="shelf-card-title">{esc(s[key])}</span>
            <span class="shelf-card-cta">{esc(s['view_all'])}</span>
        </a>"""

    series_block = f"""<section class="section">
            <div class="container">
                {section_head(s['sec_series_over'], s['explore_series'])}
                <div class="series-grid">{cards}</div>
            </div>
        </section>""" if cards else ''

    return f"""
        {page_header(s['the_library'], s['sec_books_over'], esc(s['library_lead']))}
        {series_block}
        <section class="section">
            <div class="container">
                {section_head('', s['other_works'])}
                <div class="shelf-grid">{shelves}</div>
            </div>
        </section>"""


def render_series_page(data, series, lang):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    sd = series['i18n'].get(ui) or series['i18n'].get('en') or {}
    header_img = series.get('seriesImage')
    cards = ''.join(book_card(b, ui, delay=min(i + 1, 3))
                    for i, b in enumerate(series.get('books', [])))
    banner = ''
    if header_img:
        banner = (f'<div class="series-banner rv" data-d="2">'
                  f'<span class="banner-frame" style="background-image:url(\'/{esc(header_img)}\')"></span></div>')
    return f"""
        {page_header(sd.get('title', series['id']), s['series'], sd.get('series_synopsis', ''), banner)}
        <section class="section">
            <div class="container">
                {section_head('', s['books_in_series'])}
                <div class="books-grid">{cards}</div>
            </div>
        </section>"""


def render_book_list_page(data, lang, kind):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    key = 'standalone_novels' if kind == 'novels' else 'short_stories'
    books = data.get(kind, [])
    cards = ''.join(book_card(b, ui, delay=min(i + 1, 3)) for i, b in enumerate(books))
    body = f'<div class="books-grid">{cards}</div>' if cards else f'<p class="empty-note rv">{esc(s["nothing_here"])}</p>'
    return f"""
        {page_header(s[key], s['the_library'])}
        <section class="section">
            <div class="container">{body}</div>
        </section>"""


def render_lead_magnet(bdata, lang):
    """Banner + instant custom modal for a free-gift Sender.net embedded form,
    shown only if configured for this book+language. Sender.net's script is only
    loaded on click, and its embedded-form widget renders inside our own modal
    so opening is instant (no provider trigger delay)."""
    lm = bdata.get('leadMagnet') or {}
    if not lm.get('enabled') or not lm.get('senderFormId'):
        return ''
    ui = ui_lang_of(lang)
    cta = UI_STRINGS[ui]['get_gift']
    img_html = f'<img src="/{esc(lm["image"])}" alt="" class="lead-magnet-img" loading="lazy">' if lm.get('image') else ''
    return f"""
        <div class="lead-magnet-banner">
            {img_html}
            <div class="lead-magnet-body">
                <p>{esc(lm.get('bannerText', ''))}</p>
                <button type="button" class="btn btn-solid lead-magnet-cta" data-account-id="{esc(SENDER_ACCOUNT_ID)}">{esc(cta)}</button>
            </div>
        </div>
        <div class="lead-magnet-modal">
            <div class="lead-magnet-modal-inner">
                <button type="button" class="lead-magnet-modal-close" aria-label="Close">&times;</button>
                <div class="sender-form-field" data-sender-form-id="{esc(lm['senderFormId'])}"></div>
            </div>
        </div>"""


def format_price(price, lang):
    """Price as the reader of that language writes it: €9.99, 9,99 €, € 9,99.
    Anything that is not a number is printed exactly as typed in the admin panel."""
    sep, template = PRICE_FORMATS.get(lang, PRICE_FORMATS['en'])
    raw = str(price or '').strip()
    try:
        amount = f'{float(raw.replace(",", ".")):.2f}'
    except ValueError:
        return raw
    return template.format(amount=amount.replace('.', sep))


def render_direct_sale(bdata, lang):
    """Checkout button for this language edition, sold by the author through Creem.
    Every translation is its own product, so price and link come from i18n[lang].
    The label speaks the language of the book, not of the surrounding chrome."""
    if not bdata.get('direct_sale_active'):
        return ''
    url = (bdata.get('creem_checkout_url') or '').strip()
    price = str(bdata.get('price') or '').strip()
    if not url or not price:
        return ''
    label = BUY_DIRECT_LABELS.get(lang, BUY_DIRECT_LABELS['en']).format(
        price=format_price(price, lang))
    return f"""
        <div class="direct-sale">
            <a href="{esc(url)}" class="btn btn-solid direct-sale-btn" target="_blank" rel="noopener">{esc(label)}</a>
        </div>"""


def render_book_detail(data, book, lang, synopsis_html, series=None):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    bdata = book['i18n'].get(lang) or book['i18n'].get('en')
    cover = bdata.get('cover') or 'images/common/cover-placeholder.jpg'

    excerpt_link = ''
    if bdata.get('excerpt'):
        excerpt_link = (f'<a href="{excerpt_path(book["id"], lang)}" class="btn btn-block">'
                        f'{esc(s["read_excerpt"])}</a>')

    editions = ''.join(
        f'<a href="{book_path(book["id"], l)}" class="lang-pill{" on" if l == lang else ""}">{esc(LANG_AUTONYMS.get(l, l.upper()))}</a>'
        for l in book.get('i18n', {})
    )

    links = [l for l in book.get('links', []) if l.get('lang', '').lower() == lang.lower()]
    if links:
        buy_html = ''.join(
            f'<a href="{esc(l["url"])}" target="_blank" rel="noopener" class="buy-logo-link" title="{esc(l["platform"])}">'
            f'<img src="/images/common/{l["platform"].lower()}.png" alt="{esc(l["platform"])}" loading="lazy"></a>'
            for l in links
        )
    else:
        buy_html = f'<p class="muted-note">{esc(s["no_links_lang"])}</p>'

    synopsis_html = synopsis_html or f'<p>{esc(s["synopsis_not_available"])}</p>'
    series_line = ''
    if series:
        # Series pages exist only in the two chrome languages, so a Dutch book
        # links back to the series page of the chrome the reader is in.
        sd = series['i18n'].get(lang) or series['i18n'].get(ui) or series['i18n'].get('en') or {}
        series_line = (f'<a class="book-series-link" href="{series_path(series["id"], ui)}">'
                       f'{esc(sd.get("title", series["id"]))}</a>')

    return f"""
        <article class="section book-detail">
            <div class="container book-grid">
                <aside class="book-aside">
                    <div class="cover-frame large rv"><img src="/{esc(cover)}" alt="{esc(bdata['title'])}"></div>
                    <div class="book-aside-actions rv" data-d="1">
                        {excerpt_link}
                    </div>
                    <div class="book-editions rv" data-d="2">
                        <p class="aside-label">{esc(s['editions'])}</p>
                        <div class="lang-pills">{editions}</div>
                    </div>
                </aside>

                <div class="book-main">
                    {f'<p class="book-over rv">{series_line}</p>' if series_line else ''}
                    <h1 class="book-title rv" data-d="1">{esc(bdata['title'])}</h1>
                    {f'<p class="book-genre rv" data-d="1">{esc(bdata["genre"])}</p>' if bdata.get('genre') else ''}
                    <div class="deco-rule left rv" data-d="1">{RULE_SVG}</div>
                    {f'<div class="rv" data-d="2">{render_book_facts(data, book, lang, series)}</div>'}
                    <div class="rv" data-d="2">
                        <h2 class="sub-head">{esc(s['synopsis'])}</h2>
                        <div class="synopsis prose">{synopsis_html}</div>
                    </div>
                    <div class="rv" data-d="2">{render_lead_magnet(bdata, lang)}</div>
                    <div class="rv" data-d="2">{render_direct_sale(bdata, lang)}</div>
                    <div class="rv" data-d="3">
                        <h2 class="sub-head">{esc(s['available_on'])}</h2>
                        <div class="buy-links">{buy_html}</div>
                    </div>
                </div>
            </div>
        </article>"""


def render_excerpt_page(book, lang, excerpt_html):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    bdata = book['i18n'].get(lang) or book['i18n'].get('en')
    return f"""
        <div class="reading-page">
            <div class="reading-container">
                <a href="{book_path(book['id'], lang)}" class="back-link">&#8592; {esc(s['back'])}</a>
                <p class="reading-over rv">{esc(s['excerpt_from'])}</p>
                <h1 class="reading-title rv" data-d="1">{esc(bdata['title'])}</h1>
                <div class="deco-rule rv" data-d="1">{RULE_SVG}</div>
                <article class="prose rv" data-d="2">{excerpt_html}</article>
                {render_lead_magnet(bdata, lang)}
            </div>
        </div>"""


def render_news_list_page(lang, articles):
    """articles: list of dicts {slug, title, date_fmt, author, excerpt, content_html}, newest first."""
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    if not articles:
        items = f'<p class="empty-note rv">{esc(s["no_news"])}</p>'
    else:
        items = ''
        for i, a in enumerate(articles):
            items += f"""<article class="news-item rv" data-d="{min(i + 1, 3)}">
                <p class="news-meta"><time>{esc(a['date_fmt'])}</time><span class="sep">&#183;</span><span>{esc(s['by'])} {esc(a['author'])}</span></p>
                <h2 class="news-item-title"><a href="{news_article_path(a['slug'], lang)}">{esc(a['title'])}</a></h2>
                <p class="news-excerpt">{esc(a['excerpt'])}</p>
                <a href="{news_article_path(a['slug'], lang)}" class="link-arrow">{esc(s['read_more'])}</a>
            </article>"""
    return f"""
        {page_header(s['news_and_updates'], s['sec_news_over'])}
        <section class="section">
            <div class="container narrow"><div class="news-list">{items}</div></div>
        </section>"""


def render_news_article_page(lang, article, content_html):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    return f"""
        <div class="reading-page">
            <div class="reading-container">
                <a href="{news_path(lang)}" class="back-link">&#8592; {esc(s['back'])}</a>
                <p class="news-meta rv"><time>{esc(article['date_fmt'])}</time><span class="sep">&#183;</span><span>{esc(s['by'])} {esc(article['author'])}</span></p>
                <h1 class="reading-title rv" data-d="1">{esc(article['title'])}</h1>
                <div class="deco-rule rv" data-d="1">{RULE_SVG}</div>
                <article class="prose rv" data-d="2">{content_html}</article>
            </div>
        </div>"""


def render_about_page(data, lang, bio_html, author_photo):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    name = author_name(data, lang)
    return f"""
        {page_header(s['about_the_author'], s['sec_author_over'])}
        <section class="section">
            <div class="container about-grid">
                <div class="about-figure rv">
                    <span class="portrait-frame large"><img src="/{esc(author_photo)}" alt="{esc(name)}"></span>
                </div>
                <div class="about-body rv" data-d="1">
                    <div class="prose bio">{bio_html}</div>
                    <div class="about-actions">
                        <a href="{library_path(lang)}" class="btn btn-solid">{esc(s['explore_library'])}</a>
                        <a href="{contact_path(lang)}" class="btn">{esc(s['get_in_touch'])}</a>
                    </div>
                </div>
            </div>
        </section>"""


def render_contact_page(lang):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    return f"""
        {page_header(s['get_in_touch'], s['sec_contact_over'], esc(s['contact_intro']))}
        <section class="section">
            <div class="container narrow">
                <form id="contact-form" class="contact-form rv">
                    <div class="form-group">
                        <label for="name">{esc(s['name'])}</label>
                        <input type="text" id="name" name="name" required>
                    </div>
                    <div class="form-group">
                        <label for="email">{esc(s['email'])}</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="message">{esc(s['message'])}</label>
                        <textarea id="message" name="message" rows="7" required></textarea>
                    </div>
                    <button type="submit" class="btn btn-solid">{esc(s['send_message'])}</button>
                    <div id="form-status" role="status"></div>
                </form>
                <p class="contact-direct">{esc(s['or_write_to'])} <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
            </div>
        </section>"""


def render_privacy_page(lang, title, body_html):
    ui = ui_lang_of(lang)
    return f"""
        {page_header(title, UI_STRINGS[ui]['legal'])}
        <section class="section">
            <div class="container narrow"><div class="prose rv">{body_html}</div></div>
        </section>"""


def store_row(entry, ui):
    """One purchasable edition: cover, what it is, and the way to buy it."""
    lang = entry['lang']
    book_url = book_path(entry['id'], lang)
    cover = entry.get('cover') or 'images/common/cover-placeholder.jpg'
    overline = ' · '.join(filter(None, [entry.get('series'), LANG_NAMES[ui].get(lang, lang.upper())]))
    genre = f'<p class="store-genre">{esc(entry["genre"])}</p>' if entry.get('genre') else ''
    teaser = f'<p class="store-teaser">{esc(entry["teaser"])}</p>' if entry.get('teaser') else ''
    excerpt = (f'<a class="store-excerpt link-arrow" href="{excerpt_path(entry["id"], lang)}">'
               f'{esc(UI_STRINGS[ui]["read_excerpt_short"])}</a>') if entry.get('has_excerpt') else ''
    return f"""
            <article class="store-item rv">
                <a class="store-cover" href="{book_url}"><span class="cover-frame"><img src="/{esc(cover)}" alt="{esc(entry['title'])}" loading="lazy"></span></a>
                <div class="store-body">
                    <p class="store-overline">{esc(overline)}</p>
                    <h3 class="store-title"><a href="{book_url}">{esc(entry['title'])}</a></h3>
                    {genre}
                    {teaser}
                </div>
                <div class="store-buy">
                    <span class="store-price">{esc(format_price(entry['price'], lang))}</span>
                    <a class="btn btn-solid" href="{esc(entry['url'])}" target="_blank" rel="noopener">{esc(BUY_DIRECT_SHORT[ui])}</a>
                    {excerpt}
                </div>
            </article>"""


def render_store_page(entries, lang):
    """The bookshop: every edition the author sells directly, grouped by language
    only once there is more than one — a lone section heading looks like a mistake."""
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    langs = [l for l in ALL_LANGS if any(e['lang'] == l for e in entries)]
    sections = []
    for l in langs:
        rows = ''.join(store_row(e, ui) for e in entries if e['lang'] == l)
        head = (f'<h2 class="sub-head">{esc(s["editions_in"])} {esc(LANG_NAMES[ui][l])}</h2>'
                if len(langs) > 1 else '')
        sections.append(head + f'<div class="store-list">{rows}</div>')
    terms_link = f'<a href="{terms_path(ui)}">{esc(s["terms_of_service"])}</a>'
    note = esc(s['store_note']).replace('{terms}', terms_link)
    return f"""
        {page_header(s['store'], s['sec_shop_over'], esc(s['store_intro']))}
        <section class="section">
            <div class="container">
                {''.join(sections)}
                <p class="store-note rv">{note}</p>
            </div>
        </section>"""


def render_store_band(entries, lang):
    """Homepage strip pointing at the bookshop. Silent when nothing is on sale."""
    if not entries:
        return ''
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    covers = ''.join(
        f'<span class="cover-frame"><img src="/{esc(e.get("cover") or "images/common/cover-placeholder.jpg")}" alt="{esc(e["title"])}" loading="lazy"></span>'
        for e in entries[:3]
    )
    return f"""
        <section class="section store-band-section">
            <div class="container store-band">
                <div class="store-band-covers rv">{covers}</div>
                <div class="store-band-text">
                    {section_head(s['sec_shop_over'], s['store_heading'])}
                    <p class="rv" data-d="1">{esc(s['store_intro'])}</p>
                    <div class="rv" data-d="2"><a class="btn btn-solid" href="{store_path(ui)}">{esc(s['store_cta'])}</a></div>
                </div>
            </div>
        </section>"""


def render_terms_page(lang, title, body_html):
    ui = ui_lang_of(lang)
    return f"""
        {page_header(title, UI_STRINGS[ui]['legal'])}
        <section class="section">
            <div class="container narrow"><div class="prose rv">{body_html}</div></div>
        </section>"""


def render_404_page(lang='en'):
    ui = ui_lang_of(lang)
    s = UI_STRINGS[ui]
    return f"""
        <section class="section error-page">
            <div class="container narrow center">
                <p class="ph-over">404</p>
                <h1 class="ph-title">{esc(s['not_found'])}</h1>
                <div class="deco-rule">{RULE_SVG}</div>
                <p class="ph-lead">{esc(s['not_found_lead'])}</p>
                <div class="hero-cta">
                    <a href="{home_path(ui)}" class="btn btn-solid">{esc(s['back_home'])}</a>
                    <a href="{library_path(ui)}" class="btn">{esc(s['the_library'])}</a>
                </div>
            </div>
        </section>"""
