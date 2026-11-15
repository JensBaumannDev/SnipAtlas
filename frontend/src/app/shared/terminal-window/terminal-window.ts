import { Component, computed, input } from '@angular/core';
import { highlight } from '../../core/content/code-highlight';

@Component({
  selector: 'app-terminal-window',
  styleUrl: './terminal-window.scss',
  templateUrl: './terminal-window.html',
})
export class TerminalWindow {
  readonly title = input.required<string>();
  readonly command = input.required<string>();
  readonly cwd = input('~');
  readonly cursor = input(true);

  protected readonly user = 'dev@snipatlas';
  protected readonly tokens = computed(() => highlight(this.command(), 'terminal')[0].tokens);
}
