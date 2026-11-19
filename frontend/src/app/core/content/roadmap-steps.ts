import { Roadmap, RoadmapBlock, RoadmapStep, StepRef } from '../models/roadmap';
import { OperatingSystem } from '../user-data/preferences';
import { resolveOsCode } from './os-code';

export type ProjectKind = 'frontend' | 'backend' | 'both';

export function stepRefs(roadmap: Roadmap): StepRef[] {
  let number = 0;
  return roadmap.phases.flatMap((phase) =>
    phase.steps.map((step) => ({ phase, step, number: ++number })),
  );
}

export function findStep(refs: StepRef[], phase: string, step: string): StepRef | undefined {
  return refs.find((ref) => ref.phase.slug === phase && ref.step.slug === step);
}

export function firstCommand(step: RoadmapStep, os: OperatingSystem): string | undefined {
  const command = step.code.find((code) => code.kind === 'command');
  return command ? resolveOsCode(command.code, os).code.split('\n')[0] : undefined;
}

export function newPaths(step: RoadmapStep): string[] {
  return step.paths.filter((path) => path.change === 'new').map((path) => path.path);
}

export function kindOf(blocks: readonly RoadmapBlock[], chosen: readonly string[]): ProjectKind {
  const kinds = blocks.filter((block) => chosen.includes(block.slug)).map((block) => block.kind);
  if (kinds.includes('frontend') && kinds.includes('backend')) {
    return 'both';
  }
  return kinds.includes('backend') ? 'backend' : 'frontend';
}

export function allowedFor(block: RoadmapBlock, kind: ProjectKind): boolean {
  if (block.requirement === 'backend') {
    return kind !== 'frontend';
  }
  return block.requirement === 'no-backend' ? kind === 'frontend' : true;
}
