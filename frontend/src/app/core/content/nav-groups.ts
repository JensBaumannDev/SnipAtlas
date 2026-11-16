import { NavArea } from './area-links';
import { DEBUG_PATH } from '../models/debug-guide';
import { Group, Topic } from '../models/topic';

export interface NavGroup {
  slug: string;
  name: string;
  translate: boolean;
  path: string;
  topics: Topic[];
}

function translatedGroup(
  slug: string,
  name: string,
  path: string,
  topics: readonly Topic[],
): NavGroup {
  return { slug, name, translate: true, path, topics: [...topics] };
}

function topicGroups(path: string, groups: readonly Group[]): NavGroup[] {
  return groups.map((group) => ({ ...group, translate: false, path }));
}

function debuggingGroups(
  path: string,
  groups: readonly Group[],
  ways: readonly Topic[],
): NavGroup[] {
  return [
    translatedGroup(DEBUG_PATH, 'debugging.nav.debug', `${path}/${DEBUG_PATH}`, ways),
    ...topicGroups(path, groups),
  ];
}

function groupsOfArea(area: NavArea | undefined, groups: readonly Group[]): Group[] {
  const groupArea = area === 'ai' ? 'ai' : 'general';
  return groups.filter((group) => group.area === groupArea);
}

export function navGroups(
  area: NavArea | undefined,
  path: string,
  groups: readonly Group[],
  ways: readonly Topic[],
): NavGroup[] {
  const own = groupsOfArea(area, groups);
  return area === 'debugging' ? debuggingGroups(path, own, ways) : topicGroups(path, own);
}
