import { CodeLanguage, OsCode } from './entry';

export type BlockKind = 'frontend' | 'backend' | 'extra' | 'hosting';
export type BlockRequirement = 'any' | 'backend' | 'no-backend';
export type CodeKind = 'command' | 'create' | 'change';
export type PathChange = 'new' | 'changed' | 'removed';

export interface RoadmapBlock {
  slug: string;
  name: string;
  kind: BlockKind;
  requirement: BlockRequirement;
  available: boolean;
  topic?: string;
}

export interface RoadmapCode {
  kind: CodeKind;
  path?: string;
  language: CodeLanguage;
  code: string | OsCode;
}

export interface RoadmapPath {
  path: string;
  change: PathChange;
  tracked: boolean;
  explanation: string;
}

export interface TreeNode {
  name: string;
  path: string;
  folder: boolean;
  tracked: boolean;
  change?: PathChange;
  explanation?: string;
  phase?: string;
  step?: string;
  children?: TreeNode[];
}

export interface ErrorLink {
  topic: string;
  slug: string;
  message: string;
}

export interface ConceptLink {
  topic: string;
  subtopic: string;
  slug: string;
  title: string;
}

export interface RoadmapStep {
  slug: string;
  title: string;
  why: string;
  folder?: string;
  context?: string;
  verification: string;
  note?: string;
  code: RoadmapCode[];
  paths: RoadmapPath[];
  tree: TreeNode[];
  errors: ErrorLink[];
  concepts: ConceptLink[];
}

export interface RoadmapPhase {
  slug: string;
  title: string;
  summary: string;
  steps: RoadmapStep[];
}

export interface Roadmap {
  blocks: string[];
  phases: RoadmapPhase[];
}

export interface UserProject {
  blocks: string[];
  completed: Record<string, string[]>;
  notes: Record<string, Record<string, string>>;
  createdAt: string;
  updatedAt: string;
}

export interface StepRef {
  phase: RoadmapPhase;
  step: RoadmapStep;
  number: number;
}
