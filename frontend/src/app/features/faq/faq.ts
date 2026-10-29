import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { chevronDownIcon } from '../../core/ui/icons';

interface FaqGroup {
  id: string;
  questions: string[];
}

const GROUPS: FaqGroup[] = [
  { id: 'content', questions: ['what', 'tested', 'os', 'wrong'] },
  { id: 'account', questions: ['needed', 'stored', 'delete'] },
  { id: 'costs', questions: ['free'] },
  { id: 'requests', questions: ['suggest', 'answer'] },
];

@Component({
  imports: [RouterLink, TranslatePipe, LucideDynamicIcon],
  selector: 'app-faq',
  styleUrl: './faq.scss',
  templateUrl: './faq.html',
})
export class Faq {
  protected readonly chevronDownIcon = chevronDownIcon;
  protected readonly groups = GROUPS;
}
