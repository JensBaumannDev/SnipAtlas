import { Component, computed, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { AreaContent } from '../../core/content/area-content';
import { AreaLink } from '../../core/content/area-links';
import { filterGroups } from '../../core/content/content-index';
import { NavGroup, navGroups } from '../../core/content/nav-groups';
import { TopicApi } from '../../core/api/topic-api';
import { TopicLogo } from '../../shared/topic-logo/topic-logo';

interface MenuColumn extends NavGroup {
  summaries: string[];
}

function toColumn(group: NavGroup): MenuColumn {
  return {
    ...group,
    summaries: group.topics.map((topic) => topic.subtopics.map((sub) => sub.name).join(', ')),
  };
}

@Component({
  imports: [RouterLink, TopicLogo, TranslatePipe],
  selector: 'app-area-menu',
  styleUrl: './area-menu.scss',
  templateUrl: './area-menu.html',
})
export class AreaMenu {
  private readonly areaContent = inject(AreaContent);
  private readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });

  readonly link = input.required<AreaLink>();

  private readonly index = rxResource({
    params: () => this.link().area,
    stream: ({ params }) => this.areaContent.getIndex(params),
  });

  private readonly debugWays = rxResource({
    params: () => (this.link().area === 'debugging' ? true : undefined),
    stream: () => this.areaContent.getDebugWays(),
    defaultValue: [],
  });

  protected readonly loaded = computed(() => this.index.hasValue());

  protected readonly hasDebugColumn = computed(() => this.link().area === 'debugging');

  protected readonly columns = computed(() => {
    const index = this.index.value();
    if (!index) {
      return [];
    }
    const { area, path } = this.link();
    const groups = filterGroups(this.groups(), index);
    return navGroups(area, path, groups, this.debugWays.value()).map(toColumn);
  });
}
