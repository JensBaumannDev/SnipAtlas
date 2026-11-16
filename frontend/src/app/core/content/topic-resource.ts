import { Signal, computed, inject } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { Group, Subtopic, Topic } from '../models/topic';
import { TopicApi } from '../api/topic-api';

export interface SubtopicSection<T> {
  subtopic: Subtopic;
  items: T[];
}

function findTopic(groups: readonly Group[], slug: string | undefined): Topic | undefined {
  return groups.flatMap((group) => group.topics).find((topic) => topic.slug === slug);
}

export function injectTopic(slug: () => string | undefined): Signal<Topic | undefined> {
  const topicApi = inject(TopicApi);
  const groups = toSignal(topicApi.getGroups(), { initialValue: [] });
  const loaded = rxResource({
    params: slug,
    stream: ({ params }) => topicApi.getBySlug(params),
  }).value;
  return computed(() => findTopic(groups(), slug()) ?? loaded());
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
