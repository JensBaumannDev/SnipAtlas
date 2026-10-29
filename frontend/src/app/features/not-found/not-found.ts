import { Component, RESPONSE_INIT, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { AreaLinks } from '../../shared/area-links/area-links';

@Component({
  imports: [AreaLinks, RouterLink, TranslatePipe],
  selector: 'app-not-found',
  styleUrl: './not-found.scss',
  templateUrl: './not-found.html',
})
export class NotFound {
  constructor() {
    const response = inject(RESPONSE_INIT, { optional: true });
    if (response) {
      response.status = 404;
    }
  }
}
