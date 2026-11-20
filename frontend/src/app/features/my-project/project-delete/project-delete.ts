import { Component, inject, signal } from '@angular/core';
import { LucideDynamicIcon } from '@lucide/angular';
import { TranslatePipe } from '@ngx-translate/core';
import { finalize } from 'rxjs';
import { trashIcon, triangleAlertIcon } from '../../../core/ui/icons';
import { MyProject } from '../../../core/user-data/my-project';

@Component({
  imports: [LucideDynamicIcon, TranslatePipe],
  selector: 'app-project-delete',
  host: { '[class.project-delete--open]': 'confirming()' },
  styleUrl: './project-delete.scss',
  templateUrl: './project-delete.html',
})
export class ProjectDelete {
  private readonly project = inject(MyProject);

  protected readonly trashIcon = trashIcon;
  protected readonly alertIcon = triangleAlertIcon;

  protected readonly confirming = signal(false);
  protected readonly pending = signal(false);
  protected readonly failed = signal(false);

  protected cancel(): void {
    this.failed.set(false);
    this.confirming.set(false);
  }

  protected remove(): void {
    this.pending.set(true);
    this.failed.set(false);
    this.project
      .remove()
      .pipe(finalize(() => this.pending.set(false)))
      .subscribe({ error: () => this.failed.set(true) });
  }
}
