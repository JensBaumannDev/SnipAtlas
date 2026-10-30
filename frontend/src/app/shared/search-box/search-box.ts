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
import type { ContentSearch } from '../../core/content/content-search';
import { searchIcon, xIcon } from '../../core/ui/icons';
import { SearchResult } from '../../core/models/search-result';

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
  protected readonly clearIcon = xIcon;
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

  private readonly keyActions: Partial<Record<string, () => boolean>> = {
    ArrowDown: () => {
      this.open.set(true);
      return this.moveActive(1);
    },
    ArrowUp: () => this.moveActive(-1),
    Enter: () => this.goToActive(),
    Escape: () => this.closeIfOpen(),
  };

  focus(): void {
    this.input().nativeElement.focus();
  }

  search(text: string): void {
    this.query.set(text);
    this.active.set(-1);
    this.focus();
  }

  protected clearSearch(): void {
    this.query.set('');
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
    const { ContentSearch } = await import('../../core/content/content-search');
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
    if (this.keyActions[event.key]?.()) {
      event.preventDefault();
    }
  }

  protected onShortcut(event: KeyboardEvent): void {
    if (this.shortcut() && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      this.focus();
    }
  }

  protected go(result: SearchResult): void {
    this.router.navigate(result.link, {
      fragment: result.fragment,
      queryParams: result.query ? { q: result.query } : undefined,
    });
    this.query.set('');
    this.close();
    this.input().nativeElement.blur();
  }

  protected close(): void {
    this.open.set(false);
    this.active.set(-1);
  }

  private moveActive(step: 1 | -1): boolean {
    const count = this.results().length;
    this.active.update((index) => (count ? (index + step + count) % count : -1));
    return true;
  }

  private goToActive(): boolean {
    const result = this.results()[Math.max(this.active(), 0)];
    if (!this.expanded() || !result) {
      return false;
    }
    this.go(result);
    return true;
  }

  private closeIfOpen(): boolean {
    if (!this.expanded()) {
      return false;
    }
    this.close();
    return true;
  }
}
