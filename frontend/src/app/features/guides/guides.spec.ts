import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideTranslateService } from '@ngx-translate/core';
import { BlueprintProgress } from '../../core/blueprint-progress';
import { Guides } from './guides';

describe('Guides', () => {
  let fixture: ComponentFixture<Guides>;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Guides],
      providers: [provideRouter([]), provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(Guides);
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  afterEach(() => localStorage.removeItem('snipatlas-progress'));

  it('groups the blueprints by topic and links them below their topic', () => {
    const sections = [...element.querySelectorAll('.guides__section-title')].map((title) => title.id);
    const links = [...element.querySelectorAll('.guides__link')].map((link) => link.getAttribute('href'));

    expect(sections).toEqual(['django']);
    expect(links).toContain('/bauplaene/django/django-projekt-anlegen');
  });

  it('shows only the blueprints of the chosen topic', async () => {
    fixture.componentRef.setInput('topic', 'django');
    await fixture.whenStable();

    expect(element.querySelector('h1')?.textContent).toContain('Django');
    expect(element.querySelector('.guides__section-title')).toBeNull();
    expect(element.querySelectorAll('.guides__item').length).toBe(3);
  });

  it('shows a hint for a topic without blueprints', async () => {
    fixture.componentRef.setInput('topic', 'css');
    await fixture.whenStable();

    expect(element.querySelector('.guides__item')).toBeNull();
    expect(element.querySelector('.guides__empty')).toBeTruthy();
  });

  it('shows the progress of each blueprint', async () => {
    TestBed.inject(BlueprintProgress).toggle('django-projekt-klonen', 'repo-klonen');
    await fixture.whenStable();

    const values = [...element.querySelectorAll('[role="progressbar"]')].map((bar) =>
      bar.getAttribute('aria-valuenow'),
    );
    expect(values).toEqual(['0', '1', '0']);
  });
});
