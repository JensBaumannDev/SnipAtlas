import {
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  computed,
  inject,
  input,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { AreaColumns } from '../../core/content/area-columns';
import { AreaLink } from '../../core/content/area-links';
import { arrowRightIcon } from '../../core/ui/icons';
import { AiCodingNotice } from '../../core/user-data/ai-notice';
import { TopicLogo } from '../../shared/topic-logo/topic-logo';
import { AiNotice } from '../ai-notice/ai-notice';

@Component({
  imports: [AiNotice, LucideDynamicIcon, RouterLink, TopicLogo, TranslatePipe],
  selector: 'app-area-menu',
  styleUrl: './area-menu.scss',
  templateUrl: './area-menu.html',
})
export class AreaMenu {
  protected readonly arrowRightIcon = arrowRightIcon;

  private readonly notice = inject(AiCodingNotice);
  private readonly injector = inject(Injector);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;

  readonly link = input.required<AreaLink>();

  private readonly areaColumns = new AreaColumns(this.link);

  protected readonly loaded = this.areaColumns.loaded;
  protected readonly columns = this.areaColumns.columns;

  protected readonly noticeOpen = computed(
    () => this.link().area === 'ai' && !this.notice.confirmed(),
  );

  protected readonly hasDebugColumn = computed(() => this.link().area === 'debugging');

  protected confirmNotice(): void {
    this.notice.confirm();
    afterNextRender(() => this.host.querySelector<HTMLElement>('.area-menu__topic')?.focus(), {
      injector: this.injector,
    });
  }
}
