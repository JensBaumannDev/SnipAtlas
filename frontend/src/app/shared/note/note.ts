import { Component, input } from '@angular/core';

@Component({
  selector: 'app-note',
  styleUrl: './note.scss',
  templateUrl: './note.html',
})
export class Note {
  readonly label = input.required<string>();
  readonly text = input.required<string>();
}
