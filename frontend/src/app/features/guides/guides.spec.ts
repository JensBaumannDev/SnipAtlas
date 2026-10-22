import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideTranslateService } from '@ngx-translate/core';
import { Guides } from './guides';

describe('Guides', () => {
  let component: Guides;
  let fixture: ComponentFixture<Guides>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Guides],
      providers: [provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(Guides);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
