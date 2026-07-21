# Résumé Structure and Application Version Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Preserve the visually distinctive web résumé while adding a machine-readable application résumé, shared structured data, readable print sizing, a value-proposition profile structure, selective skills, and consistent labels/contact metadata—without rewriting the existing experience bullets.

**Architecture:** Move résumé facts into one `data/resume.toml` source and render two standalone Zola pages from shared Tera macros. `/resume/` remains the polished web presentation; `/resume/application/` is a single-column, text-first, print-ready application version. Preserve the old `/resume.html` URL with a Zola alias, and generate a downloadable PDF from the application page only after its plain-text order has been verified.

**Tech Stack:** Zola 0.22.x, Tera templates, Tailwind CSS 4 for the web résumé, a small hand-authored print stylesheet for the application résumé, headless Chrome, `pdftotext`/Poppler for extraction checks.

---

## Scope Mapping

This plan implements the requested résumé recommendations:

1. **Replace the current profile layout with a value-proposition structure** — structurally now, while preserving existing wording until a later copy pass.
2. **Provide a one-column application version** alongside the styled web version.
3. **Stop forcing the résumé onto one page** — remove print zoom and allow one or two readable pages.
5. **Make Skills selective and grouped** — store all known skills but render only approved `featured` skills.
7. **Standardize details** — title/company/date/location/contact presentation and valid link targets.

Explicitly out of scope for this pass:

- Rewriting individual experience bullets.
- Inventing new metrics or achievements.
- Finalizing the exact professional-summary prose.
- Changing the underlying employment dates or facts without user approval.
- Rewriting the Education credential until its exact award/date are confirmed.

## Current Context and Constraints

- Current source: `static/resume.html` and `static/input.css`; `static/output.css` is generated.
- Current route: `/resume.html`.
- The current PDF is one A4 page but plain-text extraction interleaves Contact, Skills, Education, and Experience.
- The current print `zoom: 0.93` reduces 12px content to approximately 8.37pt.
- The displayed phone number and `tel:` target disagree at `static/resume.html:229-232`.
- The current GitHub Actions workflow points to nonexistent/stale paths and uses unpinned or beta actions.
- `public/` is generated output and must not be edited by hand.
- Do not commit unless the user explicitly requests it.

## Content-Freeze Rules for This Structural Pass

1. Copy all current role descriptions and experience bullets verbatim into `data/resume.toml`.
2. Do not “improve” wording during migration.
3. Split the existing Profile facts into two data groups without rewriting them:
   - `summary_seed`: the two existing professional-positioning statements.
   - `logistics`: location, work authorization/citizenship, and time-zone availability.
4. Add a clearly marked `summary_status = "needs-copy-review"` field so a later copy pass is explicit.
5. Store all existing skills, but render only those marked `featured = true`; changing those flags is not destructive.

## Proposed Data Shape

Create `data/resume.toml` with these top-level groups:

```toml
[identity]
name = "Jordan Butterwick"
professional_title = "Senior Software Engineer"
email = "jordan@butterwick.tech"
phone_display = "+1-(587)-830-5974"
phone_href = "+15878305974"
location = "Airdrie, AB"
website = "https://butterwick.tech"
github = "https://github.com/jbutterwick"
linkedin = "https://www.linkedin.com/in/jbutterwick/"

[profile]
summary_status = "needs-copy-review"
summary_seed = [
  "Polyglot full stack engineer seeking permanent role.",
  "Experienced in Data, Backend, and ML/AI Engineering roles.",
]
logistics = [
  "Canadian Citizen based in Airdrie, Alberta",
  "Located in MST, available from PST to EST.",
]

[[experience]]
company = "Tresco Consoles"
title = "Senior Software Engineer"
start = "2026-05"
end = "present"
location = "Calgary, AB"
remote = false
bullets = [
  # Copy the existing bullets verbatim during migration.
]

[[skills]]
name = "Python"
category = "Languages"
featured = true
```

Use analogous entries for all current experience, skills, and education facts. Keep machine-sortable dates separate from display formatting.

## Application Résumé Information Order

The application template must use this DOM and extraction order:

1. Name and professional title.
2. Plain-text contact links and location.
3. Professional summary block.
4. Professional Experience.
5. Selected Technical Skills.
6. Education.

Do not use CSS Grid columns, tables, text boxes, icon fonts, decorative glyph bullets, or header/footer content for résumé facts.

---

### Task 1: Establish Baseline Fixtures and Route Expectations

**Objective:** Capture the current facts and define the required outputs before moving content.

**Files:**
- Create: `scripts/verify_resume.py`
- Read only: `static/resume.html`
- Read only: `static/input.css`

**Steps:**

1. Create a standard-library Python verifier that accepts `public/resume/index.html`, `public/resume/application/index.html`, and optionally a PDF text file.
2. Add assertions for:
   - exactly four experience roles;
   - exactly twelve experience bullets;
   - each known company name appears once per rendered version;
   - application HTML contains one `<main>` and one `<h1>`;
   - application contact content appears before Experience;
   - Skills and Education appear after Experience;
   - no `<table>`, `.grid`, icon-font `<i>`, or external script in the application page;
   - `tel:+15878305974` is present;
   - old route alias output exists after the Zola build.
3. Run the verifier against the current build and record expected failures for the new pages and extraction order.
4. Do not modify résumé content yet.

**Verification:**

Run:

```bash
zola build
python3 scripts/verify_resume.py public
```

Expected before implementation: failure because `/resume/` and `/resume/application/` do not exist.

### Task 2: Create the Shared Résumé Data Source

**Objective:** Move all résumé facts to one structured source without changing prose.

**Files:**
- Create: `data/resume.toml`
- Modify later: `static/resume.html` (source will be retired after parity)

**Steps:**

1. Transcribe identity, contact, profile, experience, skills, and education into `data/resume.toml`.
2. Preserve all current experience bullets verbatim.
3. Store dates as `start`, `end`, and optional `display_date` fields so both templates use the same values.
4. Store `location` and `remote` separately.
5. Store `phone_display` and normalized `phone_href` separately.
6. Give each skill a category and `featured` flag.
7. Extend `scripts/verify_resume.py` to parse TOML with `tomllib` and assert source counts before rendering.

**Initial featured-skill rule:** Mark a skill featured only when it is evidenced by current experience bullets or is intentionally retained for target-role positioning. Keep nonfeatured skills in the data file so selection is reversible.

**User review checkpoint:** Before pruning the rendered list, show the proposed `featured = true` set for approval. Do not silently remove Rust, Scala, Java, C#, or Haskell from the source data.

**Verification:**

```bash
python3 scripts/verify_resume.py --data-only data/resume.toml
```

Expected: source counts and required fields pass.

### Task 3: Add Shared Tera Résumé Macros

**Objective:** Ensure both presentations render the same facts while allowing different layouts.

**Files:**
- Create: `templates/macros/resume.html`

**Steps:**

1. Add macros for:
   - contact list;
   - profile/summary;
   - experience roles;
   - featured skill groups;
   - education.
2. Keep semantic elements in macros: `<address>`, `<section>`, `<h2>`, `<article>`, `<ul>`, and `<time>`.
3. Pass presentation-specific class names into macros or wrap macro output; do not duplicate content loops in two templates.
4. Render ordinary text bullets with CSS list markers. Do not output the decorative `›` character in application content.
5. Render full company names and full job titles.

**Verification:** Build a temporary template fixture if needed, then run `zola build`; expected: no Tera errors.

### Task 4: Create the Single-Column Application Page

**Objective:** Add the ATS-oriented HTML application résumé with normal document flow.

**Files:**
- Create: `content/resume-application.md`
- Create: `templates/resume-application.html`
- Create: `static/resume-application.css`

**Front matter:**

```toml
+++
title = "Jordan Butterwick — Application Résumé"
description = "Application résumé for Jordan Butterwick, Senior Software Engineer."
path = "resume/application"
template = "resume-application.html"
in_search_index = false

[extra]
robots = "noindex,follow"
+++
```

**Steps:**

1. Load `data/resume.toml` from the template.
2. Render the required information order with shared macros.
3. Add visible links to:
   - polished web résumé;
   - print/save as PDF;
   - downloadable PDF once generated.
4. Use a system font stack and no external fonts, scripts, or icon libraries.
5. Add print CSS with:
   - A4 paper;
   - 12–14mm margins;
   - 10.5–11pt body text;
   - 1.25–1.4 line height;
   - no `zoom` or `transform: scale`;
   - `break-inside: avoid` for each role where practical;
   - normal wrapping for URLs and long words;
   - hidden screen-only controls in print.
6. Allow the document to occupy two pages naturally.
7. Keep name/contact in the document body, not CSS running headers or footers.

**Verification:**

```bash
zola build
python3 scripts/verify_resume.py public
```

Expected: application structure passes; PDF checks remain pending.

### Task 5: Migrate the Polished Web Résumé to Zola

**Objective:** Preserve the current visual résumé while making it data-driven and mobile-safe.

**Files:**
- Create: `content/resume.md`
- Create: `templates/resume-web.html`
- Modify: `static/input.css`
- Remove after parity: `static/resume.html`
- Keep generated: `static/output.css`

**Front matter:**

```toml
+++
title = "Jordan Butterwick — Résumé"
description = "Jordan Butterwick, Senior Software Engineer specializing in backend, data, cloud, and ML systems."
path = "resume"
aliases = ["resume.html"]
template = "resume-web.html"
+++
```

**Steps:**

1. Recreate the existing web layout from shared macros and data.
2. Keep the distinctive green accent, Albert Sans body, and display name treatment for now.
3. Replace the current Profile bullet grid with:
   - professional title beneath the name;
   - full-width summary block using `summary_seed` temporarily;
   - compact logistics line beneath it.
4. Add a prominent “Application version” action and retain “Save as PDF” for the web presentation.
5. Remove the web print zoom from `static/input.css`; web printing may be multi-page.
6. Keep the two-column desktop composition only for the pretty web version.
7. At widths below 768px, render one column, place controls in normal flow, and set `min-width: 0` on grid/flex children.
8. Ensure company names, URLs, and bullet text wrap without horizontal scrolling at 320px.
9. Build Tailwind output using the actual paths:

```bash
npx @tailwindcss/cli -i ./static/input.css -o ./static/output.css
```

10. Build Zola, confirm `/resume/`, `/resume/application/`, and the `/resume.html` alias.
11. Remove `static/resume.html` only after rendered-content parity is verified.

**Verification:** Compare current and new desktop screenshots before retiring the static source. Exact pixel parity is not required; factual parity is.

### Task 6: Implement Selective, Grouped Skills

**Objective:** Replace the icon-heavy inventory with a concise, evidence-oriented skills section.

**Files:**
- Modify: `data/resume.toml`
- Modify: `templates/macros/resume.html`
- Modify: `templates/resume-web.html`
- Modify: `templates/resume-application.html`

**Steps:**

1. Render only `featured = true` skills.
2. Group them under conventional labels such as:
   - Languages;
   - Backend & Data;
   - Cloud & Platform;
   - Observability / ML & AI, if approved.
3. Do not render Devicon or Font Awesome glyphs in the application version.
4. In the web version, prefer text chips without icon-font dependencies.
5. Keep nonfeatured skills in `data/resume.toml` for later target-specific variants.
6. Assert a reasonable upper bound in `scripts/verify_resume.py` so the application section cannot silently return to a long inventory.

**Acceptance rule:** The Skills section should be scannable in under ten seconds and should not visually compete with Experience.

### Task 7: Standardize Presentation Details Without Rewriting Bullets

**Objective:** Normalize typography, labels, dates, locations, and links across both versions.

**Files:**
- Modify: `data/resume.toml`
- Modify: `templates/macros/resume.html`
- Modify: `templates/resume-web.html`
- Modify: `templates/resume-application.html`

**Steps:**

1. Use `Title — Company` rather than `Title @ Company`.
2. Format all locations as `City, Province` or `Remote, Canada`.
3. Format all date ranges with one style and en dashes.
4. Use full job titles and company capitalization from source data.
5. Put `Senior Software Engineer` directly under the name.
6. Fix phone, GitHub, LinkedIn, email, and website link targets.
7. Use readable visible URLs in the application version.
8. Remove obsolete `meta keywords` and `X-UA-Compatible` tags.
9. Preserve Education wording but add `credential_status = "needs-confirmation"` so the exact award and graduation date remain an explicit follow-up.

**Verification:** Source-data and rendered-label assertions pass; manual spot-check all links.

### Task 8: Add PDF Export and Extraction Verification

**Objective:** Produce a downloadable application PDF and prove its reading order.

**Files:**
- Create: `scripts/export_resume_pdf.sh`
- Create/generated: `static/downloads/Jordan-Butterwick-Resume.pdf`
- Modify: `scripts/verify_resume.py`
- Modify: `README.md`

**Steps:**

1. Make the export script accept `CHROME_BIN`, defaulting to common macOS/Linux Chrome paths.
2. Build the site, serve `public/` locally, and print `/resume/application/` with headless Chrome.
3. Write the PDF to `static/downloads/Jordan-Butterwick-Resume.pdf`.
4. Run `pdftotext` into a temporary file.
5. Extend verification to assert this text order:
   - Jordan Butterwick;
   - Senior Software Engineer;
   - contact details;
   - Profile/Summary;
   - Experience roles in reverse chronology;
   - Skills;
   - Education.
6. Assert the PDF is one or two A4 pages and comfortably under 2.5MB.
7. Rebuild Zola so the generated PDF is copied into `public/downloads/`.
8. Update both résumé pages to link to the stable PDF path.
9. Document the required regeneration command in `README.md`.

**Verification:**

```bash
./scripts/export_resume_pdf.sh
pdfinfo static/downloads/Jordan-Butterwick-Resume.pdf
pdftotext static/downloads/Jordan-Butterwick-Resume.pdf /tmp/resume.txt
python3 scripts/verify_resume.py public --pdf-text /tmp/resume.txt
```

Expected: one or two A4 pages, correct plain-text order, all assertions pass.

### Task 9: Repair the Résumé Workflow

**Objective:** Replace the stale workflow with a reproducible build/export check.

**Files:**
- Modify: `.github/workflows/main.yml`

**Steps:**

1. Trigger on changes to:
   - `data/resume.toml`;
   - résumé content/templates/macros/styles;
   - export/verification scripts.
2. Use stable action versions; do not use `@master` or beta checkout actions.
3. Install the repository’s pinned Zola version and Chrome/Chromium.
4. Build Tailwind CSS and Zola.
5. Export the application PDF.
6. Install Poppler and run the extraction verifier.
7. Upload the PDF as a workflow artifact.
8. Do not auto-tag or publish a GitHub Release unless the user explicitly asks to preserve release behavior.

**Expected CI result:** Build and extraction checks pass without referring to `oldsrc/pages/resume.html` or `../../content/resume.html`.

### Task 10: Final Visual, Mobile, and Extraction QA

**Objective:** Verify both résumé presentations end to end.

**Files:** No new source files unless fixes are required.

**Automated checks:**

```bash
npx @tailwindcss/cli -i ./static/input.css -o ./static/output.css
zola build
python3 scripts/verify_resume.py public
./scripts/export_resume_pdf.sh
```

**Manual checks:**

1. Web résumé at 1280×900, 768×1024, 390×844, and 320×568.
2. Application résumé at the same widths.
3. No horizontal scrolling.
4. All controls visible and keyboard reachable.
5. Print preview at 100% scale with no browser header/footer.
6. Body text remains at least 10pt.
7. No split role heading stranded at a page bottom.
8. PDF links are clickable.
9. Plain-text extraction is top-to-bottom and contains no icon-font garbage.
10. `/resume.html` redirects to or aliases `/resume/` successfully.

## Files Likely to Change

**Create**

- `data/resume.toml`
- `content/resume.md`
- `content/resume-application.md`
- `templates/resume-web.html`
- `templates/resume-application.html`
- `templates/macros/resume.html`
- `static/resume-application.css`
- `static/downloads/Jordan-Butterwick-Resume.pdf`
- `scripts/verify_resume.py`
- `scripts/export_resume_pdf.sh`

**Modify**

- `static/input.css`
- `static/output.css` (generated)
- `config.toml`
- `.github/workflows/main.yml`
- `README.md`

**Remove after verified migration**

- `static/resume.html`

**Never hand-edit**

- `public/**`

## Risks and Tradeoffs

- A shared data model adds initial migration work but prevents web/application content drift.
- Zola aliases must be verified before deleting `static/resume.html`; otherwise existing inbound links may break.
- ATS behavior differs by vendor. The acceptance test is correct text order and conservative markup, not a guarantee for every system.
- Two readable pages are preferable to one compressed page; page count is not a failure unless a target employer specifies one page.
- A committed PDF can become stale. The export command and CI artifact make regeneration explicit, but the implementation must update the PDF whenever résumé data changes.
- Final summary wording, skill flags, and Education credential need user review; structural work should not guess them.

## Completion Criteria

- One source of truth renders both versions.
- `/resume/` is polished and mobile-safe.
- `/resume/application/` is one-column and ATS-oriented.
- `/resume.html` remains functional via alias/redirect.
- Experience bullets remain textually unchanged.
- Skills are grouped and filtered by explicit flags.
- Dates, locations, labels, and links are consistent.
- Application print uses ≥10pt text with no zoom and may use up to two pages.
- The generated PDF extracts in correct reading order.
- Build and verifier pass locally and in CI.
- No commits are created unless the user requests them.
