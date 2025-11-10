import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {SidebarComponent} from '../../components/sidebar/sidebar.component';
import {PreselectionComponent} from '../../components/preselection/preselection.component';
import { PreselectionData} from '../../models/preselection.model';
import {ChatComponent} from '../../components/chat/chat.component';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [
    CommonModule,
    SidebarComponent,
    PreselectionComponent
  ],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.css']
})
export class LandingComponent implements OnInit {
  constructor() {
  }

  ngOnInit() {
  }
}
