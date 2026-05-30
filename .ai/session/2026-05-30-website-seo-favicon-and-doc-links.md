# Session: Website SEO, Favicon, and Concepts Guide Entry Links

**Date:** 2026-05-30  
**Type:** Documentation + website metadata enhancement

## Objective
1. Add prominent links to `docs/guides/concepts.md` from top-level docs.
2. Add favicon for `website/`.
3. Verify and improve website SEO and confirm GitHub Pages deployment alignment.

## Changes Made

### Documentation discoverability
- Updated `README.md`:
  - Added concepts guide in the "New here?" line.
  - Added concepts guide in the task quick-links table.
- Updated `GETTING_STARTED.md`:
  - Added concepts guide row in "ML Lifecycle Quick Links".

### Website favicon + SEO
- Added `website/public/favicon.svg`.
- Added social preview image `website/public/og-image.svg`.
- Added crawler support files:
  - `website/public/robots.txt`
  - `website/public/sitemap.xml`
- Added web manifest:
  - `website/public/site.webmanifest`
- Updated `website/index.html` metadata:
  - canonical URL
  - robots meta
  - Open Graph type/url/image
  - Twitter card tags
  - manifest link
  - JSON-LD structured data (`WebSite` schema with `SearchAction`)

### Hosting/deployment check
- Verified workflow ` .github/workflows/deploy-website.yml` deploys to GitHub Pages using `actions/upload-pages-artifact` and `actions/deploy-pages`.
- Verified Vite base path is set to `/mlops-playbook/` in `website/vite.config.ts`.

## Validation
- Ran `npm run build` from `website/`.
- Build succeeded and generated production bundle.

## Repo Intelligence Updates
- Updated `.ai/context/repo-summary.md` with website SEO/branding capability note.
- Updated `.ai/retrieval/workflow-to-files.yaml` with SEO-related website entrypoints.
