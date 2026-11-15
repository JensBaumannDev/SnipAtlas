import { ContentArea } from './content-index';
import { DEBUG_PATH } from '../models/debug-guide';
import { Group, Topic } from '../models/topic';

const ERRORS_GROUP = 'haeufige-fehler';

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

function debuggingGroups(
  path: string,
  groups: readonly Group[],
  ways: readonly Topic[],
): NavGroup[] {
  const topics = groups.flatMap((group) => group.topics);
  return [
    translatedGroup(DEBUG_PATH, 'debugging.nav.debug', `${path}/${DEBUG_PATH}`, ways),
    translatedGroup(ERRORS_GROUP, 'debugging.nav.errors', path, topics),
  ];
}

export function navGroups(
  area: ContentArea | undefined,
  path: string,
  groups: readonly Group[],
  ways: readonly Topic[],
): NavGroup[] {
  return area === 'debugging'
    ? debuggingGroups(path, groups, ways)
    : groups.map((group) => ({ ...group, translate: false, path }));
}
