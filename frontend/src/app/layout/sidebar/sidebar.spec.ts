import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { provideTranslateService } from '@ngx-translate/core';
import { Sidebar } from './sidebar';

@Component({ template: '' })
class Blank {}

describe('Sidebar', () => {
  let fixture: ComponentFixture<Sidebar>;
  let element: HTMLElement;

  async function navigate(url: string): Promise<void> {
    await TestBed.inject(Router).navigateByUrl(url);
    await fixture.whenStable();
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Sidebar],
      providers: [
        provideRouter([
          { path: 'befehle', data: { sidebar: 'subtopics' }, children: [{ path: '**', component: Blank }] },
          { path: 'konzepte', data: { sidebar: 'subtopics' }, children: [{ path: '**', component: Blank }] },
          { path: 'debugging', data: { sidebar: 'topics' }, children: [{ path: '**', component: Blank }] },
          { path: '**', component: Blank },
        ]),
        provideTranslateService(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Sidebar);
    element = fixture.nativeElement;
    await navigate('/befehle');
  });

  it('shows the collection first, then the groups', () => {
    const headings = element.querySelectorAll('.sidebar__heading');
    expect(headings.length).toBe(4);
    expect(headings[0].id).toBe('sidebar-group-collection');
  });

  it('links topics and subtopics to readable URLs', () => {
    expect(element.querySelector('a[href="/befehle/git"]')).toBeTruthy();
    expect(element.querySelector('a[href="/befehle/git/stash"]')).toBeTruthy();
  });

  it('links into the current area', async () => {
    await navigate('/konzepte');
    expect(element.querySelector('a[href="/konzepte/python/listen"]')).toBeTruthy();
    expect(element.querySelector('a[href^="/befehle"]')).toBeNull();
  });

  it('shows topics without subtopics in debugging', async () => {
    await navigate('/debugging');
    expect(element.querySelector('a[href="/debugging/django"]')).toBeTruthy();
    expect(element.querySelector('.sidebar__subtopics')).toBeNull();
    expect(element.querySelector('.sidebar__expand')).toBeNull();
  });

  it('is hidden in areas without topics', async () => {
    await navigate('/anfrage');
    expect(element.hidden).toBe(true);
  });

  it('expands subtopics on click', async () => {
    const toggle = element.querySelector<HTMLButtonElement>('[aria-controls="sidebar-topic-git"]');
    const list = element.querySelector<HTMLUListElement>('#sidebar-topic-git');
    expect(list?.hidden).toBe(true);

    toggle?.click();
    await fixture.whenStable();

    expect(toggle?.getAttribute('aria-expanded')).toBe('true');
    expect(list?.hidden).toBe(false);
  });

  it('keeps only one topic expanded', async () => {
    element.querySelector<HTMLButtonElement>('[aria-controls="sidebar-topic-git"]')?.click();
    await fixture.whenStable();
    element.querySelector<HTMLButtonElement>('[aria-controls="sidebar-topic-docker"]')?.click();
    await fixture.whenStable();

    expect(element.querySelector<HTMLUListElement>('#sidebar-topic-git')?.hidden).toBe(true);
    expect(element.querySelector<HTMLUListElement>('#sidebar-topic-docker')?.hidden).toBe(false);
  });

  it('expands the active topic after navigation', async () => {
    await navigate('/befehle/python/schleifen');

    expect(element.querySelector<HTMLUListElement>('#sidebar-topic-python')?.hidden).toBe(false);
    expect(element.querySelector('.sidebar__toggle-label')?.textContent).toContain('Python');
  });
});
