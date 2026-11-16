import { Component, computed, inject, input } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { EntryApi } from '../../core/api/entry-api';
import { terminalIcon } from '../../core/ui/icons';
import { Preferences } from '../../core/user-data/preferences';
import { TopicListing } from '../../core/content/topic-listing';
import { ContentPaths } from '../../core/content/content-paths';
import { AreaInfo } from '../../shared/area-info/area-info';
import { AreaIntro } from '../../shared/area-intro/area-intro';
import { SubtopicTabs } from '../../shared/subtopic-tabs/subtopic-tabs';
import { TopicHeader } from '../../shared/topic-header/topic-header';
import { KindTabs } from '../../shared/kind-tabs/kind-tabs';
import { EntryCard } from './entry-card/entry-card';

@Component({
  imports: [
    AreaInfo,
    AreaIntro,
    EntryCard,
    KindTabs,
    RouterLink,
    SubtopicTabs,
    TopicHeader,
    TranslatePipe,
  ],
  selector: 'app-commands',
  styleUrl: './commands.scss',
  templateUrl: './commands.html',
})
export class Commands {
  protected readonly paths = inject(ContentPaths);
  private readonly entryApi = inject(EntryApi);

  readonly topic = input<string>();
  readonly subtopic = input<string>();

  protected readonly os = inject(Preferences).os;
  protected readonly icon = terminalIcon;
  protected readonly infoSections = ['what', 'why', 'memorize'];
  protected readonly summary = toSignal(this.entryApi.getSummary(), {
    initialValue: { entries: 0, topics: 0 },
  });

  private readonly entries = rxResource({
    params: () => this.topic(),
    stream: ({ params }) => this.entryApi.getByTopic(params),
    defaultValue: [],
  });

  protected readonly listing = new TopicListing(this.topic, this.subtopic, this.entries.value);

  protected readonly hasOsVariants = computed(() =>
    this.listing.visible().some((entry) => typeof entry.code !== 'string'),
  );
}
