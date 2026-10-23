import { Clipboard } from '@angular/cdk/clipboard';
import { Component, DestroyRef, computed, inject, input, signal } from '@angular/core';
import { LucideCheck, LucideCopy } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { CodeToken, highlight } from '../../../core/code-highlight';
import { CodeLanguage } from '../../../core/entry';
import { OperatingSystem } from '../../../core/preferences';

const COPIED_DURATION = 2000;

const LANGUAGE_LABELS: Record<CodeLanguage, string> = {
  terminal: 'Terminal',
  python: 'Python',
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  html: 'HTML',
  css: 'CSS',
  gitignore: '.gitignore',
};

@Component({
  imports: [TranslatePipe, LucideCheck, LucideCopy],
  selector: 'app-code-block',
  styleUrl: './code-block.scss',
  templateUrl: './code-block.html',
})
export class CodeBlock {
  private readonly clipboard = inject(Clipboard);
  private resetTimer?: ReturnType<typeof setTimeout>;

  readonly code = input.required<string>();
  readonly language = input.required<CodeLanguage>();
  readonly os = input<OperatingSystem>();

  protected readonly lines = computed(() => highlight(this.code(), this.language()));
  protected readonly languageLabel = computed(() => LANGUAGE_LABELS[this.language()]);
  protected readonly copied = signal(false);

  constructor() {
    inject(DestroyRef).onDestroy(() => clearTimeout(this.resetTimer));
  }

  protected copy(): void {
    if (!this.clipboard.copy(this.code())) {
      return;
    }
    this.copied.set(true);
    clearTimeout(this.resetTimer);
    this.resetTimer = setTimeout(() => this.copied.set(false), COPIED_DURATION);
  }

  protected tokenClass(token: CodeToken): string {
    return `code-block__token code-block__token--${token.kind}`;
  }
}
