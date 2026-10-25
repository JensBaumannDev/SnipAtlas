import { Component, effect, inject, input } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { PROJECT_KEYS, ProjectKey, ProjectValues, isProjectKey } from '../../core/project-values';

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
    effect(() => {
      const values = this.project.values();
      for (const key of PROJECT_KEYS) {
        const control = this.form.controls[key];
        const value = values[key] ?? '';
        if (control.value !== value) {
          control.setValue(value, { emitEvent: false });
        }
      }
    });

    this.form.valueChanges.pipe(takeUntilDestroyed()).subscribe((values) => {
      for (const [key, value] of Object.entries(values)) {
        if (isProjectKey(key) && typeof value === 'string' && value !== this.project.values()[key]) {
          this.project.set(key, value);
        }
      }
    });
  }
}
