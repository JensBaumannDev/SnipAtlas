import { Component, input } from '@angular/core';
import { AbstractControl, ReactiveFormsModule } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { BugType } from '../../../core/models/contact-request';
import { BugForm, FieldError, LIMITS, visibleError } from '../request-form';

@Component({
  imports: [ReactiveFormsModule, TranslatePipe],
  selector: 'app-bug-fields',
  styleUrl: './bug-fields.scss',
  templateUrl: './bug-fields.html',
})
export class BugFields {
  readonly group = input.required<BugForm>();
  readonly submitted = input(false);

  protected readonly types: BugType[] = ['wrong', 'outdated', 'broken', 'typo'];
  protected readonly limits = LIMITS;

  protected error(control: AbstractControl): FieldError | undefined {
    return visibleError(control, this.submitted());
  }
}
