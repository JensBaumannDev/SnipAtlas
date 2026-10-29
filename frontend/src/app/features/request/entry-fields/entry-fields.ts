import { Component, inject, input } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { AbstractControl, ReactiveFormsModule } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { EntryArea } from '../../../core/models/contact-request';
import { TopicApi } from '../../../core/api/topic-api';
import { EntryForm, FieldError, LIMITS, visibleError } from '../request-form';

@Component({
  imports: [ReactiveFormsModule, TranslatePipe],
  selector: 'app-entry-fields',
  styleUrl: './entry-fields.scss',
  templateUrl: './entry-fields.html',
})
export class EntryFields {
  readonly group = input.required<EntryForm>();
  readonly submitted = input(false);

  protected readonly areas: EntryArea[] = ['command', 'concept', 'error'];
  protected readonly groups = toSignal(inject(TopicApi).getGroups(), { initialValue: [] });
  protected readonly limits = LIMITS;

  protected error(control: AbstractControl): FieldError | undefined {
    return visibleError(control, this.submitted());
  }
}
