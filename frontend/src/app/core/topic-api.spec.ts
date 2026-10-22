import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { TOPIC_ICONS, TOPIC_LOGOS } from './topic-logos';
import { TopicApi } from './topic-api';

describe('TopicApi', () => {
  it('returns the groups Frontend, Backend and Tools', async () => {
    const groups = await firstValueFrom(TestBed.inject(TopicApi).getGroups());
    expect(groups.map((group) => group.slug)).toEqual(['frontend', 'backend', 'tools']);
  });

  it('uses unique topic slugs', async () => {
    const groups = await firstValueFrom(TestBed.inject(TopicApi).getGroups());
    const slugs = groups.flatMap((group) => group.topics.map((topic) => topic.slug));
    expect(new Set(slugs).size).toBe(slugs.length);
  });

  it('has a logo or an icon for every topic', async () => {
    const groups = await firstValueFrom(TestBed.inject(TopicApi).getGroups());
    const missing = groups
      .flatMap((group) => group.topics)
      .filter((topic) => !TOPIC_LOGOS[topic.slug] && !TOPIC_ICONS[topic.slug])
      .map((topic) => topic.slug);
    expect(missing).toEqual([]);
  });

  it('uses unique subtopic slugs within each topic', async () => {
    const groups = await firstValueFrom(TestBed.inject(TopicApi).getGroups());
    for (const topic of groups.flatMap((group) => group.topics)) {
      const slugs = topic.subtopics.map((subtopic) => subtopic.slug);
      expect(new Set(slugs).size).toBe(slugs.length);
    }
  });
});
