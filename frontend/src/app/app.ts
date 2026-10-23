import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { Footer } from './layout/footer/footer';
import { Outline } from './layout/outline/outline';
import { Rail } from './layout/rail/rail';
import { Sidebar } from './layout/sidebar/sidebar';
import { Topbar } from './layout/topbar/topbar';

@Component({
  imports: [RouterOutlet, Rail, Topbar, Sidebar, Outline, Footer, TranslatePipe],
  selector: 'app-root',
  styleUrl: './app.scss',
  templateUrl: './app.html',
})
export class App {}
