import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Rail } from './rail';

describe('Rail', () => {
  let component: Rail;
  let fixture: ComponentFixture<Rail>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Rail],
    }).compileComponents();

    fixture = TestBed.createComponent(Rail);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
