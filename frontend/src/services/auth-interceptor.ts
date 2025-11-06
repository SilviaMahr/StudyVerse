import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandlerFn,
  HttpInterceptorFn,
  HttpRequest
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from './auth.service'; // Pfad ggf. anpassen

/**
 * Dies ist jetzt ein FUNKTIONALER Interceptor,
 * der mit 'withInterceptors' kompatibel ist.
 */
export const AuthInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn
): Observable<HttpEvent<unknown>> => {

  // Services (die früher im Konstruktor waren) werden jetzt mit inject() geholt
  const authService = inject(AuthService);
  const router = inject(Router);

  // Die Anfrage durchlassen und auf die Antwort warten
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {

      // 1. Prüfen, ob es ein 401-Fehler ist
      if (error.status === 401) {

        // 2. Prüfen, ob es NICHT die Login-Anfrage selbst war
        if (!req.url.endsWith('/auth/login')) {

          console.error('Interceptor: Token abgelaufen oder ungültig. Logout wird durchgeführt.');

          // 3. Benutzer global ausloggen
          authService.logout();

          // 4. Zur Login-Seite umleiten
          router.navigate(['/login']);
        }
      }

      // 5. Wichtig: Den Fehler weiterwerfen
      return throwError(() => error);
    })
  );
};
