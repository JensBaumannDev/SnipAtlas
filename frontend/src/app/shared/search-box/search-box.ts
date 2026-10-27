import {
  Component,
  ElementRef,
  Injector,
  computed,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';
import { Router } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import type { ContentSearch } from '../../core/content-search';
import { searchIcon } from '../../core/icons';
import { SearchResult } from '../../core/search-result';

@Component({
  imports: [TranslatePipe, LucideDynamicIcon],
  selector: 'app-search-box',
  styleUrl: './search-box.scss',
  templateUrl: './search-box.html',
  host: {
    '(document:keydown)': 'onShortcut($event)',
  },
})
export class SearchBox {
  private readonly injector = inject(Injector);
  private readonly router = inject(Router);
  private readonly input = viewChild.required<ElementRef<HTMLInputElement>>('input');
  private readonly engine = signal<ContentSearch | undefined>(undefined);

  readonly inputId = input.required<string>();
  readonly variant = input<'bar' | 'hero'>('bar');
  readonly placeholder = input('search.placeholder');
  readonly shortcut = input(false);

  protected readonly searchIcon = searchIcon;
  protected readonly query = signal('');
  protected readonly open = signal(false);
  protected readonly active = signal(-1);

  protected readonly hasQuery = computed(() => this.query().trim() !== '');
  protected readonly results = computed(() => this.engine()?.search(this.query()) ?? []);
  protected readonly expanded = computed(
    () => this.open() && this.hasQuery() && this.results().length > 0,
  );
  protected readonly listId = computed(() => `${this.inputId()}-results`);
  protected readonly activeId = computed(() =>
    this.expanded() && this.active() >= 0 ? this.optionId(this.active()) : null,
  );

  focus(): void {
    this.input().nativeElement.focus();
  }

  search(text: string): void {
    this.query.set(text);
    this.active.set(-1);
    this.focus();
  }

  protected optionId(index: number): string {
    return `${this.inputId()}-option-${index}`;
  }

  protected async onFocus(): Promise<void> {
    this.open.set(true);
    if (this.engine()) {
      return;
    }
    const { ContentSearch } = await import('../../core/content-search');
    this.engine.set(this.injector.get(ContentSearch));
  }

  protected onInput(event: Event): void {
    if (event.target instanceof HTMLInputElement) {
      this.query.set(event.target.value);
    }
    this.open.set(true);
    this.active.set(-1);
  }

  protected onKeydown(event: KeyboardEvent): void {
    const count = this.results().length;
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        this.open.set(true);
        this.active.update((index) => (count ? (index + 1) % count : -1));
        break;
      case 'ArrowUp':
        event.preventDefault();
        this.active.update((index) => (count ? (index - 1 + count) % count : -1));
        break;
      case 'Enter': {
        const result = this.results()[Math.max(this.active(), 0)];
        if (this.expanded() && result) {
          event.preventDefault();
          this.go(result);
        }
        break;
      }
      case 'Escape':
        if (this.expanded()) {
          event.preventDefault();
          this.close();
        }
        break;
    }
  }

  protected onShortcut(event: KeyboardEvent): void {
    if (this.shortcut() && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      this.focus();
    }
  }

  protected go(result: SearchResult): void {
    this.router.navigate(result.link, { fragment: result.fragment });
    this.query.set('');
    this.close();
    this.input().nativeElement.blur();
  }

  protected close(): void {
    this.open.set(false);
    this.active.set(-1);
  }
}
