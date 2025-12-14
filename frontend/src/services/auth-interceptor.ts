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
import { AuthService } from './auth.service';


export const AuthInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn
): Observable<HttpEvent<unknown>> => {

  const authService = inject(AuthService);
  const router = inject(Router);

   return next(req).pipe(
    catchError((error: HttpErrorResponse) => {

      if (error.status === 401) {

        if (!req.url.endsWith('/auth/login')) {

          console.error('Interceptor: Token abgelaufen oder ungültig. Logout wird durchgeführt.');

          authService.logout();

          router.navigate(['/login']);
        }
      }

      return throwError(() => error);
    })
  );
};
