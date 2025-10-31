import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {SidebarComponent} from '../../components/sidebar/sidebar.component';
import {PreselectionComponent, PreselectionData} from '../../components/preselection/preselection.component';

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

  onStartPlanning (data: PreselectionData): void {
    console.log('Daten von Preselection-Komponente empfangen', data);
  }

  constructor() { }

  ngOnInit(): void {
  }

}
