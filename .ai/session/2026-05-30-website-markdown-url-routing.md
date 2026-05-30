# Session: Website Markdown URL Routing and In-App Link Navigation

**Date:** 2026-05-30  
**Type:** Logic update (existing website components)

## Objective
Fix markdown link behavior in the website browser so clicking links does not navigate to 404 pages and instead opens target markdown files inside the app with URL/history support.

## Changes Implemented

### 1) URL-synced file state in website app
Updated `website/src/App.tsx` to manage selected files through query parameter routing:
- Introduced `?file=<repo-relative-path>` as the canonical file URL.
- Added URL read-on-load selection logic.
- Added `popstate` handling for browser back/forward.
- Added history push/replace synchronization when file selection changes.

### 2) Internal markdown link resolution and interception
Updated `website/src/App.tsx` and `website/src/components/CodeViewer.tsx`:
- Added internal link resolver for markdown links (relative and absolute repo paths).
- Added support for GitHub blob links by mapping them back to repo-relative paths.
- Added candidate matching strategy for directories and markdown defaults:
  - exact path
  - `<path>/README.md`
  - `<path>.md` (when extension omitted)
- Added click interception in markdown renderer to keep navigation inside the website.

### 3) Existing navigation hooks use URL-aware selection
- Sidebar file selection now routes via URL-aware selector.
- Random file picker now routes via URL-aware selector.

## Validation
- Ran website build from `website/`:
  - `npm run build`
  - Result: successful TypeScript + Vite production build.

## Repo Intelligence Updates
- Updated `.ai/context/repo-summary.md` with website markdown browser navigation capability.
- Updated `.ai/retrieval/workflow-to-files.yaml` with `website/src/App.tsx` and `website/src/components/CodeViewer.tsx` as frontend SPA entrypoints for this behavior.

## Outcome
Markdown links now open content within the site, and browser back/forward returns users to previously viewed files instead of losing reading context or navigating to external 404 pages.
