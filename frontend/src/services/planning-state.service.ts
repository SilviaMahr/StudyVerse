import {Injectable} from '@angular/core';
import {BehaviorSubject, Observable} from 'rxjs';
import {PlanningResponse} from '../app/models/preselection.model';
import {PlanningService} from './planning.service';

@Injectable({
  providedIn: 'root'
})

export class PlanningStateService {
  private readonly _planning = new BehaviorSubject<PlanningResponse | null>(null);
  public readonly planning$ = this._planning.asObservable();

  private readonly _isChatVisible = new BehaviorSubject<boolean>(false);
  public readonly isChatVisible$ = this._isChatVisible.asObservable();

  constructor(private planningService: PlanningService) { }

  loadPlan(id: number): Observable<PlanningResponse> {
    const plan$ = this.planningService.getPlanningDetails(id);

    plan$.subscribe({
      next: (data) => {
        this._planning.next(data);
      },
      error: (err) => {
        console.error("Fehler beim Laden des Plans im StateService", err);
        this._planning.next(null);
      }
    });

    return plan$;
  }

  openChat(): void {
    this._isChatVisible.next(true);
  }

  closeChat(): void {
    this._isChatVisible.next(false);
  }

  updatePlan(newPlanData: PlanningResponse): void {
    this._planning.next(newPlanData);
  }

  clearState(): void {
    this._planning.next(null);
    this._isChatVisible.next(false);
  }
}
