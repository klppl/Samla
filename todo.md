# Static Site Generator Roadmap

## 🚨 Must Have
**Critical fixes and essential features for a baseline production site.**

- [x] **OpenGraph & Twitter Cards**: Add `<meta property="og:..." >` tags to `base.html` for social sharing previews.
- [x] **Canonical URLs**: Add `<link rel="canonical" ...>` to prevent duplicate content issues.
- [x] **404 Page**: Generate a custom `404.html` for error handling on deployment platforms.
- [x] **Draft Support**: content loader should respect `draft: true` in frontmatter and exclude those posts from production builds (allow via flag).
- [x] **Fix CLI Config Consistency**: Ensure `manage.py` respects `output_dir` from `config.yaml` instead of hardcoding `public`/`dist`.
- [x] **Cloudflare Deployment**: Added `wrangler.toml` and `package.json` for automated builds and Workers/Pages hosting.

## ⚠️ Should Have
**Important features for a professional quality site.**

- [x] **Asset Minification**: Compress CSS and JS files during the build process to improve load times.
- [x] **Syntax Highlighting CSS**: Ensure a Pygments/highlight.js compatible CSS theme is included for code blocks.
- [x] **Better Pagination**: Add numbered pagination links (1, 2, 3...) instead of just Prev/Next.
- [x] **Related Posts**: Suggest content based on shared tags.
- [x] **Enhanced `new` Command**: Support creating `micro`, `review`, etc., via CLI arguments.
- [x] **Robust Shortcode Parser**: Improve regex in `shortcode_manager.py` to handle quotes and spaces reliably.
- [x] **Refactor Content Loading**: Implement Registry Pattern for content types to remove hardcoded logic in `content_loader.py`.
- [x] **Custom Timeline Icon**: Use post frontmatter `emoji` (if present) as the timeline icon, falling back to the category default.
- [x] **Data Files Support**: Load structured data (JSON/YAML) from a `data/` directory into `site.data` (like Jekyll `_data`).

- [x] **Live Reload**: Enhance `manage.py serve` to watch for file changes and auto-rebuild/reload the browser.
- [x] **Archetypes**: Replace hardcoded `new` command logic with template files in `archetypes/` for custom content generation.
- [x] **Localization / i18n**: Support translating UI strings (e.g., "Read more" -> "Läs mer") and date formatting (Swedish locale) via `i18n/*.yaml` files.
- [x] **Localized URLs**: Map content sections to localized URLs (e.g. `posts` -> `inlagg`) via `slugs` in `i18n/sv.yaml`.
- [x] **Relative URLs**: Ensure all links and assets use relative paths for portability (subdirectory hosting).
- [x] **Icon Refactor**: Moved default icons to Archetypes (📝, 💬, 🎬, 🔖) and implemented a global fallback (💬) with Unicode escape reliability.


## 🚀 Nice to Have
**Advanced features for specific use cases.**

- [x] **Search Functionality**: Generate a `search.json` index for client-side search (Lunr.js).
- [x] **Image Optimization**: Automatically resize and convert images to WebP during build.
- [x] **Incremental Builds**: The Pragmatic Strategy: For a site of this size, `Cache Markdown Processing` (CPU-heavy) but `Always Re-generate Pages` (Jinja2 is fast).
- [x] **Theme Toggle**: Add a JavaScript toggle for Light/Dark mode.
- [x] **CLI Interface**: Use `argparse` or `click` for a better command-line experience (e.g. `python manage.py build`).
- [x] **Shortcodes**: Add support for custom shortcodes in Markdown (e.g., `{{< youtube id >}}`).
- [x] **Image Shortcode**: Add `{{< img src="..." >}}` shortcode for easy image embedding.
- [x] **Post Assets**: Copy non-markdown files (images, etc.) from content folders to output folders.
- [x] **External Link Referral**: Append `?ref=...` to all external links (use `base_url` from `config.yaml`).
- [x] **Generators**: Add `humans.txt` generation.
- [x] **Dynamic humans.txt**: Generate `humans.txt` using data from `config.yaml` (chef, contact, social media, etc.).
- [x] **Code Cleanup**: Remove redundant logic in `content_loader.py` and unify `public`/`dist` references.
- [ ] **Permalinks Configuration**: Allow configurable URL structures in `config.yaml` (e.g. `/:year/:month/:slug/`) instead of hardcoded paths.
- [ ] **Redirects / Aliases**: Support `aliases: [/old-url/]` in frontmatter to generate HTML redirect pages.
- [ ] **Custom Taxonomies**: Allow defining arbitrary taxonomies (e.g., "Series", "Authors") in `config.yaml`.
- [ ] **Open Graph Image Generation**: Automatically generate social preview images with the post title overlaid.
- [x] **Asset Pipeline (Sass)**: Add support for compiling SCSS/Sass files to CSS.
- [ ] **Sitemap Priorities**: Allow setting priority/changefreq in frontmatter for better SEO control.
- [x] **Root Files Support**: Allow a specific folder (e.g., `files/` or `static/root/`) to be copied directly to the site root (e.g. for `robots.txt`, `favicon.ico`).
- [x] **Internal Linking (Shortnames)**: Support `shortname` in frontmatter and a mechanism (like `[[shortname]]` or `{{< link "shortname" >}}`) to auto-link to that post. (Implemented via `shortcodes/link.py` and `SiteBuilder._resolve_internal_links`)

## 🥱 Stuff to add if I'm bored
- [ ] **Reading Time**: Calculate estimated reading time for posts and expose it in the template context.
- [ ] **Table of Contents**: Auto-generate a TOC from markdown headers for long posts.
