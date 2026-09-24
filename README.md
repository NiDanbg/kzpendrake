# K.Z. Pendrake — kzpendrake.com

Statically generated author site (no client-side router, real HTML per page/language).

Visual identity: navy and brass, set like a book. Cormorant for what a reader reads,
Jost for what a reader clicks, one accent colour, cut corners on buttons only.
The homepage hero stands the featured covers inside two CSS orbits; no canvas, no library.
The design follows the taste-skill audit (github.com/leonxlnx/taste-skill, installed locally, not in this repo).

## Local development

```
pip install -r requirements.txt
python scripts/build.py                     # generates dist/
python -m http.server 8070 --directory dist # http://localhost:8070
```

Or run `start.bat`, which builds, serves on 8070 and opens the admin panel on 8080.

## Editing content

```
python admin_server.py        # http://localhost:8080/admin
```

Edits go straight to `data.js` / `synopsis/` / `books/` / `news/` / `images/`. Use the admin panel's
**Build** tab to regenerate `dist/` for local preview, and **Publish** to commit and push.

## Deployment

Pushing to `main` runs `.github/workflows/deploy.yml`, which builds the site with
`scripts/build.py` and publishes `dist/` via GitHub Pages (Pages source: **GitHub Actions**).
The domain comes from the `CNAME` file that the build writes into `dist/`.

## Layout

| Path | What it holds |
| --- | --- |
| `data.js` | books, series, featured list, author meta — the one source of structure |
| `synopsis/<lang>/` | book synopses, plus `about.txt`, `privacy-policy.txt`, `terms-of-service.txt` |
| `books/<lang>/` | chapter excerpts in Markdown |
| `news/<lang>/` | news posts in Markdown, ordered by `news/index.json` |
| `images/<lang>/` | covers; `images/common/` holds the portrait, retailer logos and favicons |
| `scripts/render.py` | every HTML template — the whole visual layer lives here |
| `style.css` | the design system: colour tokens, type scale, components |
| `assets/site.js` | mobile menu, search, cookie banner, contact form, scroll reveals |

Interface languages: English and Bulgarian. Book languages: bg, en, de, fr, it, nl, es, pt, se.

## Still to fill in

- `GA_ID` in `scripts/render.py` is empty; set a GA4 measurement id to switch analytics on.
- `images/common/author-kzpendrake.jpg` is 166px wide — it needs a larger version.
- Bulgarian synopses exist only for `about` and the legal pages; books fall back to English.
