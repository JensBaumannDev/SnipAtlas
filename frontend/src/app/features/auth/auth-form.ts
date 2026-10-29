import {
  ElementRef,
  Injector,
  WritableSignal,
  afterNextRender,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AbstractControl, ValidationErrors } from '@angular/forms';
import { ApiError } from '../../core/api-error';

export function passwordsMatch(group: AbstractControl): ValidationErrors | null {
  const { password, repeat } = group.getRawValue() as { password: string; repeat: string };
  return password === repeat ? null : { mismatch: true };
}

export function hasVisibleError(
  control: AbstractControl,
  error: string,
  attempted: boolean,
): boolean {
  return control.hasError(error) && (attempted || control.touched);
}

export function injectFocusInvalid(): () => void {
  const host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  const injector = inject(Injector);
  return () =>
    afterNextRender(() => host.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus(), {
      injector,
    });
}

export function injectApiError(form: AbstractControl): WritableSignal<ApiError | undefined> {
  const error = signal<ApiError | undefined>(undefined);
  form.valueChanges.pipe(takeUntilDestroyed()).subscribe(() => error.set(undefined));
  return error;
}
