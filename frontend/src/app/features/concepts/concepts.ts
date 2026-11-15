import { Component, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { ConceptApi } from '../../core/api/concept-api';
import { bookTextIcon } from '../../core/ui/icons';
import { TopicListing } from '../../core/content/topic-listing';
import { AreaInfo } from '../../shared/area-info/area-info';
import { AreaIntro } from '../../shared/area-intro/area-intro';
import { SubtopicTabs } from '../../shared/subtopic-tabs/subtopic-tabs';
import { TopicHeader } from '../../shared/topic-header/topic-header';
import { ConceptCard } from './concept-card/concept-card';

@Component({
  imports: [AreaInfo, AreaIntro, ConceptCard, RouterLink, SubtopicTabs, TopicHeader, TranslatePipe],
  selector: 'app-concepts',
  styleUrl: './concepts.scss',
  templateUrl: './concepts.html',
})
export class Concepts {
  private readonly conceptApi = inject(ConceptApi);

  readonly topic = input<string>();
  readonly subtopic = input<string>();

  protected readonly icon = bookTextIcon;
  protected readonly infoSections = ['what', 'why', 'difference'];
  protected readonly summary = toSignal(this.conceptApi.getSummary(), {
    initialValue: { entries: 0, topics: 0 },
  });

  private readonly concepts = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.conceptApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly listing = new TopicListing(this.topic, this.subtopic, this.concepts.value);
}
