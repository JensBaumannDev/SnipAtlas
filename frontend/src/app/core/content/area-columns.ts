import { Signal, computed, inject } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { TopicApi } from '../api/topic-api';
import { AreaContent } from './area-content';
import { AreaLink } from './area-links';
import { filterGroups } from './content-index';
import { NavGroup, navGroups } from './nav-groups';

export interface TopicColumn extends NavGroup {
  summaries: string[];
}

function toColumn(group: NavGroup): TopicColumn {
  return {
    ...group,
    summaries: group.topics.map((topic) => topic.subtopics.map((sub) => sub.name).join(', ')),
  };
}

export class AreaColumns {
  private readonly areaContent = inject(AreaContent);
  private readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });

  private readonly index = rxResource({
    params: () => this.link().area,
    stream: ({ params }) => this.areaContent.getIndex(params),
  });

  private readonly debugWays = rxResource({
    params: () => (this.link().area === 'debugging' ? true : undefined),
    stream: () => this.areaContent.getDebugWays(),
    defaultValue: [],
  });

  readonly loaded = computed(() => this.index.hasValue());

  readonly columns = computed(() => {
    const index = this.index.value();
    if (!index) {
      return [];
    }
    const { area, path } = this.link();
    const groups = filterGroups(this.groups(), index);
    return navGroups(area, path, groups, this.debugWays.value()).map(toColumn);
  });

  constructor(private readonly link: Signal<AreaLink>) {}
}
