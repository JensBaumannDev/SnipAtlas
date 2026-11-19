import { Component, computed, effect, inject, input, signal, untracked } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { ContentPaths } from '../../../core/content/content-paths';
import { resolveOsCode } from '../../../core/content/os-code';
import { findStep } from '../../../core/content/roadmap-steps';
import { ConceptLink, ErrorLink, StepRef } from '../../../core/models/roadmap';
import { checkIcon, squareIcon } from '../../../core/ui/icons';
import { Preferences } from '../../../core/user-data/preferences';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { Note } from '../../../shared/note/note';
import { ProjectTextPipe } from '../../../shared/project-text/project-text';
import { TermText } from '../../../shared/term-text/term-text';
import { TopicHeader } from '../../../shared/topic-header/topic-header';
import { ProjectNavigation } from '../project-navigation/project-navigation';
import { ProjectTree } from '../project-tree/project-tree';
import { injectRoadmap } from '../roadmap-state';

const NOTE_MAX_LENGTH = 2000;

@Component({
  imports: [
    CodeBlock,
    LucideDynamicIcon,
    Note,
    ProjectNavigation,
    ProjectTextPipe,
    ProjectTree,
    ReactiveFormsModule,
    RouterLink,
    TermText,
    TopicHeader,
    TranslatePipe,
  ],
  selector: 'app-project-step-page',
  styleUrl: './project-step-page.scss',
  templateUrl: './project-step-page.html',
})
export class ProjectStepPage {
  private readonly os = inject(Preferences).os;
  private readonly paths = inject(ContentPaths);

  readonly phase = input.required<string>();
  readonly step = input.required<string>();

  protected readonly state = injectRoadmap();
  protected readonly project = this.state.project;
  protected readonly checkIcon = checkIcon;
  protected readonly squareIcon = squareIcon;
  protected readonly noteMaxLength = NOTE_MAX_LENGTH;
  protected readonly note = new FormControl('', {
    nonNullable: true,
    validators: [Validators.maxLength(NOTE_MAX_LENGTH)],
  });
  protected readonly noteSaved = signal(false);

  protected readonly current = computed(() =>
    findStep(this.state.refs(), this.phase(), this.step()),
  );
  protected readonly previous = computed(() => this.neighbor(-1));
  protected readonly next = computed(() => this.neighbor(1));
  protected readonly done = computed(() => this.project.isDone(this.phase(), this.step()));
  protected readonly missing = computed(
    () => this.state.resource.hasValue() || (this.project.ready() && !this.project.blocks().length),
  );
  protected readonly codes = computed(
    () =>
      this.current()?.step.code.map((code) => ({
        ...code,
        ...resolveOsCode(code.code, this.os()),
      })) ?? [],
  );

  constructor() {
    effect(() => {
      const text = this.project.note(this.phase(), this.step());
      untracked(() => this.resetNote(text));
    });
  }

  protected saveNote(): void {
    if (this.note.invalid) {
      return;
    }
    this.project.saveNote(this.phase(), this.step(), this.note.value).subscribe({
      next: () => this.noteSaved.set(true),
      error: () => undefined,
    });
  }

  protected errorLink(error: ErrorLink): string[] {
    return this.paths.link('debugging', error.topic, error.slug);
  }

  protected conceptLink(concept: ConceptLink): string[] {
    return this.paths.link('concepts', concept.topic, concept.subtopic, concept.slug);
  }

  private neighbor(offset: number): StepRef | undefined {
    const ref = this.current();
    return ref ? this.state.refs()[ref.number - 1 + offset] : undefined;
  }

  private resetNote(text: string): void {
    this.note.setValue(text);
    this.noteSaved.set(false);
  }
}
