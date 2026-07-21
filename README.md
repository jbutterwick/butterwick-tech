# butterwick.tech

My professional portfolio and résumé live here. Zola renders the site, Sass provides the site-specific visual system, and Tailwind CSS builds the polished web résumé stylesheet.

## Build

```bash
npm install
npm run build:site
```

The generated site is written to `public/`.

## Local development

```bash
npm run build:resume-css
npm run serve
```

For Tailwind watch mode while editing the polished résumé:

```bash
npx tailwindcss -i ./static/input.css -o ./static/output.css --watch
```

## Verify the résumé

```bash
npm run check:resume
```

## Verify the website

```bash
npm run check:site
```

The site verifier checks generated metadata, canonical URL equality, heading structure, accessible link names, local assets, Open Graph images, external page resources, internal links, and required homepage content. Run both website and résumé checks with:

```bash
npm run check
```

Résumé content lives in `data/resume.toml`. The polished version is available at `/resume/`; the one-column application version is available at `/resume/application/`; and `/resume.html` remains as a compatibility alias.

Generate the downloadable application PDF with:

```bash
python3 scripts/export_resume_pdf.py
```

For browser diagnostics after starting the local server:

```bash
npx --yes lighthouse http://127.0.0.1:1111/ --quiet --chrome-flags='--headless'
```