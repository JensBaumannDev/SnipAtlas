import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { provideTranslateService } from '@ngx-translate/core';
import { PageOutline } from '../../core/page-outline';
import { Outline } from './outline';

@Component({ template: '' })
class Blank {}

describe('Outline', () => {
  let fixture: ComponentFixture<Outline>;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Outline],
      providers: [provideRouter([{ path: '**', component: Blank }]), provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(Outline);
    element = fixture.nativeElement;
    await TestBed.inject(Router).navigateByUrl('/befehle/git');
    await fixture.whenStable();
  });

  it('renders nothing without sections', () => {
    expect(element.querySelector('nav')).toBeNull();
  });

  it('links each section on the current page', async () => {
    TestBed.inject(PageOutline).set([
      { id: 'einrichten', label: 'Einrichten' },
      { id: 'alltag', label: 'Alltag' },
    ]);
    await fixture.whenStable();

    const links = [...element.querySelectorAll('a')];
    expect(links.map((link) => link.getAttribute('href'))).toEqual([
      '/befehle/git#einrichten',
      '/befehle/git#alltag',
    ]);
    expect(links[0].getAttribute('aria-current')).toBe('location');
  });
});
