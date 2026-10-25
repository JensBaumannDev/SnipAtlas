import {
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  computed,
  inject,
  input,
  model,
  signal,
  viewChild,
} from '@angular/core';
import { LucideChevronDown, LucideStar } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { firstCodeLine } from '../../../core/code-highlight';
import { Entry } from '../../../core/entry';
import { Favorites } from '../../../core/favorites';
import { LoginDialog } from '../../../core/login-dialog';
import { resolveOsCode } from '../../../core/os-code';
import { Preferences } from '../../../core/preferences';
import { ProjectValues, fillPlaceholders } from '../../../core/project-values';
import { Session } from '../../../core/session';
import { CodeBlock } from '../../../shared/code-block/code-block';
import { ReportLink } from '../../../shared/report-link/report-link';
import { TermText } from '../../../shared/term-text/term-text';

@Component({
  imports: [CodeBlock, ReportLink, TermText, TranslatePipe, LucideChevronDown, LucideStar],
  selector: 'app-entry-card',
  styleUrl: './entry-card.scss',
  templateUrl: './entry-card.html',
})
export class EntryCard {
  private readonly os = inject(Preferences).os;
  private readonly project = inject(ProjectValues);
  private readonly favorites = inject(Favorites);
  private readonly session = inject(Session);
  private readonly loginDialog = inject(LoginDialog);
  private readonly injector = inject(Injector);
  private readonly star = viewChild.required<ElementRef<HTMLButtonElement>>('star');

  readonly entry = input.required<Entry>();
  readonly level = input<2 | 3>(3);
  readonly expanded = model(false);

  protected readonly resolved = computed(() => resolveOsCode(this.entry().code, this.os()));
  protected readonly peek = computed(() =>
    firstCodeLine(
      fillPlaceholders(this.resolved().code, this.project.values(), (key) => `<${key}>`),
    ),
  );
  protected readonly bodyId = computed(() => `${this.entry().slug}-body`);
  protected readonly favorite = computed(() => this.favorites.has(this.entry()));
  protected readonly loginHint = signal(false);

  protected toggleFavorite(): void {
    if (!this.session.user()) {
      this.loginHint.set(true);
      return;
    }
    this.favorites.toggle(this.entry());
  }

  protected async login(): Promise<void> {
    const dialogRef = await this.loginDialog.open();
    dialogRef.closed.subscribe(() => {
      if (!this.session.user()) {
        return;
      }
      this.loginHint.set(false);
      afterNextRender(() => this.star().nativeElement.focus(), { injector: this.injector });
    });
  }

  protected toggle(): void {
    this.expanded.update((expanded) => !expanded);
  }
}
