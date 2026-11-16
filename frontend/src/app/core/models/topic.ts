export interface Subtopic {
  slug: string;
  name: string;
}

export interface Topic {
  slug: string;
  name: string;
  color: string;
  subtopics: Subtopic[];
}

export type GroupArea = 'general' | 'ai';

export interface Group {
  slug: string;
  name: string;
  area: GroupArea;
  topics: Topic[];
}
