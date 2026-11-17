import { Component, afterRenderEffect, computed, inject, input } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { AreaContent } from '../../core/content/area-content';
import { aiAreaPath } from '../../core/content/area-links';
import { CONTENT_AREAS, ContentArea } from '../../core/content/content-index';
import { KEEP_SCROLL } from '../../core/ui/scroll-restoration';

const KIND_LABELS: Readonly<Record<ContentArea, string>> = {
  commands: 'nav.commands',
  concepts: 'nav.concepts',
  blueprints: 'nav.blueprints',
  debugging: 'nav.debugging',
};

@Component({
  imports: [RouterLink, RouterLinkActive, TranslatePipe],
  selector: 'app-kind-tabs',
  styleUrl: './kind-tabs.scss',
  templateUrl: './kind-tabs.html',
})
export class KindTabs {
  readonly topic = input.required<string>();

  protected readonly keepScroll = KEEP_SCROLL;

  private readonly areaContent = inject(AreaContent);
  private readonly indexes = this.areaContent.kindIndexesSignal();

  protected readonly tabs = computed(() => {
    const topic = this.topic();
    return CONTENT_AREAS.filter((_, i) => Object.hasOwn(this.indexes()[i] ?? {}, topic)).map(
      (kind) => ({
        kind,
        label: KIND_LABELS[kind],
        link: [aiAreaPath(kind), topic],
      }),
    );
  });

  constructor() {
    afterRenderEffect(() => this.areaContent.prefetchTopic(this.topic()));
  }
}
