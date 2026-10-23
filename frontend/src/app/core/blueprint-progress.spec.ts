import { TestBed } from '@angular/core/testing';
import { BlueprintProgress } from './blueprint-progress';

const KEY = 'snipatlas-progress';

describe('BlueprintProgress', () => {
  afterEach(() => localStorage.removeItem(KEY));

  it('toggles steps and stores them in the browser', () => {
    const progress = TestBed.inject(BlueprintProgress);

    progress.toggle('django', 'ordner');
    progress.toggle('django', 'venv');
    progress.toggle('django', 'ordner');
    TestBed.tick();

    expect(progress.doneSteps('django')).toEqual(['venv']);
    expect(JSON.parse(localStorage.getItem(KEY) ?? '')).toEqual({ django: ['venv'] });
  });

  it('resets one blueprint and keeps the others', () => {
    const progress = TestBed.inject(BlueprintProgress);

    progress.toggle('django', 'ordner');
    progress.toggle('env', 'anlegen');
    progress.reset('django');

    expect(progress.doneSteps('django')).toEqual([]);
    expect(progress.doneSteps('env')).toEqual(['anlegen']);
  });

  it('restores stored progress', () => {
    localStorage.setItem(KEY, JSON.stringify({ django: ['ordner'] }));
    expect(TestBed.inject(BlueprintProgress).doneSteps('django')).toEqual(['ordner']);
  });

  it('ignores invalid stored data', () => {
    localStorage.setItem(KEY, '{"django": "ordner"}');
    expect(TestBed.inject(BlueprintProgress).done()).toEqual({});
  });
});
