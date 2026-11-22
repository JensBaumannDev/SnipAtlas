import { Component, input, model } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { TreeNode } from '../../../core/models/roadmap';
import { chevronDownIcon, chevronRightIcon, fileIcon, folderIcon } from '../../../core/ui/icons';

@Component({
  imports: [LucideDynamicIcon, TranslatePipe],
  selector: 'app-project-folder-tree',
  styleUrl: './project-folder-tree.scss',
  templateUrl: './project-folder-tree.html',
})
export class ProjectFolderTree {
  readonly nodes = input.required<TreeNode[]>();
  readonly selected = model('');
  readonly open = model<ReadonlySet<string>>(new Set());

  protected readonly chevronDownIcon = chevronDownIcon;
  protected readonly chevronRightIcon = chevronRightIcon;
  protected readonly fileIcon = fileIcon;
  protected readonly folderIcon = folderIcon;

  protected choose(node: TreeNode): void {
    this.selected.set(node.path);
    if (node.folder) {
      this.toggle(node.path);
    }
  }

  private toggle(path: string): void {
    this.open.update((open) => {
      const next = new Set(open);
      if (!next.delete(path)) {
        next.add(path);
      }
      return next;
    });
  }
}
