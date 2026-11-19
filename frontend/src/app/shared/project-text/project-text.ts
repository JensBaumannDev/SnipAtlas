import { Pipe, PipeTransform, inject } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { ProjectValues, fillPlaceholders } from '../../core/user-data/project-values';

@Pipe({ name: 'projectText', pure: false })
export class ProjectTextPipe implements PipeTransform {
  private readonly values = inject(ProjectValues).values;
  private readonly translate = inject(TranslateService);

  transform(text: string | undefined): string {
    return fillPlaceholders(text ?? '', this.values(), (key) =>
      `<${this.translate.instant(`project.keys.${key}`)}>`,
    );
  }
}
