import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { AreaLinks } from '../../shared/area-links/area-links';

@Component({
  imports: [AreaLinks, RouterLink, TranslatePipe],
  selector: 'app-not-found',
  styleUrl: './not-found.scss',
  templateUrl: './not-found.html',
})
export class NotFound {}
