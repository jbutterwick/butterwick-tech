# Professional Portfolio Website Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Reframe butterwick.tech as a professional senior-engineer portfolio with clear positioning, current content, a substantive About page, correct semantic structure, responsive behavior, a restrained visual system, accessible interactions, faster delivery, and complete search/social metadata.

**Architecture:** Keep Zola and the Prairie theme, but add site-specific root template overrides and a small site stylesheet rather than coupling all content decisions to generic theme templates. Centralize identity/positioning in `config.toml`, let each page supply a unique description, use a single page-owned H1, replace external icon/font dependencies where practical, and add a standard-library post-build verifier for metadata, headings, links, and assets.

**Tech Stack:** Zola 0.22.x, Tera, Sass, semantic HTML, inline SVG icons, Python standard-library verification, Lighthouse/headless Chrome for diagnostics.

---

## Scope Mapping

This plan implements the requested website recommendations:

1. **Make the homepage immediately explain who Jordan is and what outcomes he creates.**
2. **Remove employment-status contradictions and stale “looking for work” copy.**
5. **Remove duplicate titles and repair heading/link structure.**
6. **Expand the sparse About page into a credible professional narrative.**
7. **Fix mobile navigation and horizontal clipping.**
8. **Apply a restrained editorial-technical visual direction.**
9. **Complete accessibility, performance, SEO, and social-metadata hygiene.**

Explicitly out of scope for this pass because those recommendations were not selected:

- Repairing or replacing the Frishy live project/certificate.
- Rewriting existing project pages into full engineering case studies.
- Adding new project screenshots, confidential work case studies, or outcome metrics not already verified.
- Rewriting exact résumé bullets; the separate résumé plan owns résumé structure and routes.
- Building a contact form, analytics platform, CMS, or JavaScript framework.

## Current Context and Constraints

- The site uses Zola with the local `prairie` theme.
- `config.toml:45` currently says `homepage of butterwick.tech`.
- `content/about/index.md:7` and `content/now/index.md:7` contradict the current role in the résumé.
- The site header is an H1 on every page, while content/templates add additional H1s.
- Project/blog Markdown files repeat page titles as H1s.
- Page-listing macros wrap summaries in links even when summary Markdown contains links, producing invalid nested anchors and unnamed links.
- Mobile navigation uses floated list items and overflows the viewport in the 390px screenshot.
- The About and Now templates reference a nonexistent `/about/me.jpg` Open Graph image.
- 13 of 15 built pages currently use the same generic meta description; all 15 lack canonical links.
- The homepage’s muted metadata/link colors fail normal-text contrast.
- The bison image is described as “A misty forest.”
- `public/` is generated and must not be edited directly.
- Do not commit unless the user explicitly requests it.

## Content and Design Assumptions

1. Use only claims already verified in the current résumé: senior software engineer, backend/data/ML/cloud systems, 15M users, billions of records, millions of events, and 75% AWS savings.
2. Do not imply that Jordan is currently seeking work.
3. The homepage should be useful to a recruiter or engineering manager in the first viewport.
4. Preserve personality—gardening, fishing, writing, and the bison photograph—but subordinate it to professional positioning.
5. Use a dark editorial-technical design: restrained color, serif display type, sans-serif body type, real content, no gradients/glass/parallax/cursor effects.
6. `/resume/` will be the canonical résumé route after the résumé plan; `/resume.html` remains an alias.

## Proposed Homepage Information Architecture

1. **Hero**
   - Jordan Butterwick.
   - Senior Software Engineer.
   - One concise outcome-oriented positioning sentence.
   - Primary actions: View work, Résumé, Contact.
2. **Impact strip**
   - 15M users scaled.
   - Billions of records.
   - Millions of daily events.
   - 75% AWS savings.
3. **Selected work / recent project entries**
   - Reuse existing project records; do not rewrite case studies in this pass.
4. **Writing**
   - Existing recent blog entries, visually secondary to professional work.
5. **Short About preview**
   - Brief career narrative plus About link.
6. **Personal note / bison image**
   - Keep personality below professional evidence with accurate alt text.
7. **Contact/footer**
   - Email, GitHub, LinkedIn, feed.

---

### Task 1: Add a Post-Build Site Verifier

**Objective:** Define objective semantic, metadata, link, and asset requirements before changing templates.

**Files:**
- Create: `scripts/verify_site.py`

**Steps:**

1. Use Python’s `html.parser` and `pathlib`; do not add a runtime dependency.
2. Crawl generated `public/**/*.html`.
3. Assert for every indexable page:
   - nonempty, page-specific `<title>`;
   - nonempty, page-specific meta description;
   - exactly one canonical link;
   - one logical H1;
   - nonempty `lang` attribute;
   - no empty accessible link names;
   - all local stylesheet, image, favicon, and internal-link targets exist.
4. Assert Open Graph baseline fields: title, type, URL, image, and description.
5. Assert no page references `/about/me.jpg` unless that asset exists.
6. Assert the homepage contains the professional title and primary action links.
7. Assert About and Now do not contain “looking for work” or “seeking permanent role.”
8. Assert project/blog listing summaries do not contain nested anchors.
9. Add a warning—not a failure—for multiple same-value descriptions while migration is in progress; turn it into a failure after page descriptions are added.

**Baseline verification:**

```bash
zola build
python3 scripts/verify_site.py public
```

Expected before implementation: failures for metadata, multiple H1s, broken OG assets, stale copy, and nested/empty links.

### Task 2: Centralize Site Identity and Positioning

**Objective:** Give templates one verified source for name, role, positioning, actions, and impact claims.

**Files:**
- Modify: `config.toml`

**Steps:**

1. Replace the generic site title/description with a descriptive identity while preserving the `butterwick.tech` brand label for navigation.
2. Add structured site-specific configuration:

```toml
[extra.profile]
name = "Jordan Butterwick"
role = "Senior Software Engineer"
location = "Airdrie, Alberta"
# Draft positioning from verified résumé facts; final wording can be reviewed.
tagline = "I build and lead reliable backend, data, cloud, and ML systems at production scale."

[[extra.impact]]
value = "15M"
label = "users scaled"

[[extra.impact]]
value = "Billions"
label = "of records managed"

[[extra.impact]]
value = "Millions"
label = "of daily events"

[[extra.impact]]
value = "75%"
label = "AWS cost reduction"
```

3. Update the résumé menu URL to `$LANG_BASE_URL/resume/`.
4. Add a stable default social-image path and site-name value under `[extra.ogp]`.
5. Remove the external Font Awesome CDN configuration after inline icons are implemented.

**Content review checkpoint:** Show the hero tagline and labels to the user before treating them as final copy. Do not invent additional claims.

### Task 3: Create a Site-Specific Base Template

**Objective:** Establish correct landmarks, metadata, heading ownership, accessibility hooks, and navigation across all pages.

**Files:**
- Create: `templates/base.html` (project-level override)
- Create: `templates/macros/social.html` (project-level override)

**Steps:**

1. Adapt the current theme base template rather than extending invalid behavior.
2. Add a skip link targeting `#main-content`.
3. Change the global brand from `<h1>` to a plain `<a class="site-brand">`; page templates own H1.
4. Give navigation an accessible label and active links `aria-current="page"`.
5. Add `rel="noopener noreferrer"` to external links opened in new tabs.
6. Replace Font Awesome social icons with small inline SVGs that inherit `currentColor` and have visible/accessible link labels.
7. Build metadata variables with this precedence:
   - page/section title and description;
   - site defaults from `config.toml`.
8. Add:
   - unique title block;
   - meta description;
   - canonical URL;
   - Open Graph title/type/URL/image/description/site_name/image alt;
   - favicon, Apple touch icon, and manifest links.
9. Do not emit broken profile-image metadata.
10. Add a block for page-specific JSON-LD but keep default pages free of speculative schema.
11. Ensure every content template supplies `<main id="main-content">`.

**Verification:** Build and inspect Home, About, Now, Projects, one project page, and one blog page with `scripts/verify_site.py`.

### Task 4: Build the Professional Homepage

**Objective:** Replace the generic blog-first homepage with the proposed professional information architecture.

**Files:**
- Create: `templates/index.html` (project-level override)
- Modify: `config.toml`
- Modify: `sass/site.scss` after Task 9 creates it

**Steps:**

1. Render a single hero H1 containing the name and a separate visible role line.
2. Render the approved positioning sentence.
3. Add primary actions:
   - `/projects/` as “View selected work”;
   - `/resume/` as “Résumé”;
   - `mailto:` as “Contact”.
4. Render the four verified impact items from `config.extra.impact`.
5. Reuse the existing recent-project and recent-blog loops, but make Projects visually primary.
6. Add a short About preview sourced from approved static copy or `config.extra.profile`; do not duplicate the entire About page.
7. Move the bison image below professional content or into the About preview.
8. Correct the image alt text to describe the bison and surrounding prairie accurately.
9. Give the image explicit width/height or `aspect-ratio`; lazy-load it if it is below the fold.
10. Preserve crawlable ordinary links; do not add JavaScript navigation or filter controls.

**Acceptance:** At 1280×900 and 390×844, the first viewport identifies name, seniority, specialties, and at least two clear actions.

### Task 5: Remove Stale Employment Copy

**Objective:** Make current role/status consistent across the website without rewriting résumé bullets.

**Files:**
- Modify: `content/about/index.md`
- Modify: `content/now/index.md`
- Modify: `templates/now.html`

**Steps:**

1. Remove “currently looking for work” from About.
2. Remove “currently looking for work” and unemployment framing from Now.
3. Add or update front matter descriptions on both pages.
4. Add an `updated` date to Now and render it visibly.
5. Fix `templates/now.html` so its title and Open Graph title use `page.title`, not the About translation.
6. Let the shared base template provide default social metadata; do not hard-code `/about/me.jpg`.
7. Draft replacement copy only from known current facts and personal interests already present in the repo.

**Verification:** Search source and built output for stale phrases; expected: zero matches outside archived `oldsrc/`.

### Task 6: Expand the About Page

**Objective:** Turn the one-sentence About page into a concise professional narrative with personality and proof links.

**Files:**
- Modify: `content/about/index.md`
- Create: `templates/about.html` (project-level override)

**Proposed content structure:**

1. Current role and seniority.
2. Career arc across backend, data, ML, and cloud systems.
3. Engineering strengths: system design, modernization, team formation, mentoring.
4. Verified impact examples, linked to résumé rather than duplicated at excessive length.
5. Current focus.
6. Personal interests: gardening, fishing, hiking, whittling.
7. Contact/GitHub/LinkedIn actions.

**Steps:**

1. Draft approximately 250–400 words from verified repository facts.
2. Avoid “passionate,” “results-driven,” or generic technology-list prose.
3. Distinguish professional evidence from personal context with headings.
4. Add direct links to Projects, Résumé, GitHub, LinkedIn, and email.
5. Keep portrait imagery optional; do not block completion on a photo.
6. Add a page-specific description and profile Open Graph type only if all required fields are valid.
7. Optionally add `Person` JSON-LD with `name`, `url`, `jobTitle`, and `sameAs`; validate it and make no rich-result claims.

**User review checkpoint:** About copy requires approval because tone and personal narrative are subjective.

### Task 7: Repair Duplicate Titles, Heading Order, and Listing Links

**Objective:** Produce one logical H1 per page and valid, understandable link markup.

**Files:**
- Create: `templates/page.html` (project-level override)
- Create: `templates/macros/page.html` (project-level override)
- Modify: `content/projects/frishy.net/index.md`
- Modify: `content/projects/prairie/index.md`
- Modify: `content/blog/calgary-corn-city/index.md`
- Review: `templates/now.html`
- Review/Create if needed: `templates/projects.html`

**Steps:**

1. Let each page template render `page.title` as its only H1.
2. Remove the repeated leading Markdown H1 from the three current content pages without changing their prose.
3. In listing macros, make only the title or an explicit “Read…” link clickable.
4. Render summary HTML outside that anchor so Markdown links cannot nest inside it.
5. Use sequential headings: page H1, section H2, item H3.
6. Ensure link text is descriptive and nonempty.
7. Add `aria-label` only where visible text cannot be sufficiently descriptive; prefer visible text.
8. Keep project category behavior and case-study content unchanged because project restructuring is out of scope.

**Verification:** Lighthouse heading-order and link-name audits pass; verifier reports one H1 and no nested anchors.

### Task 8: Implement Responsive Navigation and Reflow

**Objective:** Eliminate horizontal clipping from the site and establish a mobile-first navigation layout.

**Files:**
- Modify: `themes/prairie/sass/base.scss`
- Modify/Create: `sass/site.scss`
- Modify: `templates/base.html`

**Steps:**

1. Remove float-based navigation layout.
2. Use flexbox with `flex-wrap: wrap`, explicit gaps, and no percentage margins on anchors.
3. At narrow widths, place brand and navigation in separate rows.
4. Keep all five navigation items visible without a JavaScript hamburger unless testing proves a simple wrap is insufficient.
5. Set `min-width: 0` on flex/grid children.
6. Add `overflow-wrap: anywhere` only for long URLs/identifiers, not all prose.
7. Give the main shell responsive inline padding using `clamp()`.
8. Preserve article line length around 65–70 characters while allowing the homepage to use a wider shell.
9. Ensure images use `max-width: 100%; height: auto` and explicit aspect ratios where applicable.
10. Remove accidental horizontal overflow rather than hiding it with `overflow-x: hidden`.

**Verification widths:** 320, 375, 390, 768, 1024, and 1280 CSS pixels. At each width, assert `document.documentElement.scrollWidth === window.innerWidth`.

### Task 9: Add the Editorial-Technical Visual System

**Objective:** Increase visual credibility while retaining the site’s dark, nature-oriented identity.

**Files:**
- Create: `sass/site.scss`
- Modify: `themes/prairie/sass/base.scss`
- Modify: `themes/prairie/sass/light.scss`
- Modify: `themes/prairie/sass/dark.scss`
- Modify: `templates/base.html`
- Modify: `templates/index.html`

**Design tokens:**

- Wider site shell: approximately 68–72rem.
- Reading width: 65–70ch.
- Spacing scale: 0.25rem, 0.5rem, 0.75rem, 1rem, 1.5rem, 2rem, 3rem, 4rem.
- Limited palette: background, raised surface, primary text, muted text, border, one green accent, one link accent.
- Modest radius: 6–10px.
- Thin borders; little or no shadow.
- Serif only for display headings; sans-serif for body and controls.

**Steps:**

1. Define shared custom properties for spacing, radii, widths, and semantic colors.
2. Increase homepage hierarchy: larger name, clear role, restrained eyebrow, visible actions.
3. Style impact items as a compact proof strip, not dashboard widgets.
4. Style project/writing entries as consistent cards or bordered rows with obvious focus/hover states.
5. Preserve long-form article readability.
6. Remove the remote Petrona `@import` or replace it with a self-hosted/subset font; default to a strong system serif stack if self-hosting is not justified.
7. Avoid gradients, glass effects, parallax, entrance animation, and decorative tech illustrations.
8. Add `prefers-reduced-motion` handling for any nonessential transition.
9. Confirm light and dark modes both meet contrast requirements.

**Visual acceptance:** The homepage looks intentional at desktop and mobile, while articles remain calm and readable.

### Task 10: Complete Accessibility Requirements

**Objective:** Reach a strong WCAG 2.2 AA baseline and eliminate current automated failures.

**Files:**
- Modify: `templates/base.html`
- Modify: `templates/index.html`
- Modify: `templates/page.html`
- Modify: `templates/macros/page.html`
- Modify: `templates/macros/social.html`
- Modify: `themes/prairie/sass/base.scss`
- Modify: `themes/prairie/sass/light.scss`
- Modify: `themes/prairie/sass/dark.scss`
- Modify: `sass/site.scss`

**Steps:**

1. Ensure skip link becomes visible on focus.
2. Add clear `:focus-visible` outlines with at least 3:1 non-text contrast.
3. Adjust muted/date/read-more colors to at least 4.5:1 for normal text.
4. Maintain visible non-color cues for active links and hover/focus.
5. Ensure interactive targets are at least 24×24 CSS pixels or sufficiently spaced.
6. Correct all meaningful image alt text; use empty alt only for decoration.
7. Keep logical landmarks and heading order.
8. Test keyboard-only navigation from top to footer.
9. Test at 200% zoom and 320px reflow.
10. Respect `prefers-reduced-motion`.
11. Run Lighthouse and treat automated 100 accessibility as a diagnostic goal, not proof of conformance.

**Manual acceptance:** No keyboard trap, focus loss, clipped focused control, or information conveyed by color alone.

### Task 11: Add Favicon, Social Card, Canonicals, and Page Metadata

**Objective:** Remove broken/missing trust assets and make search/social previews page-specific.

**Files:**
- Create: `static/favicon.svg`
- Create: `static/favicon.ico` or verified PNG fallback
- Create: `static/apple-touch-icon.png`
- Create: `static/social-card.png`
- Create: `static/site.webmanifest`
- Modify: `templates/base.html`
- Modify: `templates/page.html`
- Modify: `templates/about.html`
- Modify: `templates/now.html`
- Modify: content front matter under `content/**`
- Modify: `config.toml`

**Steps:**

1. Create a restrained square favicon derived from the site identity.
2. Create a 1200×630 social card with Jordan’s name, role, and domain; verify text remains legible at thumbnail size.
3. Add default Open Graph metadata in base and page-specific overrides where appropriate.
4. Add one canonical URL per page using the current permalink.
5. Add concise page-specific descriptions to Home, About, Now, Projects, Frishy, Prairie, Blog index, and Corn article.
6. Fix Now’s title and remove all references to the missing profile image.
7. Add `og:image:width`, `og:image:height`, and `og:image:alt`.
8. Keep the existing sitemap/robots output; do not add SEO plugins.
9. Validate all generated asset URLs locally and after deployment.

**Verification:** No favicon/OG 404s; verifier finds unique descriptions and one canonical per page.

### Task 12: Reduce Critical Third-Party Dependencies

**Objective:** Preserve the static-site performance advantage and remove avoidable request chains.

**Files:**
- Modify: `themes/prairie/sass/base.scss`
- Modify: `templates/base.html`
- Modify: `templates/macros/social.html`
- Modify: `config.toml`
- Modify: `templates/index.html`

**Steps:**

1. Remove Font Awesome CSS and use inline SVG social icons.
2. Remove the Bunny Fonts CSS import or self-host only the required display font files.
3. Use no client-side JavaScript for layout or navigation.
4. If the bison image remains above the fold, render an optimized image with explicit dimensions and `fetchpriority="high"`; otherwise lazy-load it below the fold.
5. Keep below-the-fold images lazy-loaded.
6. Use fingerprinted Zola-generated images where practical.
7. Avoid adding analytics or embeds in this pass.
8. Run Lighthouse mobile and desktop after local production build.

**Performance targets:** Diagnose toward LCP ≤2.5s, INP ≤200ms, and CLS ≤0.1; do not claim field performance from lab runs.

### Task 13: Integrate Build and Verification Commands

**Objective:** Make quality checks repeatable without hand-auditing generated HTML.

**Files:**
- Modify: `package.json`
- Modify: `README.md`
- Modify: `.github/workflows/main.yml` only if shared with the résumé workflow

**Proposed scripts:**

```json
{
  "scripts": {
    "build:resume-css": "npx @tailwindcss/cli -i ./static/input.css -o ./static/output.css",
    "build:site": "npm run build:resume-css && zola build",
    "check:site": "npm run build:site && python3 scripts/verify_site.py public",
    "serve": "zola serve"
  }
}
```

**Steps:**

1. Add the scripts with commands that match actual repository paths.
2. Replace the stale README Tailwind command that references `src/styles/input.css`.
3. Document local build, serve, site verification, résumé verification, and Lighthouse commands.
4. In CI, run the build and both standard-library verifiers.
5. Keep external-link checks separate because anti-bot responses and client-side fragment URLs create false positives.

**Verification:** A clean clone can run documented commands without guessing source paths.

### Task 14: Final Cross-Page QA

**Objective:** Verify the selected website improvements as one coherent release.

**Automated commands:**

```bash
npm run check:site
zola build
npx --yes lighthouse http://127.0.0.1:4173/ --quiet --chrome-flags='--headless --no-sandbox'
```

Run Lighthouse separately for Home, About, Projects, one project, one blog article, `/resume/`, and `/resume/application/`.

**Manual browser matrix:**

- 1280×900 desktop.
- 1024×768 small desktop/tablet landscape.
- 768×1024 tablet portrait.
- 390×844 phone.
- 375×812 phone.
- 320×568 minimum reflow check.

**Manual checks:**

1. Name, role, positioning, and actions are visible immediately on Home.
2. No stale job-search statements.
3. About has a credible professional narrative and direct proof/contact links.
4. Exactly one logical H1 per page.
5. No duplicated visible page titles in cards or articles.
6. No horizontal scrolling.
7. Nav remains usable and keyboard accessible at every width.
8. Focus states are visible.
9. Light/dark contrast passes.
10. No favicon, social-image, CSS, image, or canonical 404s.
11. Social card preview is legible.
12. Browser console has no errors.
13. Existing project/article content remains intact except removed duplicate H1s and explicitly approved stale-copy edits.

## Files Likely to Change

**Create**

- `templates/base.html`
- `templates/index.html`
- `templates/about.html`
- `templates/page.html`
- `templates/macros/page.html`
- `templates/macros/social.html`
- `sass/site.scss`
- `scripts/verify_site.py`
- `static/favicon.svg`
- `static/favicon.ico` or fallback PNG
- `static/apple-touch-icon.png`
- `static/social-card.png`
- `static/site.webmanifest`

**Modify**

- `config.toml`
- `content/about/index.md`
- `content/now/index.md`
- `content/projects/frishy.net/index.md` (remove duplicate H1 only)
- `content/projects/prairie/index.md` (remove duplicate H1 only)
- `content/blog/calgary-corn-city/index.md` (remove duplicate H1 only)
- `templates/now.html`
- `themes/prairie/sass/base.scss`
- `themes/prairie/sass/light.scss`
- `themes/prairie/sass/dark.scss`
- `package.json`
- `README.md`
- `.github/workflows/main.yml` if build checks are consolidated

**Never hand-edit**

- `public/**`

## Dependencies Between Plans

1. Implement the résumé plan’s routes and templates first, or coordinate route creation while changing `config.toml`.
2. The website plan should link to canonical `/resume/` and `/resume/application/` routes.
3. The shared CI workflow should run both `verify_site.py` and `verify_resume.py` after one production build.
4. The website base metadata must not override the standalone résumé templates’ deliberate metadata/print behavior.

## Risks and Tradeoffs

- Root template overrides reduce upgrade friction but duplicate some current theme markup; keep overrides small and document why they exist.
- Changing the site-wide brand/title structure can affect all pages; the verifier and screenshot matrix are required.
- Automated accessibility scores do not establish WCAG conformance; keyboard, zoom, and reflow checks remain mandatory.
- The homepage metrics are verified résumé facts, but presenting them without context can look boastful. Keep labels factual and link to the résumé rather than inventing explanations.
- Removing external fonts improves resilience/performance but changes visual character slightly; compare before/after screenshots.
- Open Graph previews are cached by external platforms; validate generated HTML and assets locally, then re-scrape after deployment.
- Project case-study quality and Frishy HTTPS remain known follow-up items, intentionally out of scope here.

## Completion Criteria

- Home identifies Jordan, role, specialties, proof, and actions in the first viewport.
- About and Now are current and no longer contradict the résumé.
- About contains a substantive professional narrative and personal context.
- Each page has one logical H1, valid listing links, and no duplicate visible title from Markdown.
- Navigation and content reflow without horizontal scrolling at 320px.
- The visual system is cohesive, restrained, and readable in light/dark mode.
- Current Lighthouse accessibility failures are resolved.
- Every indexable page has a unique title, description, canonical, and valid Open Graph baseline.
- Favicon and social-card assets return successfully.
- Critical Font Awesome and remote-font request chains are removed or justified.
- `npm run check:site` and the résumé verifier pass on a clean build.
- No project case-study rewrite or unrequested content expansion is introduced.
- No commits are created unless the user requests them.
