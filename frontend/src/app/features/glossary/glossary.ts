import { Component } from '@angular/core';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [TranslatePipe],
  selector: 'app-glossary',
  styleUrl: './glossary.scss',
  templateUrl: './glossary.html',
})
export class Glossary {}
