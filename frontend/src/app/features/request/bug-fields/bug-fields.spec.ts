import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NonNullableFormBuilder } from '@angular/forms';
import { provideTranslateService } from '@ngx-translate/core';
import { createRequestForm } from '../request-form';
import { BugFields } from './bug-fields';

describe('BugFields', () => {
  let fixture: ComponentFixture<BugFields>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BugFields],
      providers: [provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(BugFields);
    const form = createRequestForm(TestBed.inject(NonNullableFormBuilder));
    fixture.componentRef.setInput('group', form.controls.bug);
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(fixture.componentInstance).toBeTruthy();
  });
});
