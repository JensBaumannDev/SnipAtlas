import { Component } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe],
  selector: 'app-errors',
  styleUrl: './errors.scss',
  templateUrl: './errors.html',
})
export class Errors {}
