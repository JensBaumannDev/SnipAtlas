import { OperatingSystem } from './preferences';

export type CodeLanguage =
  | 'terminal'
  | 'python'
  | 'javascript'
  | 'typescript'
  | 'html'
  | 'css'
  | 'gitignore';

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
