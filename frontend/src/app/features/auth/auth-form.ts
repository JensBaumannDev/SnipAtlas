import { ElementRef, Injector, afterNextRender, inject } from '@angular/core';
import { AbstractControl } from '@angular/forms';

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
