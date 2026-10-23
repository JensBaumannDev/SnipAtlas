import { CodeLanguage } from './entry';

export interface Concept {
  slug: string;
  topic: string;
  subtopic: string;
  title: string;
  summary: string;
  explanation: string;
  language: CodeLanguage;
  code: string;
  note?: string;
}
