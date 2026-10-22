import { Component } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe],
  selector: 'app-request',
  styleUrl: './request.scss',
  templateUrl: './request.html',
})
export class Request {}
