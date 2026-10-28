import { OperatingSystem } from './preferences';

export type CodeLanguage =
  'terminal' | 'python' | 'javascript' | 'typescript' | 'html' | 'css' | 'gitignore' | 'env';

export type OsCode = Record<OperatingSystem, string>;

export interface Entry {
  slug: string;
  topic: string;
  subtopic: string;
  title: string;
  description: string;
  language: CodeLanguage;
  code: string | OsCode;
}

export function entryLink({ topic, subtopic, slug }: Entry): string[] {
  return ['/befehle', topic, subtopic, slug];
}
