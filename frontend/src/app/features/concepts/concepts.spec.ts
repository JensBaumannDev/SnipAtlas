import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideTranslateService } from '@ngx-translate/core';
import { PageOutline } from '../../core/page-outline';
import { Concepts } from './concepts';

describe('Concepts', () => {
  let fixture: ComponentFixture<Concepts>;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Concepts],
      providers: [provideRouter([]), provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(Concepts);
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  async function open(topic: string, subtopic?: string): Promise<void> {
    fixture.componentRef.setInput('topic', topic);
    fixture.componentRef.setInput('subtopic', subtopic);
    await fixture.whenStable();
  }

  it('asks for a topic without one', () => {
    expect(element.querySelector('.concepts__empty')).toBeTruthy();
    expect(element.querySelector('app-concept-card')).toBeNull();
  });

  it('groups the concepts of a topic by subtopic', async () => {
    await open('python');

    const titles = [...element.querySelectorAll('.concepts__section-title')].map((title) => title.id);
    expect(titles).toEqual(['schleifen', 'listen', 'funktionen']);
    expect(element.querySelector('h1')?.textContent).toContain('Python');
  });

  it('shows only the concepts of the chosen subtopic', async () => {
    await open('python', 'schleifen');

    expect(element.querySelector('.concepts__section-title')).toBeNull();
    expect(element.querySelectorAll('app-concept-card').length).toBe(5);
    expect(element.querySelector('.concepts__parent')?.getAttribute('href')).toBe('/konzepte/python');
  });

  it('shows a hint for a subtopic without concepts', async () => {
    await open('python', 'dateien');

    expect(element.querySelector('app-concept-card')).toBeNull();
    expect(element.querySelector('.concepts__empty')).toBeTruthy();
  });

  it('publishes the sections as page outline', async () => {
    const outline = TestBed.inject(PageOutline);

    await open('python');
    expect(outline.items()[0]).toEqual({ id: 'schleifen', label: 'Schleifen' });

    await open('python', 'schleifen');
    expect(outline.items().map((item) => item.id)).toContain('while-schleife');

    fixture.destroy();
    expect(outline.items()).toEqual([]);
  });

  it('expands and collapses all concepts', async () => {
    await open('python', 'schleifen');
    const button = element.querySelector<HTMLButtonElement>('.concepts__header .btn');

    button?.click();
    await fixture.whenStable();
    expect(element.querySelectorAll('[aria-expanded="true"]').length).toBe(5);

    button?.click();
    await fixture.whenStable();
    expect(element.querySelectorAll('[aria-expanded="true"]').length).toBe(0);
  });
});
