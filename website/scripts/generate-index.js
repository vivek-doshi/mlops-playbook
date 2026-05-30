#!/usr/bin/env node
/**
 * generate-index.js
 * Scans the mlops-playbook repo and produces website/public/index.json
 * Run from the website/ directory: node scripts/generate-index.js
 */

import fs   from 'fs'
import path from 'path'
import { createHash } from 'crypto'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = path.resolve(__dirname, '../../')
const OUT_FILE  = path.resolve(__dirname, '../public/index.json')

// ── Config ─────────────────────────────────────────────────────────────────

const EXCLUDE_DIRS = new Set([
  'website', 'node_modules', '.git', '.github', '.ai', '__pycache__',
  '.mypy_cache', '.pytest_cache', '.venv', 'venv', 'env', '.env',
  'dist', 'build', '.terraform', '.task',
])

const EXCLUDE_FILES = new Set([
  '.DS_Store', 'Thumbs.db', '.gitignore', '.gitattributes',
  '.env', '.env.example',
  'package-lock.json', 'yarn.lock', 'poetry.lock',
  '__init__.py',
])

const INCLUDE_EXTS = new Set([
  '.yml', '.yaml', '.py', '.tf', '.tfvars', '.hcl',
  '.json', '.sh', '.bash', '.md', '.dockerfile', 'dockerfile',
  '.toml', '.ini', '.cfg', 'makefile', 'taskfile.yml',
])

const EXT_TO_LANG = {
  '.yml':  'yaml',  '.yaml': 'yaml',
  '.py':   'python',
  '.tf':   'hcl',   '.tfvars': 'hcl', '.hcl': 'hcl',
  '.json': 'json',
  '.sh':   'bash',  '.bash': 'bash',
  '.md':   'markdown',
  '.toml': 'toml',  '.ini': 'ini', '.cfg': 'ini',
  '.dockerfile': 'dockerfile', 'dockerfile': 'dockerfile',
  'makefile': 'makefile', 'taskfile.yml': 'yaml',
}

const CATEGORY_DIRS = [
  'ci', 'cd', 'training', 'serving', 'monitoring', 'batch', 'pipelines',
  'fairness', 'terraform', 'finops', 'mlflow', 'dvc', 'feature-store',
  'policy', 'docs',
]

const MAX_FILE_SIZE = 100 * 1024  // 100 KB

// ── Helpers ────────────────────────────────────────────────────────────────

function fileId(filepath) {
  return createHash('md5').update(filepath).digest('hex').slice(0, 10)
}

function detectLang(filepath) {
  const base = path.basename(filepath).toLowerCase()
  if (base === 'dockerfile') return 'dockerfile'
  const ext = path.extname(base)
  return EXT_TO_LANG[ext] ?? 'text'
}

function shouldInclude(filepath) {
  const base = path.basename(filepath)
  const ext  = path.extname(base).toLowerCase()
  if (EXCLUDE_FILES.has(base)) return false
  if (INCLUDE_EXTS.has(ext))  return true
  if (INCLUDE_EXTS.has(base.toLowerCase())) return true
  return false
}

function walkDir(dir, category, repoRelBase, files = []) {
  let entries
  try { entries = fs.readdirSync(dir, { withFileTypes: true }) }
  catch { return files }

  for (const entry of entries) {
    if (entry.name.startsWith('.') && entry.name !== '.gitignore') continue

    const fullPath = path.join(dir, entry.name)
    const relPath  = path.relative(REPO_ROOT, fullPath).replace(/\\/g, '/')

    if (entry.isDirectory()) {
      if (EXCLUDE_DIRS.has(entry.name)) continue
      walkDir(fullPath, category, repoRelBase, files)
    } else if (entry.isFile() && shouldInclude(fullPath)) {
      const stat = fs.statSync(fullPath)
      if (stat.size > MAX_FILE_SIZE) continue

      let content
      try { content = fs.readFileSync(fullPath, 'utf8') }
      catch { continue }

      // Normalise line endings, strip BOM
      content = content.replace(/^\uFEFF/, '').replace(/\r\n/g, '\n').trimEnd()

      files.push({
        id:       fileId(relPath),
        name:     entry.name,
        path:     relPath,
        language: detectLang(fullPath),
        size:     Buffer.byteLength(content, 'utf8'),
        content,
        category,
      })
    }
  }
  return files
}

// ── Main ───────────────────────────────────────────────────────────────────

console.log('🔍  Scanning repo at:', REPO_ROOT)

// Dynamically discover all top-level directories (skip only explicitly excluded dirs)
const topLevelDirs = fs.readdirSync(REPO_ROOT, { withFileTypes: true })
  .filter(e => e.isDirectory() && !EXCLUDE_DIRS.has(e.name))
  .map(e => e.name)

// Apply known category ordering first, then sort any remaining alphabetically
const orderedDirs = [
  ...CATEGORY_DIRS.filter(c => topLevelDirs.includes(c)),
  ...topLevelDirs.filter(c => !CATEGORY_DIRS.includes(c)).sort(),
]

const allFiles = []
for (const cat of orderedDirs) {
  const dir = path.join(REPO_ROOT, cat)
  const catFiles = walkDir(dir, cat, dir)
  allFiles.push(...catFiles)
  console.log(`  ✓  ${cat}: ${catFiles.length} files`)
}

// Scan root-level files directly (README.md, Makefile, Taskfile.yml, .pre-commit-config.yaml, etc.)
const rootFiles = []
for (const entry of fs.readdirSync(REPO_ROOT, { withFileTypes: true })) {
  if (!entry.isFile()) continue
  const fullPath = path.join(REPO_ROOT, entry.name)
  if (!shouldInclude(fullPath)) continue
  const stat = fs.statSync(fullPath)
  if (stat.size > MAX_FILE_SIZE) continue
  let content
  try { content = fs.readFileSync(fullPath, 'utf8') } catch { continue }
  content = content.replace(/^\uFEFF/, '').replace(/\r\n/g, '\n').trimEnd()
  rootFiles.push({
    id:       fileId(entry.name),
    name:     entry.name,
    path:     entry.name,
    language: detectLang(fullPath),
    size:     Buffer.byteLength(content, 'utf8'),
    content,
    category: 'root',
  })
}
if (rootFiles.length) {
  allFiles.push(...rootFiles)
  console.log(`  ✓  root: ${rootFiles.length} files`)
}

// Sort: by category order, then by path
allFiles.sort((a, b) => {
  const ca = CATEGORY_DIRS.indexOf(a.category)
  const cb = CATEGORY_DIRS.indexOf(b.category)
  if (ca !== cb) return ca - cb
  return a.path.localeCompare(b.path)
})

const index = {
  generated:  new Date().toISOString(),
  repoName:   'mlops-playbook',
  repoUrl:    'https://github.com/vivek-doshi/mlops-playbook',
  totalFiles: allFiles.length,
  files:      allFiles,
}

fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true })
fs.writeFileSync(OUT_FILE, JSON.stringify(index), 'utf8')

const sizeKB = (Buffer.byteLength(JSON.stringify(index), 'utf8') / 1024).toFixed(1)
console.log(`\n✅  Wrote ${allFiles.length} files → ${path.relative(process.cwd(), OUT_FILE)} (${sizeKB} KB)`)
