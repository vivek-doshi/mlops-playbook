export interface FileEntry {
  id: string
  name: string
  path: string
  language: string
  size: number
  content: string
  category: string
  tags?: string[]
}

export interface FileIndex {
  generated: string
  repoName: string
  repoUrl: string
  totalFiles: number
  files: FileEntry[]
}

export type Theme = 'dawn' | 'dusk'

export interface CategoryMeta {
  name: string
  icon: string
  color: string
  description: string
}

export interface TreeNode {
  name: string
  path: string
  children: Map<string, TreeNode>
  files: FileEntry[]
  totalFiles: number
}
