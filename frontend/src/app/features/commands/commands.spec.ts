import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideTranslateService } from '@ngx-translate/core';
import { Commands } from './commands';

describe('Commands', () => {
  let component: Commands;
  let fixture: ComponentFixture<Commands>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Commands],
      providers: [provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(Commands);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
