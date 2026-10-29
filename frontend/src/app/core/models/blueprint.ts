import { CodeLanguage, OsCode } from './entry';

export interface BlueprintCode {
  language: CodeLanguage;
  code: string | OsCode;
}

export interface BlueprintStep {
  slug: string;
  title: string;
  why: string;
  code: BlueprintCode[];
  note?: string;
}

export interface Blueprint {
  slug: string;
  topic: string;
  title: string;
  summary: string;
  steps: BlueprintStep[];
}
