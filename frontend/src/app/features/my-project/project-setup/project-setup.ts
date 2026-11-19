import { Component, computed, effect, inject, signal, untracked } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { of } from 'rxjs';
import { RoadmapApi } from '../../../core/api/roadmap-api';
import { ProjectKind, allowedFor, kindOf } from '../../../core/content/roadmap-steps';
import { BlockKind, RoadmapBlock } from '../../../core/models/roadmap';
import { MyProject } from '../../../core/user-data/my-project';
import { ProjectKey } from '../../../core/user-data/project-values';
import { ProjectForm } from '../../../shared/project-form/project-form';
import { TopicHeader } from '../../../shared/topic-header/topic-header';

interface Choice {
  kind: ProjectKind;
  frontend: string;
  backend: string;
  extras: readonly string[];
  hosting: string;
}

const KINDS: readonly ProjectKind[] = ['frontend', 'backend', 'both'];

@Component({
  imports: [ProjectForm, TopicHeader, TranslatePipe],
  selector: 'app-project-setup',
  styleUrl: './project-setup.scss',
  templateUrl: './project-setup.html',
})
export class ProjectSetup {
  private readonly router = inject(Router);
  private readonly api = inject(RoadmapApi);
  private readonly project = inject(MyProject);

  protected readonly kinds = KINDS;
  protected readonly projectKeys: readonly ProjectKey[] = ['project', 'githubUser', 'repo'];
  protected readonly blocks = toSignal(this.api.getBlocks(), { initialValue: [] });
  protected readonly choice = signal<Choice>({
    kind: 'both',
    frontend: '',
    backend: '',
    extras: [],
    hosting: '',
  });
  protected readonly saving = signal(false);

  protected readonly chosen = computed(() => chosenSlugs(this.choice(), this.blocks()));
  protected readonly complete = computed(() => isComplete(this.choice()));
  private readonly preview = rxResource({
    params: () => (this.complete() ? this.chosen() : []),
    stream: ({ params }) => (params.length ? this.api.getRoadmap(params) : of(undefined)),
  });
  protected readonly summary = computed(() => {
    const roadmap = this.preview.value();
    const steps = roadmap?.phases.reduce((sum, phase) => sum + phase.steps.length, 0) ?? 0;
    return roadmap ? { phases: roadmap.phases.length, steps } : undefined;
  });

  constructor() {
    effect(() => {
      const blocks = this.blocks();
      if (blocks.length && this.project.ready()) {
        untracked(() => this.choice.set(initialChoice(blocks, this.project.blocks())));
      }
    });
  }

  protected blocksOf(kind: BlockKind): RoadmapBlock[] {
    return this.blocks().filter((block) => block.kind === kind);
  }

  protected allowed(block: RoadmapBlock): boolean {
    return block.available && allowedFor(block, this.choice().kind);
  }

  protected setKind(kind: ProjectKind): void {
    this.choice.update((choice) => this.cleaned({ ...choice, kind }));
  }

  protected pick(field: 'frontend' | 'backend' | 'hosting', slug: string): void {
    this.choice.update((choice) => ({ ...choice, [field]: slug }));
  }

  protected toggleExtra(slug: string): void {
    this.choice.update((choice) => {
      const extras = choice.extras.includes(slug)
        ? choice.extras.filter((extra) => extra !== slug)
        : [...choice.extras, slug];
      return { ...choice, extras };
    });
  }

  protected submit(): void {
    this.saving.set(true);
    this.project.choose(this.chosen()).subscribe({
      next: () => void this.router.navigate(['/mein-projekt']),
      error: () => this.saving.set(false),
    });
  }

  private cleaned(choice: Choice): Choice {
    const keep = (slug: string) => {
      const block = this.blocks().find((item) => item.slug === slug);
      return !!block && allowedFor(block, choice.kind);
    };
    return {
      ...choice,
      extras: choice.extras.filter(keep),
      hosting: keep(choice.hosting) ? choice.hosting : '',
    };
  }
}

function isComplete(choice: Choice): boolean {
  const frontendOk = choice.kind === 'backend' || !!choice.frontend;
  return frontendOk && (choice.kind === 'frontend' || !!choice.backend);
}

function chosenSlugs(choice: Choice, blocks: readonly RoadmapBlock[]): string[] {
  const slugs = [
    choice.kind !== 'backend' ? choice.frontend : '',
    choice.kind !== 'frontend' ? choice.backend : '',
    ...choice.extras,
    choice.hosting,
  ];
  return slugs.filter((slug) => blocks.some((block) => block.slug === slug));
}

function initialChoice(blocks: readonly RoadmapBlock[], current: readonly string[]): Choice {
  const first = (kind: BlockKind) =>
    blocks.find((block) => block.kind === kind && current.includes(block.slug))?.slug ??
    blocks.find((block) => block.kind === kind && block.available)?.slug ??
    '';
  return {
    kind: current.length ? kindOf(blocks, current) : 'both',
    frontend: first('frontend'),
    backend: first('backend'),
    extras: blocks.filter((b) => b.kind === 'extra' && current.includes(b.slug)).map((b) => b.slug),
    hosting: blocks.find((b) => b.kind === 'hosting' && current.includes(b.slug))?.slug ?? '',
  };
}
