import { Component } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe],
  selector: 'app-guides',
  styleUrl: './guides.scss',
  templateUrl: './guides.html',
})
export class Guides {}
