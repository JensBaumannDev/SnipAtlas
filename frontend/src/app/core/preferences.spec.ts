import { TestBed } from '@angular/core/testing';
import { TranslateService, provideTranslateService } from '@ngx-translate/core';
import { Preferences } from './preferences';

describe('Preferences', () => {
  let service: Preferences;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideTranslateService()],
    });
    service = TestBed.inject(Preferences);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should apply and store the language', () => {
    service.setLanguage('en');
    TestBed.tick();

    expect(document.documentElement.lang).toBe('en');
    expect(TestBed.inject(TranslateService).getCurrentLang()).toBe('en');
    expect(localStorage.getItem('snipatlas-language')).toBe('en');
  });
});
