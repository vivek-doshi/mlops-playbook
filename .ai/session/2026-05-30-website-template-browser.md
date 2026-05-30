# Session: MLOps Playbook Website — Template Lab

**Date:** 2026-05-30  
**Type:** Feature creation (new website/ directory)

## Objective
Create a creative, animated template browser website for the mlops-playbook repo, to be deployed on GitHub Pages. Inspired by DevOps Playbook but with ML-themed visual design.

## What Was Built

### Stack
- React 18.3.1 + TypeScript 5.5.3 + Vite 5.3.4
- Prism.js 1.29.0 for syntax highlighting
- Canvas-based neural network animation
- Base URL: `/mlops-playbook/`
- Deployed via GitHub Actions → GitHub Pages

### Files Created
```
website/
  package.json                   # npm package, scripts: dev/build/preview/index
  tsconfig.json                  # references tsconfig.app.json
  tsconfig.app.json              # includes "types": ["vite/client"] (critical)
  vite.config.ts                 # base: '/mlops-playbook/', @vitejs/plugin-react
  index.html                     # Inter + JetBrains Mono fonts, OG meta tags
  public/
    index.json                   # 161 files, 15 categories, 762.7 KB (pre-generated)
  scripts/
    generate-index.js            # ESM Node.js script: walks repo root → public/index.json
  src/
    main.tsx                     # React root mount
    App.tsx                      # Root component: theme, fetch, Ctrl+K shortcut
    App.css                      # CSS custom properties, keyframes, global styles
    types/index.ts               # FileEntry, FileIndex, Theme, CategoryMeta, TreeNode
    components/
      NeuralCanvas.tsx           # Canvas animation: 55 nodes, connections, particles
      Header.tsx / Header.css    # Logo, stats pills, Random button, theme toggle
      Sidebar.tsx / Sidebar.css  # Search, category tree, language badges
      CodeViewer.tsx / CodeViewer.css  # Prism syntax highlight, copy, GitHub link
.github/workflows/
  deploy-website.yml             # CI/CD: npm install → generate-index → build → pages
```

### Themes
- **"Synthetic Midnight"** (dark, default): `#070d1a` base, `#00d4ff` cyan, `#a855f7` violet
- **"Neural Daybreak"** (light): `#eef2ff` base, `#4f46e5` indigo, `#7c3aed` violet

### Index Coverage (161 files across 15 categories)
ci:24, cd:20, docs:31, terraform:16, policy:11, monitoring:9, finops:9, batch:7, pipelines:10, serving:6, mlflow:5, training:5, feature-store:3, fairness:3, dvc:2

## Key Technical Issues Resolved
1. **TypeScript `import.meta.env` error**: Fixed by adding `"types": ["vite/client"]` to `tsconfig.app.json`
2. **npm preview from wrong directory**: Used `npx --prefix <path> vite preview` to avoid working-directory issues

## Validation
- `npm run build` → clean build, 47 modules, dist/ generated (index.html 1.16 KB, CSS 18.75 KB, JS 194.55 KB)
- Preview server confirmed rendering: header, sidebar tree, code viewer, neural canvas all visible
- Screenshot taken showing "Synthetic Midnight" theme with live file browsing

## User Action Required
1. Go to repo **Settings → Pages**
2. Set Source to **"GitHub Actions"**
3. Push changes to `main` → workflow `deploy-website.yml` fires automatically
4. Site will be live at: `https://vivek-doshi.github.io/mlops-playbook/`
