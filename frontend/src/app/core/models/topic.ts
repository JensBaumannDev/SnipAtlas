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

export interface Group {
  slug: string;
  name: string;
  topics: Topic[];
}
