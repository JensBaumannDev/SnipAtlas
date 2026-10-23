import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { BlueprintApi } from './blueprint-api';
import { ConceptApi } from './concept-api';
import { ContentArea, ContentIndex } from './content-index';
import { EntryApi } from './entry-api';
import { ErrorApi } from './error-api';

@Service()
export class AreaContent {
  private readonly entryApi = inject(EntryApi);
  private readonly conceptApi = inject(ConceptApi);
  private readonly blueprintApi = inject(BlueprintApi);
  private readonly errorApi = inject(ErrorApi);

  getIndex(area: ContentArea): Observable<ContentIndex> {
    switch (area) {
      case 'commands':
        return this.entryApi.getIndex();
      case 'concepts':
        return this.conceptApi.getIndex();
      case 'blueprints':
        return this.blueprintApi.getIndex();
      case 'debugging':
        return this.errorApi.getIndex();
    }
  }
}
