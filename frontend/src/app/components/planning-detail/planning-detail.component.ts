import {ChangeDetectorRef, Component, OnDestroy, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {PlanningResponse} from '../../models/preselection.model';
import {ActivatedRoute} from '@angular/router';
import {PlanningService} from '../../../services/planning.service';
import { Subscription} from 'rxjs';
import { switchMap } from 'rxjs/operators';

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
  isLoading: boolean = true;
  error: string | null = null;

  private routeSubscription: Subscription | undefined;

  constructor(
    private route: ActivatedRoute,
    private planningService: PlanningService,
    private cdr: ChangeDetectorRef
  ) {
  }

  ngOnInit() {
    this.routeSubscription = this.route.paramMap.pipe(
      switchMap(params => {
        this.isLoading = true;
        this.planning = null;
        this.error = null;

        const idParam = params.get('id');

        if (!idParam) {
          this.error = "Keine Planungs-ID in der URL gefunden.";
          this.isLoading = false;
          throw new Error('NoID');
        }

        const planningId = Number(idParam);
        return this.planningService.getPlanningDetails(planningId);
      })
    ).subscribe({
      next: (data) => {
        this.planning = data;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        if (err.message !== 'NoID') {
          console.error("Fehler beim Laden der Planungsdetails:", err);
          this.error = "Planung konnte nicht geladen werden.";
        }
        this.isLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  ngOnDestroy() {
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
  }

  startRagAnalysis(): void {
    if (!this.planning) return;

    console.log(`Start RAG für Planung ${this.planning.id}...`);
  }
}
