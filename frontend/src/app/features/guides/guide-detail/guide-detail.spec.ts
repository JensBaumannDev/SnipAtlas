import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideTranslateService } from '@ngx-translate/core';
import { PageOutline } from '../../../core/page-outline';
import { GuideDetail } from './guide-detail';

describe('GuideDetail', () => {
  let fixture: ComponentFixture<GuideDetail>;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GuideDetail],
      providers: [provideRouter([]), provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(GuideDetail);
    fixture.componentRef.setInput('topic', 'django');
    fixture.componentRef.setInput('slug', 'secret-key-in-env');
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  afterEach(() => localStorage.removeItem('snipatlas-progress'));

  function progressValue(): string | null | undefined {
    return element.querySelector('[role="progressbar"]')?.getAttribute('aria-valuenow');
  }

  it('lists every step of the blueprint', () => {
    expect(element.querySelector('h1')?.textContent).toContain('SECRET_KEY');
    expect(element.querySelectorAll('app-guide-step').length).toBe(6);
  });

  it('grows the progress with every ticked step and resets it', async () => {
    const checks = element.querySelectorAll<HTMLInputElement>('.guide-step__check');

    checks[0].click();
    checks[1].click();
    await fixture.whenStable();
    expect(progressValue()).toBe('2');

    element.querySelector<HTMLButtonElement>('.guide-detail__progress .btn')?.click();
    await fixture.whenStable();
    expect(progressValue()).toBe('0');
  });

  it('publishes the steps as page outline', () => {
    const outline = TestBed.inject(PageOutline);

    expect(outline.items()[0]).toEqual({ id: 'env-anlegen', label: '.env im Projektordner anlegen' });

    fixture.destroy();
    expect(outline.items()).toEqual([]);
  });

  it('links back to the topic', () => {
    const parent = element.querySelector('.guide-detail__parent');
    expect(parent?.getAttribute('href')).toBe('/bauplaene/django');
    expect(parent?.textContent).toContain('Django');
  });

  it('shows a hint when the blueprint belongs to another topic', async () => {
    fixture.componentRef.setInput('topic', 'angular');
    await fixture.whenStable();

    expect(element.querySelector('app-guide-step')).toBeNull();
    expect(element.querySelector('.guide-detail__empty')).toBeTruthy();
  });

  it('shows a hint for an unknown blueprint', async () => {
    fixture.componentRef.setInput('slug', 'gibt-es-nicht');
    await fixture.whenStable();

    expect(element.querySelector('app-guide-step')).toBeNull();
    expect(element.querySelector('.guide-detail__empty')).toBeTruthy();
  });
});
