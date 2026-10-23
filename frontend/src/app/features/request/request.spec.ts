import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideTranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { ContactRequest } from '../../core/contact-request';
import { RequestApi } from '../../core/request-api';
import { Request } from './request';

describe('Request', () => {
  let fixture: ComponentFixture<Request>;
  let element: HTMLElement;
  const sent: ContactRequest[] = [];

  function setValue(selector: string, value: string): void {
    const field = element.querySelector<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(selector);
    if (field) {
      field.value = value;
      field.dispatchEvent(new Event(field instanceof HTMLSelectElement ? 'change' : 'input'));
    }
  }

  async function chooseKind(index: number): Promise<void> {
    element.querySelectorAll<HTMLInputElement>('input[name="kind"]')[index]?.click();
    await fixture.whenStable();
  }

  async function fillContactAndSubmit(): Promise<void> {
    setValue('#request-email', 'test@beispiel.de');
    element.querySelector<HTMLInputElement>('input[name="privacy"]')?.click();
    element.querySelector<HTMLButtonElement>('button[type="submit"]')?.click();
    await fixture.whenStable();
  }

  beforeEach(async () => {
    sent.length = 0;
    await TestBed.configureTestingModule({
      imports: [Request],
      providers: [
        provideRouter([]),
        provideTranslateService(),
        {
          provide: RequestApi,
          useValue: {
            send: (request: ContactRequest) => {
              sent.push(request);
              return of(request);
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Request);
    element = fixture.nativeElement;
    await fixture.whenStable();
  });

  it('shows no type-specific fields before a type is chosen', () => {
    expect(element.querySelector('.request__fields')).toBeNull();
  });

  it('shows errors and sends nothing when the form is empty', async () => {
    element.querySelector<HTMLButtonElement>('button[type="submit"]')?.click();
    await fixture.whenStable();

    expect(element.querySelectorAll('.field__error').length).toBe(3);
    expect(sent).toEqual([]);
  });

  it('requires the fields of the chosen type', async () => {
    await chooseKind(0);
    await fillContactAndSubmit();

    expect(element.querySelectorAll('app-entry-fields .field__error').length).toBe(4);
    expect(sent).toEqual([]);
  });

  it('sends an entry suggestion', async () => {
    await chooseKind(0);
    setValue('#entry-area', 'command');
    setValue('#entry-topic', 'git');
    setValue('#entry-title', 'git rebase -i');
    setValue('#entry-reason', 'Damit räumt man Commits vor dem Push auf.');
    await fillContactAndSubmit();

    expect(sent).toEqual([
      {
        kind: 'entry',
        area: 'command',
        topic: 'git',
        title: 'git rebase -i',
        reason: 'Damit räumt man Commits vor dem Push auf.',
        example: '',
        source: '',
        email: 'test@beispiel.de',
      },
    ]);
    expect(element.querySelector('.request__done')).not.toBeNull();
  });

  it('sends an improvement', async () => {
    await chooseKind(1);
    setValue('#improvement-area', 'feature');
    setValue('#improvement-idea', 'Eine Merkliste für zuletzt kopierte Befehle.');
    await fillContactAndSubmit();

    expect(sent).toEqual([
      {
        kind: 'improvement',
        area: 'feature',
        idea: 'Eine Merkliste für zuletzt kopierte Befehle.',
        benefit: '',
        email: 'test@beispiel.de',
      },
    ]);
  });

  it('prefills a bug report from the reference and only sends the environment for broken pages', async () => {
    fixture.componentRef.setInput('bezug', 'git stash pop');
    await fixture.whenStable();

    expect(element.querySelector<HTMLInputElement>('#bug-location')?.value).toBe('git stash pop');

    setValue('#bug-type', 'outdated');
    await fixture.whenStable();
    expect(element.querySelector('#bug-environment')).toBeNull();

    setValue('#bug-problem', 'Der Befehl hat sich in Git 2.45 geändert.');
    await fillContactAndSubmit();

    expect(sent).toEqual([
      {
        kind: 'bug',
        type: 'outdated',
        location: 'git stash pop',
        problem: 'Der Befehl hat sich in Git 2.45 geändert.',
        correction: '',
        environment: '',
        email: 'test@beispiel.de',
      },
    ]);
  });
});
