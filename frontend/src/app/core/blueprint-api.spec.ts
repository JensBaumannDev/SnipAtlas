import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { BlueprintApi } from './blueprint-api';

describe('BlueprintApi', () => {
  it('uses unique blueprint slugs and unique step slugs per blueprint', async () => {
    const blueprints = await firstValueFrom(TestBed.inject(BlueprintApi).getAll());
    const slugs = blueprints.map((blueprint) => blueprint.slug);

    expect(new Set(slugs).size).toBe(slugs.length);
    for (const blueprint of blueprints) {
      const steps = blueprint.steps.map((step) => step.slug);
      expect(new Set(steps).size).toBe(steps.length);
    }
  });

  it('gives every step code to copy', async () => {
    const blueprints = await firstValueFrom(TestBed.inject(BlueprintApi).getAll());
    const empty = blueprints.flatMap((blueprint) =>
      blueprint.steps.filter((step) => !step.code.length).map((step) => step.slug),
    );
    expect(empty).toEqual([]);
  });

  it('finds a blueprint by its slug', async () => {
    const api = TestBed.inject(BlueprintApi);

    expect((await firstValueFrom(api.getBySlug('secret-key-in-env')))?.steps.length).toBe(6);
    expect(await firstValueFrom(api.getBySlug('gibt-es-nicht'))).toBeUndefined();
  });
});
