import { Service, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { Observable, map, shareReplay } from 'rxjs';
import { AI_PATH, AREA_PATHS, aiAreaPath } from './area-links';
import { ContentArea } from './content-index';
import { TopicApi } from '../api/topic-api';
import { Group } from '../models/topic';

function aiTopicSlugs(groups: readonly Group[]): ReadonlySet<string> {
  const topics = groups.filter((group) => group.area === 'ai').flatMap((group) => group.topics);
  return new Set(topics.map((topic) => topic.slug));
}

@Service()
export class ContentPaths {
  private readonly aiTopics$ = inject(TopicApi).getGroups().pipe(map(aiTopicSlugs), shareReplay(1));

  private readonly aiTopics = toSignal(this.aiTopics$, {
    initialValue: new Set<string>() as ReadonlySet<string>,
  });

  isAi(topic: string): boolean {
    return this.aiTopics().has(topic);
  }

  belongsTo(topic: string, ai: boolean): Observable<boolean> {
    return this.aiTopics$.pipe(map((topics) => topics.has(topic) === ai));
  }

  path(area: ContentArea, topic: string): string {
    return this.isAi(topic) ? aiAreaPath(area) : AREA_PATHS[area];
  }

  link(area: ContentArea, topic: string, ...rest: string[]): string[] {
    return [this.path(area, topic), topic, ...rest];
  }

  rootPath(area: ContentArea, topic: string): string {
    return this.isAi(topic) ? AI_PATH : AREA_PATHS[area];
  }

  rootLabel(area: ContentArea, topic: string): string {
    return this.isAi(topic) ? 'pages.ai' : AREA_LABELS[area];
  }

  areaLink(link: readonly string[]): string[] {
    const [area, topic, ...rest] = link;
    return topic && this.isAi(topic) ? [`${AI_PATH}${area}`, topic, ...rest] : [...link];
  }
}

const AREA_LABELS: Readonly<Record<ContentArea, string>> = {
  commands: 'pages.commands',
  concepts: 'pages.concepts',
  blueprints: 'pages.blueprints',
  debugging: 'pages.debugging',
};
