import { Component } from '@angular/core';
import { botIcon } from '../../core/ui/icons';
import { AreaInfo } from '../../shared/area-info/area-info';
import { AreaIntro } from '../../shared/area-intro/area-intro';
import { AreaTopics } from '../../shared/area-topics/area-topics';

@Component({
  imports: [AreaInfo, AreaIntro, AreaTopics],
  selector: 'app-ai-coding',
  styleUrl: './ai-coding.scss',
  templateUrl: './ai-coding.html',
})
export class AiCoding {
  protected readonly icon = botIcon;
  protected readonly infoSections = ['what', 'why', 'start'];
}
