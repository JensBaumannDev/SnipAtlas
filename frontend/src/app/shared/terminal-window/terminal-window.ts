import { Component, computed, input } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';
import { CodeToken, highlight } from '../../core/content/code-highlight';
import { CodeLanguage } from '../../core/models/entry';

export type TerminalLineKind =
  'command' | 'code' | 'output' | 'comment' | 'error' | 'success' | 'done' | 'todo';

export interface TerminalLine {
  kind: TerminalLineKind;
  text: string;
  translate?: boolean;
  language?: CodeLanguage;
}

@Component({
  imports: [TranslatePipe],
  selector: 'app-terminal-window',
  styleUrl: './terminal-window.scss',
  templateUrl: './terminal-window.html',
})
export class TerminalWindow {
  readonly title = input.required<string>();
  readonly lines = input<TerminalLine[]>([]);
  readonly cwd = input('~');
  readonly cursor = input(true);

  protected readonly user = 'dev@snipatlas';
  protected readonly rendered = computed(() =>
    this.lines().map((line) => ({ ...line, tokens: this.tokens(line) })),
  );

  protected lineClass(kind: TerminalLineKind): string {
    return `terminal__line terminal__line--${kind}`;
  }

  protected tokenClass(token: CodeToken): string {
    return `terminal__token terminal__token--${token.kind}`;
  }

  private tokens(line: TerminalLine): CodeToken[] | undefined {
    if (line.kind === 'command') {
      return highlight(line.text, 'terminal')[0].tokens;
    }
    if (line.kind === 'code') {
      return highlight(line.text, line.language ?? 'typescript')[0].tokens;
    }
    return undefined;
  }
}
