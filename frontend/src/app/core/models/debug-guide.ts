import { CodeLanguage, OsCode } from './entry';

export const DEBUG_PATH = 'debuggen';

export interface DebugGuideStep {
  title: string;
  text: string;
  code?: { language: CodeLanguage; code: string | OsCode };
}

export interface DebugGuide {
  slug: string;
  topic?: string;
  label?: string;
  title: string;
  summary: string;
  steps: DebugGuideStep[];
}

export function debugWayLink(slug: string): string[] {
  return ['/fehler', DEBUG_PATH, slug];
}
