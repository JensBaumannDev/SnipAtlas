import { Component, computed, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { TreeNode } from '../../../core/models/roadmap';
import { arrowRightIcon, fileIcon, folderIcon } from '../../../core/ui/icons';
import { folderPaths } from '../tree-paths';

@Component({
  imports: [LucideDynamicIcon, RouterLink, TranslatePipe],
  selector: 'app-project-folder-contents',
  styleUrl: './project-folder-contents.scss',
  templateUrl: './project-folder-contents.html',
})
export class ProjectFolderContents {
  readonly folder = input.required<TreeNode>();
  readonly selected = input('');
  readonly opened = output<string>();

  protected readonly crumbs = computed(() =>
    folderPaths(this.folder().path).map((path) => ({ path, name: path.split('/').at(-2) })),
  );

  protected readonly arrowRightIcon = arrowRightIcon;
  protected readonly fileIcon = fileIcon;
  protected readonly folderIcon = folderIcon;
}
