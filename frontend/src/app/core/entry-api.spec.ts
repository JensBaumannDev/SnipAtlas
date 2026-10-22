import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { EntryApi } from './entry-api';
import { TopicApi } from './topic-api';

describe('EntryApi', () => {
  async function loadAll() {
    const groups = await firstValueFrom(TestBed.inject(TopicApi).getGroups());
    const topics = groups.flatMap((group) => group.topics);
    const api = TestBed.inject(EntryApi);
    const entries = (
      await Promise.all(topics.map((topic) => firstValueFrom(api.getByTopic(topic.slug))))
    ).flat();
    return { topics, entries };
  }

  it('returns only entries of the requested topic', async () => {
    const entries = await firstValueFrom(TestBed.inject(EntryApi).getByTopic('git'));
    expect(entries.length).toBeGreaterThan(0);
    expect(entries.every((entry) => entry.topic === 'git')).toBe(true);
  });

  it('assigns every entry to an existing subtopic', async () => {
    const { topics, entries } = await loadAll();
    const missing = entries
      .filter((entry) => {
        const topic = topics.find((item) => item.slug === entry.topic);
        return !topic?.subtopics.some((subtopic) => subtopic.slug === entry.subtopic);
      })
      .map((entry) => entry.slug);
    expect(missing).toEqual([]);
  });

  it('uses slugs that are unique and differ from subtopic slugs', async () => {
    const { topics, entries } = await loadAll();
    const subtopicSlugs = topics.flatMap((topic) => topic.subtopics.map((subtopic) => subtopic.slug));
    const slugs = entries.map((entry) => entry.slug);

    expect(new Set(slugs).size).toBe(slugs.length);
    expect(slugs.filter((slug) => subtopicSlugs.includes(slug))).toEqual([]);
  });
});
