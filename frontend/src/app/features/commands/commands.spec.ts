import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideTranslateService } from '@ngx-translate/core';
import { PageOutline } from '../../core/page-outline';
import { Commands } from './commands';

describe('Commands', () => {
  let fixture: ComponentFixture<Commands>;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Commands],
      providers: [provideRouter([]), provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(Commands);
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  async function open(topic: string, subtopic?: string): Promise<void> {
    fixture.componentRef.setInput('topic', topic);
    fixture.componentRef.setInput('subtopic', subtopic);
    await fixture.whenStable();
  }

  it('shows the intro without a topic', () => {
    expect(element.querySelector('.commands__intro')).toBeTruthy();
    expect(element.querySelector('app-entry-card')).toBeNull();
  });

  it('groups the entries of a topic by subtopic', async () => {
    await open('git');

    const titles = [...element.querySelectorAll('.commands__section-title')].map((title) => title.id);
    expect(titles).toEqual(['einrichten', 'alltag', 'branches', 'rueckgaengig']);
    expect(element.querySelector('h1')?.textContent).toContain('Git & GitHub');
  });

  it('shows only the entries of the chosen subtopic', async () => {
    await open('git', 'alltag');

    expect(element.querySelector('.commands__section-title')).toBeNull();
    expect(element.querySelectorAll('app-entry-card').length).toBe(3);
    expect(element.querySelector('.commands__parent')?.getAttribute('href')).toBe('/befehle/git');
  });

  it('publishes the sections as page outline', async () => {
    const outline = TestBed.inject(PageOutline);

    await open('git');
    expect(outline.items()[0]).toEqual({ id: 'einrichten', label: 'Einrichten' });

    await open('git', 'alltag');
    expect(outline.items().map((item) => item.id)).toContain('verlauf-anzeigen');

    fixture.destroy();
    expect(outline.items()).toEqual([]);
  });

  it('expands and collapses all entries', async () => {
    await open('git', 'alltag');
    const button = element.querySelector<HTMLButtonElement>('.commands__header .btn');

    button?.click();
    await fixture.whenStable();
    expect(element.querySelectorAll('[aria-expanded="true"]').length).toBe(3);

    button?.click();
    await fixture.whenStable();
    expect(element.querySelectorAll('[aria-expanded="true"]').length).toBe(0);
  });
});
