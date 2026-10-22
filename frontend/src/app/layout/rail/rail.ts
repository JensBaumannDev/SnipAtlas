import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [RouterLink, RouterLinkActive, TranslatePipe],
  selector: 'app-rail',
  styleUrl: './rail.scss',
  templateUrl: './rail.html',
})
export class Rail {}
