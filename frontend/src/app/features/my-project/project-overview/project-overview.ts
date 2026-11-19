import { isPlatformBrowser } from '@angular/common';
import { Component, PLATFORM_ID, computed, effect, inject, untracked } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { firstCommand, newPaths } from '../../../core/content/roadmap-steps';
import { RoadmapPhase, RoadmapStep } from '../../../core/models/roadmap';
import { checkIcon, chevronRightIcon } from '../../../core/ui/icons';
import { Preferences } from '../../../core/user-data/preferences';
import { ProjectValues } from '../../../core/user-data/project-values';
import { ProgressBar } from '../../../shared/progress-bar/progress-bar';
import { ProjectTextPipe } from '../../../shared/project-text/project-text';
import { ProjectNavigation } from '../project-navigation/project-navigation';
import { injectRoadmap } from '../roadmap-state';

@Component({
  imports: [
    LucideDynamicIcon,
    ProgressBar,
    ProjectNavigation,
    ProjectTextPipe,
    RouterLink,
    TranslatePipe,
  ],
  selector: 'app-project-overview',
  styleUrl: './project-overview.scss',
  templateUrl: './project-overview.html',
})
export class ProjectOverview {
  private readonly os = inject(Preferences).os;
  private readonly projectValues = inject(ProjectValues).values;
  protected readonly state = injectRoadmap();
  protected readonly project = this.state.project;
  protected readonly roadmap = this.state.resource.value;
  protected readonly checkIcon = checkIcon;
  protected readonly chevronRightIcon = chevronRightIcon;
  protected readonly newPaths = newPaths;

  protected readonly doneCount = computed(
    () => this.state.refs().filter((ref) => this.project.isDone(ref.phase.slug, ref.step.slug)).length,
  );
  protected readonly next = computed(() =>
    this.state.refs().find((ref) => !this.project.isDone(ref.phase.slug, ref.step.slug)),
  );
  protected readonly meta = computed(() => {
    const name = this.projectValues().project?.trim();
    const stack = this.state.chosenNames().join(' · ');
    return name ? `${name} · ${stack}` : stack;
  });

  constructor() {
    redirectWithoutChoice(this.project);
  }

  protected phaseDone(phase: RoadmapPhase): number {
    return phase.steps.filter((step) => this.project.isDone(phase.slug, step.slug)).length;
  }

  protected command(step: RoadmapStep): string | undefined {
    return firstCommand(step, this.os());
  }
}

function redirectWithoutChoice(project: ReturnType<typeof injectRoadmap>['project']): void {
  const router = inject(Router);
  const isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  effect(() => {
    if (isBrowser && project.ready() && !project.blocks().length) {
      untracked(() => void router.navigate(['/mein-projekt/neu'], { replaceUrl: true }));
    }
  });
}
