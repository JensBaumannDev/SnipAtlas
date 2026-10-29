import { Clipboard } from '@angular/cdk/clipboard';
import { Component, DestroyRef, computed, inject, input, signal } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe, TranslateService } from '@ngx-translate/core';
import { TokenKind, highlight } from '../../core/content/code-highlight';
import { CodeLanguage } from '../../core/models/entry';
import { checkIcon, copyIcon } from '../../core/ui/icons';
import { OperatingSystem } from '../../core/user-data/preferences';
import {
  ProjectKey,
  ProjectValues,
  fillPlaceholders,
  markPlaceholders,
  placeholderKeys,
  splitMarkers,
} from '../../core/user-data/project-values';
import { ProjectForm } from '../project-form/project-form';

const COPIED_DURATION = 2000;

const LANGUAGE_LABELS: Record<CodeLanguage, string> = {
  terminal: 'Terminal',
  python: 'Python',
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  html: 'HTML',
  css: 'CSS',
  gitignore: '.gitignore',
  env: '.env',
};

interface ViewToken {
  text: string;
  kind: TokenKind;
  key?: ProjectKey;
}

let nextId = 0;

@Component({
  imports: [ProjectForm, TranslatePipe, LucideDynamicIcon],
  selector: 'app-code-block',
  styleUrl: './code-block.scss',
  templateUrl: './code-block.html',
})
export class CodeBlock {
  private readonly clipboard = inject(Clipboard);
  private readonly translate = inject(TranslateService);
  private readonly project = inject(ProjectValues);
  private resetTimer?: ReturnType<typeof setTimeout>;

  readonly code = input.required<string>();
  readonly language = input.required<CodeLanguage>();
  readonly os = input<OperatingSystem>();

  protected readonly checkIcon = checkIcon;
  protected readonly copyIcon = copyIcon;
  protected readonly formId = `code-block-project-${nextId++}`;
  protected readonly keys = computed(() => placeholderKeys(this.code()));
  protected readonly missing = computed(
    () => this.keys().filter((key) => !this.project.values()[key]?.trim()).length,
  );
  protected readonly lines = computed(() => {
    const values = this.project.values();
    return highlight(markPlaceholders(this.code()), this.language()).map((line) => ({
      prompt: line.prompt,
      tokens: line.tokens.flatMap((token) =>
        splitMarkers(token.text).map<ViewToken>(({ text, key }) =>
          key
            ? { text: values[key]?.trim() ?? '', kind: token.kind, key }
            : { text, kind: token.kind },
        ),
      ),
    }));
  });
  protected readonly languageLabel = computed(() => LANGUAGE_LABELS[this.language()]);
  protected readonly copied = signal(false);
  protected readonly editing = signal(false);

  constructor() {
    inject(DestroyRef).onDestroy(() => clearTimeout(this.resetTimer));
  }

  protected copy(): void {
    const code = fillPlaceholders(
      this.code(),
      this.project.values(),
      (key) => `<${this.translate.instant(`project.keys.${key}`)}>`,
    );
    if (!this.clipboard.copy(code)) {
      return;
    }
    this.copied.set(true);
    clearTimeout(this.resetTimer);
    this.resetTimer = setTimeout(() => this.copied.set(false), COPIED_DURATION);
  }

  protected toggleEditing(): void {
    this.editing.update((editing) => !editing);
  }

  protected tokenClass(token: ViewToken): string {
    return `code-block__token code-block__token--${token.kind}`;
  }
}
