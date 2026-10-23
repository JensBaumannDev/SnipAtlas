export type SidebarMode = 'topics' | 'subtopics';

export function isSidebarMode(value: unknown): value is SidebarMode {
  return value === 'topics' || value === 'subtopics';
}

export function isGroupList(value: unknown): value is readonly string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string');
}
