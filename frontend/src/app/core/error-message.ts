import { CodeLanguage } from './entry';

export interface ErrorMessage {
  slug: string;
  topic: string;
  message: string;
  meaning: string;
  cause: string;
  steps: string[];
  solution?: { language: CodeLanguage; code: string };
}
