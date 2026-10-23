import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideTranslateService } from '@ngx-translate/core';
import { BlueprintStep } from '../../../core/blueprint';
import { Preferences } from '../../../core/preferences';
import { GuideStep } from './guide-step';

const STEP: BlueprintStep = {
  slug: 'virtuelle-umgebung',
  title: 'Virtuelle Umgebung einrichten',
  why: 'Jedes Projekt bekommt eigene Pakete.',
  code: [
    { language: 'terminal', code: { win: 'python -m venv env', unix: 'python3 -m venv env' } },
    { language: 'terminal', code: 'pip freeze' },
  ],
  note: 'Danach steht (env) vor der Eingabezeile.',
};

describe('GuideStep', () => {
  let fixture: ComponentFixture<GuideStep>;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GuideStep],
      providers: [provideTranslateService()],
    }).compileComponents();

    TestBed.inject(Preferences).setOs('unix');
    fixture = TestBed.createComponent(GuideStep);
    fixture.componentRef.setInput('step', STEP);
    fixture.componentRef.setInput('number', 2);
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  it('shows number, title, reason, code and note', () => {
    expect(element.querySelector('.guide-step__number')?.textContent).toBe('02');
    expect(element.querySelector('h2')?.textContent).toContain(STEP.title);
    expect(element.querySelector('.guide-step__why')?.textContent).toContain(STEP.why);
    expect(element.querySelectorAll('app-code-block').length).toBe(2);
    expect(element.querySelector('.guide-step__note')?.textContent).toContain(STEP.note);
  });

  it('uses the code for the chosen operating system', () => {
    expect(element.querySelector('app-code-block')?.textContent).toContain('python3 -m venv env');
  });

  it('reports a click on the checkbox', () => {
    const toggled = vi.fn();
    fixture.componentInstance.toggled.subscribe(toggled);

    element.querySelector<HTMLInputElement>('.guide-step__check')?.click();
    expect(toggled).toHaveBeenCalledOnce();
  });

  it('strikes through the title when done', async () => {
    fixture.componentRef.setInput('done', true);
    await fixture.whenStable();

    expect(element.querySelector('.guide-step--done')).toBeTruthy();
    expect(element.querySelector<HTMLInputElement>('.guide-step__check')?.checked).toBe(true);
  });
});
