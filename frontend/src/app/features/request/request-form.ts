import { AbstractControl, NonNullableFormBuilder, Validators } from '@angular/forms';
import {
  BugType,
  ContactRequest,
  EntryArea,
  ImprovementArea,
  RequestKind,
} from '../../core/contact-request';

export const LIMITS = {
  title: 120,
  short: 20,
  text: 2000,
  note: 1000,
  location: 200,
  source: 300,
} as const;

const URL_PATTERN = /^https?:\/\/\S+$/;

export interface FieldError {
  key: string;
  params?: Record<string, unknown>;
}

export function createRequestForm(fb: NonNullableFormBuilder) {
  const { required, minLength, maxLength } = Validators;
  return fb.group({
    kind: fb.control<RequestKind | ''>('', required),
    entry: fb.group({
      area: fb.control<EntryArea | ''>('', required),
      topic: ['', required],
      title: ['', [required, maxLength(LIMITS.title)]],
      reason: ['', [required, minLength(LIMITS.short), maxLength(LIMITS.note)]],
      example: ['', maxLength(LIMITS.text)],
      source: ['', [maxLength(LIMITS.source), Validators.pattern(URL_PATTERN)]],
    }),
    improvement: fb.group({
      area: fb.control<ImprovementArea | ''>('', required),
      idea: ['', [required, minLength(LIMITS.short), maxLength(LIMITS.text)]],
      benefit: ['', maxLength(LIMITS.note)],
    }),
    bug: fb.group({
      type: fb.control<BugType | ''>('', required),
      location: ['', [required, maxLength(LIMITS.location)]],
      problem: ['', [required, minLength(LIMITS.short), maxLength(LIMITS.text)]],
      correction: ['', maxLength(LIMITS.note)],
      environment: ['', maxLength(LIMITS.location)],
    }),
    email: ['', [required, Validators.email]],
    privacy: [false, Validators.requiredTrue],
  });
}

export type RequestForm = ReturnType<typeof createRequestForm>;
export type EntryForm = RequestForm['controls']['entry'];
export type ImprovementForm = RequestForm['controls']['improvement'];
export type BugForm = RequestForm['controls']['bug'];

export function toContactRequest(form: RequestForm): ContactRequest | undefined {
  const { kind, entry, improvement, bug, email } = form.getRawValue();
  const address = email.trim();

  if (kind === 'entry' && entry.area) {
    return {
      kind,
      area: entry.area,
      topic: entry.topic,
      title: entry.title.trim(),
      reason: entry.reason.trim(),
      example: entry.example.trim(),
      source: entry.source.trim(),
      email: address,
    };
  }
  if (kind === 'improvement' && improvement.area) {
    return {
      kind,
      area: improvement.area,
      idea: improvement.idea.trim(),
      benefit: improvement.benefit.trim(),
      email: address,
    };
  }
  if (kind === 'bug' && bug.type) {
    return {
      kind,
      type: bug.type,
      location: bug.location.trim(),
      problem: bug.problem.trim(),
      correction: bug.correction.trim(),
      environment: bug.type === 'broken' ? bug.environment.trim() : '',
      email: address,
    };
  }
  return undefined;
}

export function fieldError(control: AbstractControl): FieldError | undefined {
  const errors = control.errors;
  if (!errors) {
    return undefined;
  }
  if (errors['required']) {
    return { key: 'request.errors.required' };
  }
  if (errors['email']) {
    return { key: 'request.errors.emailFormat' };
  }
  if (errors['minlength']) {
    return { key: 'request.errors.minLength', params: { min: errors['minlength'].requiredLength } };
  }
  if (errors['maxlength']) {
    return { key: 'request.errors.maxLength', params: { max: errors['maxlength'].requiredLength } };
  }
  if (errors['pattern']) {
    return { key: 'request.errors.url' };
  }
  return { key: 'request.errors.invalid' };
}

export function visibleError(control: AbstractControl, submitted: boolean): FieldError | undefined {
  return control.invalid && (control.touched || submitted) ? fieldError(control) : undefined;
}
