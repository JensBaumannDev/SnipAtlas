export type ContentArea = 'commands' | 'concepts' | 'blueprints' | 'debugging';

export type ContentIndex = Readonly<Record<string, readonly string[]>>;

const AREAS: readonly ContentArea[] = ['commands', 'concepts', 'blueprints', 'debugging'];

export function isContentArea(value: unknown): value is ContentArea {
  return AREAS.some((area) => area === value);
}

export function buildIndex(items: readonly { topic: string; subtopic?: string }[]): ContentIndex {
  const index: Record<string, string[]> = {};
  for (const { topic, subtopic } of items) {
    const subtopics = (index[topic] ??= []);
    if (subtopic && !subtopics.includes(subtopic)) {
      subtopics.push(subtopic);
    }
  }
  return index;
}
