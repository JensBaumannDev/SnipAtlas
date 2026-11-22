import { Component, computed, inject, signal } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { of } from 'rxjs';
import { RoadmapApi } from '../../../core/api/roadmap-api';
import { TreeNode } from '../../../core/models/roadmap';
import { lightbulbIcon } from '../../../core/ui/icons';
import { MyProject } from '../../../core/user-data/my-project';
import { TopicHeader } from '../../../shared/topic-header/topic-header';
import { ProjectFolderContents } from '../project-folder-contents/project-folder-contents';
import { ProjectFolderTree } from '../project-folder-tree/project-folder-tree';
import { ProjectNavigation } from '../project-navigation/project-navigation';
import { findNode, folderOf, folderPaths } from '../tree-paths';

@Component({
  imports: [
    LucideDynamicIcon,
    ProjectFolderContents,
    ProjectFolderTree,
    ProjectNavigation,
    RouterLink,
    TopicHeader,
    TranslatePipe,
  ],
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

  protected readonly selected = signal('');
  protected readonly open = signal<ReadonlySet<string>>(new Set());
  protected readonly lightbulbIcon = lightbulbIcon;

  protected readonly folder = computed(() => {
    const root = rootNode(this.tree.value() ?? []);
    return findNode([root], folderOf(this.selected())) ?? root;
  });

  protected openFolder(path: string): void {
    this.selected.set(path);
    this.open.update((open) => new Set([...open, ...folderPaths(path)]));
  }
}

function rootNode(children: TreeNode[]): TreeNode {
  return { name: '', path: '', folder: true, tracked: true, children };
}
