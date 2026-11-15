import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon, LucideIconData } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { catchError, combineLatest, map, of } from 'rxjs';
import { BlueprintApi } from '../../../core/api/blueprint-api';
import { ConceptApi } from '../../../core/api/concept-api';
import { DebugGuideApi } from '../../../core/api/debug-guide-api';
import { EntryApi } from '../../../core/api/entry-api';
import { ErrorApi } from '../../../core/api/error-api';
import { bookTextIcon, routeIcon, terminalIcon, triangleAlertIcon } from '../../../core/ui/icons';

type CardArea = 'commands' | 'concepts' | 'blueprints' | 'debugging';

interface AreaCard {
  area: CardArea;
  path: string;
  icon: LucideIconData;
}

const CARDS: AreaCard[] = [
  { area: 'commands', path: '/befehle', icon: terminalIcon },
  { area: 'concepts', path: '/grundlagen', icon: bookTextIcon },
  { area: 'blueprints', path: '/anleitungen', icon: routeIcon },
  { area: 'debugging', path: '/fehler', icon: triangleAlertIcon },
];

@Component({
  imports: [LucideDynamicIcon, RouterLink, TranslatePipe],
  selector: 'app-area-cards',
  styleUrl: './area-cards.scss',
  templateUrl: './area-cards.html',
})
export class AreaCards {
  protected readonly cards = CARDS;

  protected readonly counts = toSignal(
    combineLatest([
      inject(EntryApi).getSummary(),
      inject(ConceptApi).getSummary(),
      inject(BlueprintApi).getSummary(),
      inject(ErrorApi).getSummary(),
      inject(DebugGuideApi).getAll(),
    ]).pipe(
      map(([entries, concepts, blueprints, errors, guides]): Record<CardArea, number> => ({
        commands: entries.entries,
        concepts: concepts.entries,
        blueprints: blueprints.blueprints,
        debugging: errors.entries + guides.length,
      })),
      catchError(() => of(undefined)),
    ),
  );
}
