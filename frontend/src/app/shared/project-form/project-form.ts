import { Component, effect, inject, input } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import {
  PROJECT_KEYS,
  ProjectKey,
  ProjectValueMap,
  ProjectValues,
} from '../../core/user-data/project-values';

let nextId = 0;

@Component({
  imports: [ReactiveFormsModule, TranslatePipe],
  selector: 'app-project-form',
  styleUrl: './project-form.scss',
  templateUrl: './project-form.html',
})
export class ProjectForm {
  private readonly project = inject(ProjectValues);

  readonly keys = input<readonly ProjectKey[]>(PROJECT_KEYS);

  protected readonly idPrefix = `project-form-${nextId++}`;
  protected readonly form = new FormGroup(
    Object.fromEntries(
      PROJECT_KEYS.map((key) => [key, new FormControl('', { nonNullable: true })]),
    ) as Record<ProjectKey, FormControl<string>>,
  );

  constructor() {
    effect(() => this.showValues(this.project.values()));
    this.form.valueChanges.pipe(takeUntilDestroyed()).subscribe((values) => this.save(values));
  }

  private showValues(values: ProjectValueMap): void {
    for (const key of PROJECT_KEYS) {
      const control = this.form.controls[key];
      const value = values[key] ?? '';
      if (control.value !== value) {
        control.setValue(value, { emitEvent: false });
      }
    }
  }

  private save(values: ProjectValueMap): void {
    for (const key of PROJECT_KEYS) {
      const value = values[key];
      if (value !== undefined && value !== this.project.values()[key]) {
        this.project.set(key, value);
      }
    }
  }
}
