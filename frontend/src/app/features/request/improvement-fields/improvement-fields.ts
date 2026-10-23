import { Component, input } from '@angular/core';
import { AbstractControl, ReactiveFormsModule } from '@angular/forms';
import { TranslatePipe } from '@ngx-translate/core';
import { ImprovementArea } from '../../../core/contact-request';
import { FieldError, ImprovementForm, visibleError } from '../request-form';

@Component({
  imports: [ReactiveFormsModule, TranslatePipe],
  selector: 'app-improvement-fields',
  styleUrl: './improvement-fields.scss',
  templateUrl: './improvement-fields.html',
})
export class ImprovementFields {
  readonly group = input.required<ImprovementForm>();
  readonly submitted = input(false);

  protected readonly areas: ImprovementArea[] = ['content', 'usability', 'design', 'feature', 'other'];

  protected error(control: AbstractControl): FieldError | undefined {
    return visibleError(control, this.submitted());
  }
}
