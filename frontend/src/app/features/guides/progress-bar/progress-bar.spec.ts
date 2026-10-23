import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideTranslateService } from '@ngx-translate/core';
import { ProgressBar } from './progress-bar';

describe('ProgressBar', () => {
  let fixture: ComponentFixture<ProgressBar>;
  let element: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProgressBar],
      providers: [provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(ProgressBar);
    fixture.componentRef.setInput('done', 1);
    fixture.componentRef.setInput('total', 4);
    fixture.componentRef.setInput('label', 'Fortschritt');
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  it('fills the bar by the share of done steps', () => {
    const track = element.querySelector('[role="progressbar"]');

    expect(track?.getAttribute('aria-valuenow')).toBe('1');
    expect(track?.getAttribute('aria-valuemax')).toBe('4');
    expect(element.querySelector<HTMLElement>('.progress-bar__fill')?.style.width).toBe('25%');
  });

  it('marks the bar as complete when all steps are done', async () => {
    fixture.componentRef.setInput('done', 4);
    await fixture.whenStable();

    expect(element.querySelector<HTMLElement>('.progress-bar__fill')?.style.width).toBe('100%');
    expect(element.querySelector('.progress-bar__text--complete')).toBeTruthy();
  });
});
