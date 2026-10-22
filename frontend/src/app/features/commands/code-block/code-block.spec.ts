import { Clipboard } from '@angular/cdk/clipboard';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideTranslateService } from '@ngx-translate/core';
import { CodeBlock } from './code-block';

describe('CodeBlock', () => {
  let fixture: ComponentFixture<CodeBlock>;
  let element: HTMLElement;
  let copy: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    copy = vi.fn(() => true);

    await TestBed.configureTestingModule({
      imports: [CodeBlock],
      providers: [provideTranslateService(), { provide: Clipboard, useValue: { copy } }],
    }).compileComponents();

    fixture = TestBed.createComponent(CodeBlock);
    fixture.componentRef.setInput('code', 'git add .\n\n# danach\ngit push');
    fixture.componentRef.setInput('language', 'terminal');
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  it('renders one line per code line and a prompt for each command', () => {
    expect(element.querySelectorAll('.code-block__line').length).toBe(4);
    expect(element.querySelectorAll('.code-block__prompt').length).toBe(2);
  });

  it('copies the code without prompts', async () => {
    element.querySelector<HTMLButtonElement>('.code-block__copy')?.click();
    await fixture.whenStable();

    expect(copy).toHaveBeenCalledWith('git add .\n\n# danach\ngit push');
    expect(element.querySelector('.code-block__copy--done')).toBeTruthy();
  });

  it('shows the operating system only when given', async () => {
    expect(element.querySelector('.code-block__os')).toBeNull();

    fixture.componentRef.setInput('os', 'unix');
    await fixture.whenStable();

    expect(element.querySelector('.code-block__os')).toBeTruthy();
  });
});
