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

  function isCollapsed(topic: string): boolean | undefined {
    return element.querySelector<HTMLElement>(`#sidebar-topic-${topic}`)?.closest<HTMLElement>('.sidebar__collapse')?.inert;
  }

  function isGroupCollapsed(group: string): boolean | undefined {
    return element.querySelector<HTMLElement>(`#sidebar-group-list-${group}`)?.inert;
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
    expect(isCollapsed('git')).toBe(true);

    toggle?.click();
    await fixture.whenStable();

    expect(toggle?.getAttribute('aria-expanded')).toBe('true');
    expect(isCollapsed('git')).toBe(false);
  });

  it('keeps only one topic expanded', async () => {
    element.querySelector<HTMLButtonElement>('[aria-controls="sidebar-topic-git"]')?.click();
    await fixture.whenStable();
    element.querySelector<HTMLButtonElement>('[aria-controls="sidebar-topic-docker"]')?.click();
    await fixture.whenStable();

    expect(isCollapsed('git')).toBe(true);
    expect(isCollapsed('docker')).toBe(false);
  });

  it('expands the active topic after navigation', async () => {
    await navigate('/befehle/python/schleifen');

    expect(isCollapsed('python')).toBe(false);
    expect(element.querySelector('.sidebar__toggle-label')?.textContent).toContain('Python');
  });

  it('collapses a group on click', async () => {
    expect(isGroupCollapsed('tools')).toBe(false);

    element.querySelector<HTMLButtonElement>('[aria-controls="sidebar-group-list-tools"]')?.click();
    await fixture.whenStable();

    expect(isGroupCollapsed('tools')).toBe(true);
  });

  it('opens only the group of the active topic when entering an area', async () => {
    await navigate('/anfrage');
    await navigate('/befehle/python');

    expect(isGroupCollapsed('backend')).toBe(false);
    expect(isGroupCollapsed('frontend')).toBe(true);
    expect(isGroupCollapsed('tools')).toBe(true);
  });
});
