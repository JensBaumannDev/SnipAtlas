import { Signal, inject } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { Subtopic, Topic } from './topic';
import { TopicApi } from './topic-api';

export interface SubtopicSection<T> {
  subtopic: Subtopic;
  items: T[];
}

export function injectTopic(slug: () => string | undefined): Signal<Topic | undefined> {
  const topicApi = inject(TopicApi);
  return rxResource({
    params: slug,
    stream: ({ params }) => topicApi.getBySlug(params),
  }).value;
}

export function findSubtopic(
  topic: Topic | undefined,
  slug: string | undefined,
): Subtopic | undefined {
  return topic?.subtopics.find((subtopic) => subtopic.slug === slug);
}

export function groupBySubtopic<T extends { subtopic: string }>(
  subtopics: readonly Subtopic[],
  items: readonly T[],
): SubtopicSection<T>[] {
  return subtopics
    .map((subtopic) => ({
      subtopic,
      items: items.filter((item) => item.subtopic === subtopic.slug),
    }))
    .filter((section) => section.items.length);
}
