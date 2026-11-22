import { TreeNode } from '../../core/models/roadmap';

export function findNode(nodes: TreeNode[], path: string): TreeNode | undefined {
  for (const node of nodes) {
    const found = node.path === path ? node : findNode(node.children ?? [], path);
    if (found) {
      return found;
    }
  }
  return undefined;
}

export function folderPaths(path: string): string[] {
  const parts = path.split('/').filter(Boolean);
  const count = path.endsWith('/') ? parts.length : parts.length - 1;
  return parts.slice(0, count).map((_, index) => `${parts.slice(0, index + 1).join('/')}/`);
}

export function folderOf(path: string): string {
  return folderPaths(path).at(-1) ?? '';
}
