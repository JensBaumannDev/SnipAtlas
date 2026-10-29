import { AbstractControl, NonNullableFormBuilder, Validators } from '@angular/forms';
import {
  BugRequest,
  BugType,
  ContactRequest,
  EntryArea,
  EntryRequest,
  ImprovementArea,
  ImprovementRequest,
  RequestKind,
} from '../../core/models/contact-request';

export const LIMITS = {
  title: 120,
  short: 20,
  text: 2000,
  note: 1000,
  location: 200,
  source: 300,
} as const;

const URL_PATTERN = /^https?:\/\/\S+$/;

const { required, minLength, maxLength } = Validators;

export interface FieldError {
  key: string;
  params?: Record<string, unknown>;
}

interface ErrorRule {
  name: string;
  key: string;
  param?: 'min' | 'max';
}

const ERROR_RULES: readonly ErrorRule[] = [
  { name: 'required', key: 'request.errors.required' },
  { name: 'email', key: 'request.errors.emailFormat' },
  { name: 'minlength', key: 'request.errors.minLength', param: 'min' },
  { name: 'maxlength', key: 'request.errors.maxLength', param: 'max' },
  { name: 'pattern', key: 'request.errors.url' },
];

function createEntryGroup(fb: NonNullableFormBuilder) {
  return fb.group({
    area: fb.control<EntryArea | ''>('', required),
    topic: ['', required],
    title: ['', [required, maxLength(LIMITS.title)]],
    reason: ['', [required, minLength(LIMITS.short), maxLength(LIMITS.note)]],
    example: ['', maxLength(LIMITS.text)],
    source: ['', [maxLength(LIMITS.source), Validators.pattern(URL_PATTERN)]],
  });
}

function createImprovementGroup(fb: NonNullableFormBuilder) {
  return fb.group({
    area: fb.control<ImprovementArea | ''>('', required),
    idea: ['', [required, minLength(LIMITS.short), maxLength(LIMITS.text)]],
    benefit: ['', maxLength(LIMITS.note)],
  });
}

function createBugGroup(fb: NonNullableFormBuilder) {
  return fb.group({
    type: fb.control<BugType | ''>('', required),
    location: ['', [required, maxLength(LIMITS.location)]],
    problem: ['', [required, minLength(LIMITS.short), maxLength(LIMITS.text)]],
    correction: ['', maxLength(LIMITS.note)],
    environment: ['', maxLength(LIMITS.location)],
  });
}

export function createRequestForm(fb: NonNullableFormBuilder) {
  return fb.group({
    kind: fb.control<RequestKind | ''>('', required),
    entry: createEntryGroup(fb),
    improvement: createImprovementGroup(fb),
    bug: createBugGroup(fb),
    email: ['', [required, Validators.email]],
    privacy: [false, Validators.requiredTrue],
    website: [''],
  });
}

export type RequestForm = ReturnType<typeof createRequestForm>;
export type EntryForm = ReturnType<typeof createEntryGroup>;
export type ImprovementForm = ReturnType<typeof createImprovementGroup>;
export type BugForm = ReturnType<typeof createBugGroup>;

type FormValue<T extends AbstractControl> = ReturnType<T['getRawValue']>;

function toEntryRequest(entry: FormValue<EntryForm>, email: string): EntryRequest | undefined {
  if (!entry.area) {
    return undefined;
  }
  return {
    kind: 'entry',
    area: entry.area,
    topic: entry.topic,
    title: entry.title.trim(),
    reason: entry.reason.trim(),
    example: entry.example.trim(),
    source: entry.source.trim(),
    email,
  };
}

function toImprovementRequest(
  improvement: FormValue<ImprovementForm>,
  email: string,
): ImprovementRequest | undefined {
  if (!improvement.area) {
    return undefined;
  }
  return {
    kind: 'improvement',
    area: improvement.area,
    idea: improvement.idea.trim(),
    benefit: improvement.benefit.trim(),
    email,
  };
}

function toBugRequest(bug: FormValue<BugForm>, email: string): BugRequest | undefined {
  if (!bug.type) {
    return undefined;
  }
  return {
    kind: 'bug',
    type: bug.type,
    location: bug.location.trim(),
    problem: bug.problem.trim(),
    correction: bug.correction.trim(),
    environment: bug.type === 'broken' ? bug.environment.trim() : '',
    email,
  };
}

export function toContactRequest(form: RequestForm): ContactRequest | undefined {
  const { kind, entry, improvement, bug, email } = form.getRawValue();
  const address = email.trim();
  switch (kind) {
    case 'entry':
      return toEntryRequest(entry, address);
    case 'improvement':
      return toImprovementRequest(improvement, address);
    case 'bug':
      return toBugRequest(bug, address);
    default:
      return undefined;
  }
}

function fieldError(control: AbstractControl): FieldError | undefined {
  const errors = control.errors;
  if (!errors) {
    return undefined;
  }
  const rule = ERROR_RULES.find(({ name }) => errors[name]);
  if (!rule) {
    return { key: 'request.errors.invalid' };
  }
  const { name, key, param } = rule;
  return param ? { key, params: { [param]: errors[name].requiredLength } } : { key };
}

export function visibleError(control: AbstractControl, submitted: boolean): FieldError | undefined {
  return control.invalid && (control.touched || submitted) ? fieldError(control) : undefined;
}
