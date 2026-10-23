import { Component } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe],
  selector: 'app-imprint',
  styleUrl: './imprint.scss',
  templateUrl: './imprint.html',
})
export class Imprint {}
