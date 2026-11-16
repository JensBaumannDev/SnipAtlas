import { Component } from '@angular/core';
import { botIcon } from '../../core/ui/icons';
import { AreaInfo } from '../../shared/area-info/area-info';
import { AreaIntro } from '../../shared/area-intro/area-intro';

@Component({
  imports: [AreaInfo, AreaIntro],
  selector: 'app-ai-coding',
  styleUrl: './ai-coding.scss',
  templateUrl: './ai-coding.html',
})
export class AiCoding {
  protected readonly icon = botIcon;
  protected readonly infoSections = ['what', 'why', 'start'];
}
