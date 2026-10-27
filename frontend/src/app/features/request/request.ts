import {
  Component,
  DOCUMENT,
  DestroyRef,
  ElementRef,
  Injector,
  afterNextRender,
  effect,
  inject,
  input,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NonNullableFormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon, LucideIconData } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { RequestKind } from '../../core/contact-request';
import { bugIcon, circleCheckIcon, filePlusIcon, lightbulbIcon } from '../../core/icons';
import { RequestApi } from '../../core/request-api';
import { describeEnvironment } from '../../core/user-environment';
import { BugFields } from './bug-fields/bug-fields';
import { EntryFields } from './entry-fields/entry-fields';
import { ImprovementFields } from './improvement-fields/improvement-fields';
import {
  FieldError,
  LIMITS,
  createRequestForm,
  toContactRequest,
  visibleError,
} from './request-form';

type SendStatus = 'idle' | 'sending' | 'sent' | 'error';

interface KindOption {
  value: RequestKind;
  label: string;
  description: string;
  icon: LucideIconData;
}

const KINDS: KindOption[] = [
  {
    value: 'entry',
    label: 'request.kinds.entry',
    description: 'request.kinds.entryText',
    icon: filePlusIcon,
  },
  {
    value: 'improvement',
    label: 'request.kinds.improvement',
    description: 'request.kinds.improvementText',
    icon: lightbulbIcon,
  },
  {
    value: 'bug',
    label: 'request.kinds.bug',
    description: 'request.kinds.bugText',
    icon: bugIcon,
  },
];

@Component({
  imports: [
    ReactiveFormsModule,
    RouterLink,
    TranslatePipe,
    LucideDynamicIcon,
    EntryFields,
    ImprovementFields,
    BugFields,
  ],
  selector: 'app-request',
  styleUrl: './request.scss',
  templateUrl: './request.html',
})
export class Request {
  private readonly api = inject(RequestApi);
  private readonly destroyRef = inject(DestroyRef);
  private readonly injector = inject(Injector);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  private readonly userAgent = inject(DOCUMENT).defaultView?.navigator.userAgent ?? '';

  readonly reference = input<string>(undefined, { alias: 'bezug' });

  protected readonly circleCheckIcon = circleCheckIcon;
  protected readonly kinds = KINDS;
  protected readonly status = signal<SendStatus>('idle');
  protected readonly submitted = signal(false);
  protected readonly kind = signal<RequestKind | ''>('');
  protected readonly form = createRequestForm(inject(NonNullableFormBuilder));

  constructor() {
    this.prepareForm();
    this.form.controls.kind.valueChanges
      .pipe(takeUntilDestroyed())
      .subscribe((kind) => this.selectKind(kind));

    effect(() => {
      const reference = this.reference();
      if (reference) {
        this.form.controls.bug.controls.location.setValue(reference.slice(0, LIMITS.location));
        this.form.controls.kind.setValue('bug');
      }
    });
  }

  protected error(name: 'kind' | 'email' | 'privacy'): FieldError | undefined {
    return visibleError(this.form.controls[name], this.submitted());
  }

  protected submit(): void {
    this.submitted.set(true);
    const request = toContactRequest(this.form);
    if (this.form.invalid || !request) {
      this.form.markAllAsTouched();
      this.focusFirstError();
      return;
    }

    this.status.set('sending');
    this.api
      .send(request)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.status.set('sent'),
        error: () => this.status.set('error'),
      });
  }

  protected startOver(): void {
    this.form.reset();
    this.prepareForm();
    this.submitted.set(false);
    this.status.set('idle');
  }

  private prepareForm(): void {
    this.form.controls.bug.controls.environment.setValue(describeEnvironment(this.userAgent));
    this.selectKind(this.form.controls.kind.value);
  }

  private selectKind(kind: RequestKind | ''): void {
    const { entry, improvement, bug } = this.form.controls;
    for (const [name, group] of [
      ['entry', entry],
      ['improvement', improvement],
      ['bug', bug],
    ] as const) {
      if (name === kind) {
        group.enable({ emitEvent: false });
      } else {
        group.disable({ emitEvent: false });
      }
    }
    this.kind.set(kind);
  }

  private focusFirstError(): void {
    afterNextRender(
      () => {
        const target = this.form.controls.kind.invalid
          ? this.host.querySelector<HTMLElement>('input[name="kind"]')
          : this.host.querySelector<HTMLElement>('[aria-invalid="true"]');
        target?.focus();
      },
      { injector: this.injector },
    );
  }
}
