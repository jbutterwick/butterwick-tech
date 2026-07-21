# butterwick.tech

My personal website and résumé live here. Zola renders the site, and Tailwind CSS builds the polished web résumé stylesheet.

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

Résumé content lives in `data/resume.toml`. The polished version is available at `/resume/`; the one-column application version is available at `/resume/application/`; and `/resume.html` remains as a compatibility alias.

Generate the downloadable application PDF with:

```bash
python3 scripts/export_resume_pdf.py
```