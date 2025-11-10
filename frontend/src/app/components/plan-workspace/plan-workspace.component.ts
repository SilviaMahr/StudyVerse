import {ChangeDetectorRef, Component, OnDestroy, OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {PlanningDetailComponent} from '../planning-detail/planning-detail.component';
import {ChatComponent} from '../chat/chat.component';
import {Observable, Subscription} from 'rxjs';
import {ActivatedRoute} from '@angular/router';
import {PlanningStateService} from '../../../services/planning-state.service';

@Component({
  selector: 'app-plan-workspace',
  standalone: true,
  imports: [CommonModule, PlanningDetailComponent, ChatComponent],
  templateUrl: './plan-workspace.component.html',
  styleUrls: ['./plan-workspace.component.css']
})
export class PlanWorkspaceComponent implements OnInit, OnDestroy {
  public isChatVisible$: Observable<boolean>;
  public planning$: Observable<any>;

  isLoading: boolean = true;
  error: string | null = null;

  private routeSubscription: Subscription | undefined;

  constructor(
    private route: ActivatedRoute,
    public planningState: PlanningStateService,
    private cdr: ChangeDetectorRef
  ) {
    this.isChatVisible$ = this.planningState.isChatVisible$;
    this.planning$ = this.planningState.planning$;
  }

  ngOnInit() {
    this.routeSubscription = this.route.paramMap.subscribe(params => {
      this.isLoading = true;
      this.planningState.clearState();
      this.error = null;

      const idParam = params.get('id');

      if (idParam) {
        const planningId = Number(idParam);

        this.planningState.loadPlan(planningId).subscribe({
          next: () =>{
            this.isLoading = false;
            this.cdr.detectChanges();
          },
          error: (err) => {
            this.error = "Plan konnte nicht geladen werden.";
            this.isLoading = false;
          }
        });
      } else {
        this.isLoading = false;
        this.error = "Keine Planungs-ID gefunden."
      }
    });
  }

  ngOnDestroy() {
    if (this.routeSubscription) {
      this.routeSubscription.unsubscribe();
    }
    this.planningState.clearState();
  }
}
