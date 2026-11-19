import { Signal, computed, inject } from '@angular/core';
import { rxResource, toSignal } from '@angular/core/rxjs-interop';
import { of } from 'rxjs';
import { RoadmapApi } from '../../core/api/roadmap-api';
import { stepRefs } from '../../core/content/roadmap-steps';
import { MyProject } from '../../core/user-data/my-project';

export function injectRoadmap() {
  const api = inject(RoadmapApi);
  const project = inject(MyProject);
  const resource = rxResource({
    params: () => project.blocks(),
    stream: ({ params }) => (params.length ? api.getRoadmap(params) : of(undefined)),
  });
  const refs = computed(() => {
    const roadmap = resource.value();
    return roadmap ? stepRefs(roadmap) : [];
  });
  return { project, resource, refs, chosenNames: injectChosenNames(project) };
}

function injectChosenNames(project: MyProject): Signal<string[]> {
  const blocks = toSignal(inject(RoadmapApi).getBlocks(), { initialValue: [] });
  return computed(() =>
    blocks()
      .filter((block) => project.blocks().includes(block.slug))
      .map((block) => block.name),
  );
}
