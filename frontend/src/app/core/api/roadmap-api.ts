import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { cachedPerLanguage, cachedPerLanguageAndKey } from './api-request';
import { Roadmap, RoadmapBlock, TreeNode } from '../models/roadmap';

const URL = '/api/roadmap/';

export function choiceKey(blocks: readonly string[]): string {
  return [...blocks].sort().join(',');
}

@Service()
export class RoadmapApi {
  private readonly http = inject(HttpClient);

  readonly getBlocks = cachedPerLanguage(() => this.http.get<RoadmapBlock[]>(`${URL}blocks/`));

  private readonly roadmap = cachedPerLanguageAndKey((key) =>
    this.http.get<Roadmap>(URL, { params: { blocks: key } }),
  );

  private readonly tree = cachedPerLanguageAndKey((key) =>
    this.http.get<TreeNode[]>(`${URL}tree/`, { params: { blocks: key } }),
  );

  getRoadmap(blocks: readonly string[]): Observable<Roadmap> {
    return this.roadmap(choiceKey(blocks));
  }

  getTree(blocks: readonly string[]): Observable<TreeNode[]> {
    return this.tree(choiceKey(blocks));
  }
}
