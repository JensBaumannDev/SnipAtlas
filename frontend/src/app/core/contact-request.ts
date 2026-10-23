export type RequestKind = 'entry' | 'improvement' | 'bug';
export type EntryArea = 'command' | 'concept' | 'error';
export type ImprovementArea = 'content' | 'usability' | 'design' | 'feature' | 'other';
export type BugType = 'wrong' | 'outdated' | 'broken' | 'typo';

export interface EntryRequest {
  kind: 'entry';
  area: EntryArea;
  topic: string;
  title: string;
  reason: string;
  example: string;
  source: string;
  email: string;
}

export interface ImprovementRequest {
  kind: 'improvement';
  area: ImprovementArea;
  idea: string;
  benefit: string;
  email: string;
}

export interface BugRequest {
  kind: 'bug';
  type: BugType;
  location: string;
  problem: string;
  correction: string;
  environment: string;
  email: string;
}

export type ContactRequest = EntryRequest | ImprovementRequest | BugRequest;
