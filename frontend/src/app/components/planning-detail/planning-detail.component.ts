import {ChangeDetectorRef, Component, OnDestroy, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {PlanningResponse} from '../../models/preselection.model';
import {ActivatedRoute} from '@angular/router';
import {PlanningService} from '../../../services/planning.service';
import { Subscription} from 'rxjs';
import { switchMap } from 'rxjs/operators';
import {PlanningStateService} from '../../../services/planning-state.service';

@Component ({
  selector: 'app-planning-detail',
  standalone: true,
  imports: [
    CommonModule
  ],
  templateUrl: './planning-detail.component.html',
  styleUrls: ['./planning-detail.component.css']
})

export class PlanningDetailComponent implements OnInit, OnDestroy {
  planning: PlanningResponse | null = null;

  private planningSubscription: Subscription | undefined;

  constructor(
    private planningState: PlanningStateService
  ) {
  }

  ngOnInit() {
    this.planningSubscription = this.planningState.planning$.subscribe(plan => {
      this.planning = plan;
    })
  }

  ngOnDestroy() {
    if (this.planningSubscription) {
      this.planningSubscription.unsubscribe();
    }
  }

  startRagAnalysis(): void {
    if (!this.planning) return;

    console.log(`Start RAG für Planung ${this.planning.id}...`);
    this.planningState.openChat();
  }
}
