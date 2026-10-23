import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { ConceptApi } from './concept-api';
import { TopicApi } from './topic-api';

describe('ConceptApi', () => {
  async function loadAll() {
    const groups = await firstValueFrom(TestBed.inject(TopicApi).getGroups());
    const topics = groups.flatMap((group) => group.topics);
    const api = TestBed.inject(ConceptApi);
    const concepts = (
      await Promise.all(topics.map((topic) => firstValueFrom(api.getByTopic(topic.slug))))
    ).flat();
    return { topics, concepts };
  }

  it('returns only concepts of the requested topic', async () => {
    const concepts = await firstValueFrom(TestBed.inject(ConceptApi).getByTopic('python'));
    expect(concepts.length).toBeGreaterThan(0);
    expect(concepts.every((concept) => concept.topic === 'python')).toBe(true);
  });

  it('assigns every concept to an existing subtopic', async () => {
    const { topics, concepts } = await loadAll();
    const missing = concepts
      .filter((concept) => {
        const topic = topics.find((item) => item.slug === concept.topic);
        return !topic?.subtopics.some((subtopic) => subtopic.slug === concept.subtopic);
      })
      .map((concept) => concept.slug);
    expect(missing).toEqual([]);
  });

  it('uses slugs that are unique and differ from subtopic slugs', async () => {
    const { topics, concepts } = await loadAll();
    const subtopicSlugs = topics.flatMap((topic) => topic.subtopics.map((subtopic) => subtopic.slug));
    const slugs = concepts.map((concept) => concept.slug);

    expect(new Set(slugs).size).toBe(slugs.length);
    expect(slugs.filter((slug) => subtopicSlugs.includes(slug))).toEqual([]);
  });
});
