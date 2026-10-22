import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideTranslateService } from '@ngx-translate/core';
import { Entry } from '../../../core/entry';
import { Preferences } from '../../../core/preferences';
import { EntryCard } from './entry-card';

const ENTRY: Entry = {
  slug: 'virtuelle-umgebung',
  topic: 'python',
  subtopic: 'umgebung-pakete',
  title: 'Virtuelle Umgebung anlegen',
  description: 'Jedes Projekt bekommt seine eigenen Pakete.',
  language: 'terminal',
  code: { win: 'python -m venv env', unix: 'python3 -m venv env' },
};

describe('EntryCard', () => {
  let fixture: ComponentFixture<EntryCard>;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EntryCard],
      providers: [provideTranslateService()],
    }).compileComponents();

    TestBed.inject(Preferences).setOs('win');
    fixture = TestBed.createComponent(EntryCard);
    fixture.componentRef.setInput('entry', ENTRY);
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  it('shows the title and the first code line while collapsed', () => {
    expect(element.querySelector('.entry-card__title')?.textContent).toContain(ENTRY.title);
    expect(element.querySelector('.entry-card__peek')?.textContent).toContain('python -m venv env');
    expect(element.querySelector<HTMLElement>('.entry-card__body')?.hidden).toBe(true);
  });

  it('expands on click', async () => {
    const toggle = element.querySelector<HTMLButtonElement>('.entry-card__toggle');
    toggle?.click();
    await fixture.whenStable();

    expect(toggle?.getAttribute('aria-expanded')).toBe('true');
    expect(element.querySelector<HTMLElement>('.entry-card__body')?.hidden).toBe(false);
    expect(element.querySelector('.entry-card__peek')).toBeNull();
  });

  it('follows the chosen operating system', async () => {
    TestBed.inject(Preferences).setOs('unix');
    await fixture.whenStable();

    expect(element.querySelector('.entry-card__peek')?.textContent).toContain('python3 -m venv env');
  });
});
