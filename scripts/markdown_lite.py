"""
Minimal Markdown -> HTML converter covering the subset actually used in this
project's book excerpts and news posts: headers, bold/italic, paragraphs,
and simple bullet lists. No external dependency needed at build time.
"""
import re
import html as _html


def parse_frontmatter(md_text):
    """Split '---\\nkey: value\\n---\\ncontent' into (metadata dict, content str)."""
    parts = md_text.split('---')
    if len(parts) >= 3:
        metadata = {}
        for line in parts[1].split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue
            key, _, value = line.partition(':')
            metadata[key.strip()] = value.strip().strip('"\'')
        content = '---'.join(parts[2:]).strip()
        return metadata, content
    return {}, md_text


_INLINE_CODE = re.compile(r'`([^`]+)`')
_BOLD = re.compile(r'\*\*(.+?)\*\*|__(.+?)__')
_ITALIC = re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.+?)(?<!_)_(?!_)')
_HEADER = re.compile(r'^(#{1,6})\s+(.*)$')
_BULLET = re.compile(r'^[-*]\s+(.*)$')


def _inline(text):
    text = _html.escape(text, quote=False)
    text = _INLINE_CODE.sub(lambda m: f'<code>{m.group(1)}</code>', text)
    text = _BOLD.sub(lambda m: f'<strong>{m.group(1) or m.group(2)}</strong>', text)
    text = _ITALIC.sub(lambda m: f'<em>{m.group(1) or m.group(2)}</em>', text)
    return text


def to_html(md_text):
    if not md_text:
        return ''
    lines = md_text.replace('\r\n', '\n').split('\n')
    blocks = []
    para = []
    list_items = []

    def flush_para():
        # The manuscripts separate paragraphs with a single newline, not a blank
        # line, so every line in a block is its own paragraph. Joining them with
        # <br> instead would print a chapter as one unbroken wall of text.
        for line in para:
            # A lone short line in capitals is a chapter marker, not prose.
            # It gets its own class so the stylesheet can set it apart.
            cls = ' class="prose-label"' if _is_section_heading(line) else ''
            blocks.append(f'<p{cls}>{_inline(line)}</p>')
        para.clear()

    def flush_list():
        if list_items:
            blocks.append('<ul>' + ''.join(f'<li>{_inline(i)}</li>' for i in list_items) + '</ul>')
            list_items.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            flush_para()
            flush_list()
            continue
        h = _HEADER.match(line)
        if h:
            flush_para()
            flush_list()
            level = len(h.group(1))
            blocks.append(f'<h{level}>{_inline(h.group(2))}</h{level}>')
            continue
        b = _BULLET.match(line)
        if b:
            flush_para()
            list_items.append(b.group(1))
            continue
        flush_list()
        para.append(line)

    flush_para()
    flush_list()
    return '\n'.join(blocks)


def bio_html(text):
    """The bio as real paragraphs. The file's first line repeats the page's own
    heading, so it is dropped: a title printed twice reads like a mistake."""
    if not text:
        return ''
    chunks = [c.strip() for c in re.split(r'\n\s*\n', text.strip()) if c.strip()]
    if chunks and '\n' not in chunks[0] and len(chunks[0]) <= 70 \
            and not chunks[0].rstrip().endswith(('.', '!', '?', ':')):
        chunks = chunks[1:]
    return ''.join(
        '<p>' + _html.escape(c).replace('\n', '<br>') + '</p>' for c in chunks)


def synopsis_html(text):
    """Matches original renderBookDetail: split on any run of newlines, each line -> its own <p>."""
    if not text:
        return ''
    lines = [l.strip() for l in re.split(r'\n+', text) if l.strip()]
    return ''.join(f'<p>{_html.escape(l)}</p>' for l in lines)


def _is_section_heading(chunk):
    """A short single line written in capitals is a section heading, not a paragraph."""
    return chr(10) not in chunk and len(chunk) <= 80 and chunk == chunk.upper()


def privacy_html(text):
    """Legal text pages (privacy policy, terms of service): split on blank lines.
    First chunk is the title (h1); capitalised one-liners become section headings."""
    if not text:
        return '', ''
    chunks = text.split('\n\n')
    title = chunks[0].strip()
    parts = []
    for p in (c.strip() for c in chunks[1:]):
        if not p:
            continue
        if _is_section_heading(p):
            parts.append(f'<h2>{_html.escape(p)}</h2>')
        else:
            parts.append(f'<p>{_html.escape(p).replace(chr(10), "<br>")}</p>')
    return title, ''.join(parts)
