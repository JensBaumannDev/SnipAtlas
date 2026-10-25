import { Component, ElementRef, inject, signal, viewChildren } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { combineLatest, map } from 'rxjs';
import { BlueprintApi } from '../../../core/blueprint-api';
import { ConceptApi } from '../../../core/concept-api';
import { DebugGuideApi } from '../../../core/debug-guide-api';
import { EntryApi } from '../../../core/entry-api';
import { ErrorApi } from '../../../core/error-api';
import { TerminalWindow } from '../../../shared/terminal-window/terminal-window';
import { OFFER_TABS, OfferArea } from './offer-tabs';

@Component({
  imports: [RouterLink, TerminalWindow, TranslatePipe],
  selector: 'app-offer',
  styleUrl: './offer.scss',
  templateUrl: './offer.html',
})
export class Offer {
  private readonly tabButtons = viewChildren<ElementRef<HTMLButtonElement>>('tab');

  protected readonly tabs = OFFER_TABS;
  protected readonly active = signal<OfferArea>('commands');

  protected readonly counts = toSignal(
    combineLatest([
      inject(EntryApi).getSummary(),
      inject(ConceptApi).getSummary(),
      inject(BlueprintApi).getSummary(),
      inject(ErrorApi).getSummary(),
      inject(DebugGuideApi).getAll(),
    ]).pipe(
      map(
        ([entries, concepts, blueprints, errors, guides]): Record<OfferArea, number> => ({
          commands: entries.entries,
          concepts: concepts.entries,
          blueprints: blueprints.blueprints,
          debugging: errors.entries + guides.length,
        }),
      ),
    ),
    { initialValue: { commands: 0, concepts: 0, blueprints: 0, debugging: 0 } },
  );

  protected select(area: OfferArea): void {
    this.active.set(area);
  }

  protected onKeydown(event: KeyboardEvent): void {
    const current = this.tabs.findIndex((tab) => tab.area === this.active());
    const last = this.tabs.length - 1;
    const next =
      {
        ArrowRight: current === last ? 0 : current + 1,
        ArrowLeft: current === 0 ? last : current - 1,
        Home: 0,
        End: last,
      }[event.key] ?? -1;

    if (next === -1) {
      return;
    }
    event.preventDefault();
    this.active.set(this.tabs[next].area);
    this.tabButtons()[next].nativeElement.focus();
  }
}
