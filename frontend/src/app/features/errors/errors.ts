import { Component, input } from '@angular/core';
import { LucideListTree, LucideMessageSquarePlus, LucideSearch } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { AreaHint, AreaIntro } from '../../shared/area-intro/area-intro';

const HINTS: AreaHint[] = [
  {
    icon: LucideListTree,
    title: 'debugging.hints.choose.title',
    text: 'debugging.hints.choose.text',
  },
  { icon: LucideSearch, title: 'debugging.hints.solve.title', text: 'debugging.hints.solve.text' },
  {
    icon: LucideMessageSquarePlus,
    title: 'debugging.hints.request.title',
    text: 'debugging.hints.request.text',
    link: { label: 'debugging.hints.requestLink', path: '/anfrage' },
  },
];

@Component({
  imports: [AreaIntro, TranslatePipe],
  selector: 'app-errors',
  styleUrl: './errors.scss',
  templateUrl: './errors.html',
})
export class Errors {
  readonly topic = input<string>();

  protected readonly hints = HINTS;
}
