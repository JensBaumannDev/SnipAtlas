import { Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { NewsItem } from '../../core/news';
import { TerminalLine, TerminalWindow } from '../terminal-window/terminal-window';

const FRESH_DAYS = 14;
const DAY = 24 * 60 * 60 * 1000;

@Component({
  imports: [RouterLink, TerminalWindow, TranslatePipe],
  selector: 'app-news-log',
  styleUrl: './news-log.scss',
  templateUrl: './news-log.html',
})
export class NewsLog {
  readonly items = input.required<NewsItem[]>();
  readonly command = input('snipatlas log');

  protected readonly lines = computed((): TerminalLine[] => [
    { kind: 'command', text: this.command() },
  ]);

  protected readonly rows = computed(() => {
    const freshSince = Date.now() - FRESH_DAYS * DAY;
    return this.items().map((item) => ({
      ...item,
      fresh: new Date(item.date).getTime() >= freshSince,
    }));
  });
}
