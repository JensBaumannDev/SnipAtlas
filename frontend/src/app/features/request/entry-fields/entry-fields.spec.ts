import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NonNullableFormBuilder } from '@angular/forms';
import { provideTranslateService } from '@ngx-translate/core';
import { createRequestForm } from '../request-form';
import { EntryFields } from './entry-fields';

describe('EntryFields', () => {
  let fixture: ComponentFixture<EntryFields>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EntryFields],
      providers: [provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(EntryFields);
    const form = createRequestForm(TestBed.inject(NonNullableFormBuilder));
    fixture.componentRef.setInput('group', form.controls.entry);
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(fixture.componentInstance).toBeTruthy();
  });
});
