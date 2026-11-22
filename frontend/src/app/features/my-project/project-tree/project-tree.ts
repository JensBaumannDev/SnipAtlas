import { Component, input } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { TreeNode } from '../../../core/models/roadmap';
import { fileIcon, folderIcon } from '../../../core/ui/icons';

@Component({
  imports: [LucideDynamicIcon, TranslatePipe],
  selector: 'app-project-tree',
  styleUrl: './project-tree.scss',
  templateUrl: './project-tree.html',
})
export class ProjectTree {
  readonly nodes = input.required<TreeNode[]>();

  protected readonly fileIcon = fileIcon;
  protected readonly folderIcon = folderIcon;
}
