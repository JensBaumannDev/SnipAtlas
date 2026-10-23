import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideTranslateService } from '@ngx-translate/core';
import { Concept } from '../../../core/concept';
import { ConceptCard } from './concept-card';

const CONCEPT: Concept = {
  slug: 'range',
  topic: 'python',
  subtopic: 'schleifen',
  title: 'Zählen mit range()',
  summary: 'Eine Schleife eine bestimmte Anzahl Male laufen lassen.',
  explanation: 'range(stop) erzeugt die Zahlen von 0 bis vor stop.',
  language: 'python',
  code: 'for i in range(5):\n    print(i)',
  note: 'Die 5 selbst ist nicht dabei.',
};

describe('ConceptCard', () => {
  let fixture: ComponentFixture<ConceptCard>;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConceptCard],
      providers: [provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(ConceptCard);
    fixture.componentRef.setInput('concept', CONCEPT);
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  it('shows the title and the summary while collapsed', () => {
    expect(element.querySelector('.concept-card__title')?.textContent).toContain(CONCEPT.title);
    expect(element.querySelector('.concept-card__summary')?.textContent).toContain(CONCEPT.summary);
    expect(element.querySelector<HTMLElement>('.concept-card__body')?.hidden).toBe(true);
  });

  it('expands on click', async () => {
    const toggle = element.querySelector<HTMLButtonElement>('.concept-card__toggle');
    toggle?.click();
    await fixture.whenStable();

    expect(toggle?.getAttribute('aria-expanded')).toBe('true');
    expect(element.querySelector<HTMLElement>('.concept-card__body')?.hidden).toBe(false);
    expect(element.querySelector('app-code-block')).toBeTruthy();
    expect(element.querySelector('.concept-card__note')?.textContent).toContain(CONCEPT.note);
  });

  it('leaves out the note when there is none', async () => {
    fixture.componentRef.setInput('concept', { ...CONCEPT, note: undefined });
    await fixture.whenStable();

    expect(element.querySelector('.concept-card__note')).toBeNull();
  });
});
