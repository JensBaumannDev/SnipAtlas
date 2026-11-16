import { Component, output } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe],
  selector: 'app-ai-notice',
  styleUrl: './ai-notice.scss',
  templateUrl: './ai-notice.html',
})
export class AiNotice {
  readonly confirmed = output();
}
