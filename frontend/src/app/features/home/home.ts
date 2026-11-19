import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { map } from 'rxjs';
import { NewsApi } from '../../core/api/news-api';
import { checkIcon } from '../../core/ui/icons';
import { MyProject } from '../../core/user-data/my-project';
import { SearchBox } from '../../shared/search-box/search-box';
import { AreaLinks } from '../../shared/area-links/area-links';
import { GuideLink } from './guide-link/guide-link';
import { NewsList } from './news-list/news-list';

const NEWS_LIMIT = 4;

@Component({
  imports: [AreaLinks, GuideLink, LucideDynamicIcon, NewsList, RouterLink, SearchBox, TranslatePipe],
  selector: 'app-home',
  styleUrl: './home.scss',
  templateUrl: './home.html',
})
export class Home {
  protected readonly myProject = inject(MyProject);
  protected readonly checkIcon = checkIcon;
  protected readonly projectPoints = [
    'myProject.home.points.why',
    'myProject.home.points.tree',
    'myProject.home.points.progress',
  ];
  protected readonly news = toSignal(
    inject(NewsApi)
      .getAll()
      .pipe(map((items) => items.slice(0, NEWS_LIMIT))),
    { initialValue: [] },
  );
}
