import { ContentArea } from './content-index';
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

export function navGroups(
  area: ContentArea | undefined,
  path: string,
  groups: readonly Group[],
  ways: readonly Topic[],
): NavGroup[] {
  return area === 'debugging' ? debuggingGroups(path, groups, ways) : topicGroups(path, groups);
}
