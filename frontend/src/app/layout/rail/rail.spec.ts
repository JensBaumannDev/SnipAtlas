import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideTranslateService } from '@ngx-translate/core';
import { Rail } from './rail';

describe('Rail', () => {
  let component: Rail;
  let fixture: ComponentFixture<Rail>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Rail],
      providers: [provideRouter([]), provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(Rail);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
