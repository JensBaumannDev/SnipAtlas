import { Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { AreaColumns } from '../../core/content/area-columns';
import { AREA_LINKS, AreaLink, NavArea } from '../../core/content/area-links';
import { TopicLogo } from '../topic-logo/topic-logo';

function linkOf(area: NavArea): AreaLink {
  return AREA_LINKS.find((link) => link.area === area) ?? AREA_LINKS[0];
}

@Component({
  imports: [RouterLink, TopicLogo, TranslatePipe],
  selector: 'app-area-topics',
  styleUrl: './area-topics.scss',
  templateUrl: './area-topics.html',
})
export class AreaTopics {
  readonly area = input.required<NavArea>();

  private readonly link = computed(() => linkOf(this.area()));
  private readonly areaColumns = new AreaColumns(this.link);

  protected readonly loaded = this.areaColumns.loaded;
  protected readonly columns = this.areaColumns.columns;
}
