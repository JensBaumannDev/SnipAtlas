import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideTranslateService } from '@ngx-translate/core';
import { SettingsMenu } from './settings-menu';

describe('SettingsMenu', () => {
  let component: SettingsMenu;
  let fixture: ComponentFixture<SettingsMenu>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SettingsMenu],
      providers: [provideTranslateService()],
    }).compileComponents();

    fixture = TestBed.createComponent(SettingsMenu);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
