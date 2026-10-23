import { Service, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { BlueprintApi } from './blueprint-api';
import { ConceptApi } from './concept-api';
import { ContentArea, ContentIndex } from './content-index';
import { EntryApi } from './entry-api';

@Service()
export class AreaContent {
  private readonly entryApi = inject(EntryApi);
  private readonly conceptApi = inject(ConceptApi);
  private readonly blueprintApi = inject(BlueprintApi);

  getIndex(area: ContentArea): Observable<ContentIndex> {
    switch (area) {
      case 'commands':
        return this.entryApi.getIndex();
      case 'concepts':
        return this.conceptApi.getIndex();
      case 'blueprints':
        return this.blueprintApi.getIndex();
      case 'debugging':
        return of({});
    }
  }
}
