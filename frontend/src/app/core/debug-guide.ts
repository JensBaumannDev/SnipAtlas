import { CodeLanguage, OsCode } from './entry';

export interface DebugGuideStep {
  title: string;
  text: string;
  code?: { language: CodeLanguage; code: string | OsCode };
}

export interface DebugGuide {
  slug: string;
  topic?: string;
  title: string;
  summary: string;
  steps: DebugGuideStep[];
}
