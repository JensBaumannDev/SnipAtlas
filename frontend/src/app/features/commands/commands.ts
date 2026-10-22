import { Component } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe],
  selector: 'app-commands',
  styleUrl: './commands.scss',
  templateUrl: './commands.html',
})
export class Commands {}
