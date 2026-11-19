import { Component, inject } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { of } from 'rxjs';
import { RoadmapApi } from '../../../core/api/roadmap-api';
import { MyProject } from '../../../core/user-data/my-project';
import { TopicHeader } from '../../../shared/topic-header/topic-header';
import { ProjectNavigation } from '../project-navigation/project-navigation';
import { ProjectTree } from '../project-tree/project-tree';

@Component({
  imports: [ProjectNavigation, ProjectTree, RouterLink, TopicHeader, TranslatePipe],
  selector: 'app-project-structure',
  styleUrl: './project-structure.scss',
  templateUrl: './project-structure.html',
})
export class ProjectStructure {
  private readonly api = inject(RoadmapApi);
  protected readonly project = inject(MyProject);

  protected readonly tree = rxResource({
    params: () => this.project.blocks(),
    stream: ({ params }) => (params.length ? this.api.getTree(params) : of(undefined)),
  });
}
