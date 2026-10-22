export type SidebarMode = 'topics' | 'subtopics';

export function isSidebarMode(value: unknown): value is SidebarMode {
  return value === 'topics' || value === 'subtopics';
}
