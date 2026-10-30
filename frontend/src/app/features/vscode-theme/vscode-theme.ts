import { Component } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe],
  selector: 'app-vscode-theme',
  styleUrl: './vscode-theme.scss',
  templateUrl: './vscode-theme.html',
})
export class VscodeTheme {}
