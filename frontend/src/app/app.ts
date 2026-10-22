import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Rail } from './layout/rail/rail';
import { Sidebar } from './layout/sidebar/sidebar';
import { Topbar } from './layout/topbar/topbar';

@Component({
  imports: [RouterOutlet, Rail, Topbar, Sidebar],
  selector: 'app-root',
  styleUrl: './app.scss',
  templateUrl: './app.html',
})
export class App {}
