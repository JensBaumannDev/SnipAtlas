import { Component, input } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe],
  selector: 'app-area-info',
  styleUrl: './area-info.scss',
  templateUrl: './area-info.html',
})
export class AreaInfo {
  readonly area = input.required<string>();
  readonly sections = input.required<readonly string[]>();
}
