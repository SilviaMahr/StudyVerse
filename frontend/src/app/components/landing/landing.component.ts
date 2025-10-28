import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {SidebarComponent} from '../sidebar/sidebar.component';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, SidebarComponent],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.css']
})
export class LandingComponent implements OnInit {

  constructor() { }

  ngOnInit(): void {
  }

}
