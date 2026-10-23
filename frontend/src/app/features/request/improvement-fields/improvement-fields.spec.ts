import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NonNullableFormBuilder } from '@angular/forms';
import { provideTranslateService } from '@ngx-translate/core';
import { createRequestForm } from '../request-form';
import { ImprovementFields } from './improvement-fields';

describe('ImprovementFields', () => {
  let fixture: ComponentFixture<ImprovementFields>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImprovementFields],
      providers: [provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(ImprovementFields);
    const form = createRequestForm(TestBed.inject(NonNullableFormBuilder));
    fixture.componentRef.setInput('group', form.controls.improvement);
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(fixture.componentInstance).toBeTruthy();
  });
});
