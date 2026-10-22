import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideTranslateService } from '@ngx-translate/core';
import { Errors } from './errors';

describe('Errors', () => {
  let component: Errors;
  let fixture: ComponentFixture<Errors>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Errors],
      providers: [provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(Errors);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
