import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';

@Component({
  imports: [RouterLink, RouterLinkActive, TranslatePipe],
  selector: 'app-project-navigation',
  styleUrl: './project-navigation.scss',
  templateUrl: './project-navigation.html',
})
export class ProjectNavigation {}
