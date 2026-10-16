import { HttpErrorResponse } from '@angular/common/http';
import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import {
  catchError,
  combineLatest,
  EMPTY,
  finalize,
  Observable,
  startWith,
  Subject,
  switchMap,
} from 'rxjs';
import { RESULTADOS_CONFIG, RESULTADOS_SOURCE, ResultadoResumen } from './resultados.models';

@Injectable()
export class ResultadosViewModel {
  readonly config = inject(RESULTADOS_CONFIG);
  private readonly api = inject(RESULTADOS_SOURCE);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);
  private readonly retry = new Subject<void>();
  readonly loading = signal(false);
  readonly error = signal('');
  readonly esDetalle = signal(false);
  readonly resultados = signal<ResultadoResumen[]>([]);
  readonly resultado = signal<ResultadoResumen | null>(null);

  constructor() {
    combineLatest([this.route.paramMap, this.retry.pipe(startWith(undefined))])
      .pipe(
        switchMap(([params]) => {
          const id = params.get('resultadoId');
          this.esDetalle.set(!!id);
          this.resultados.set([]);
          this.resultado.set(null);
          this.error.set('');
          this.loading.set(true);
          const request: Observable<ResultadoResumen | ResultadoResumen[]> = id
            ? this.api.detalle(id)
            : this.api.listar(params.get('trabajadorId') ?? undefined);
          return request.pipe(
            catchError((error: HttpErrorResponse) => {
              this.error.set(
                error.status === 403 || error.status === 404
                  ? 'No tienes acceso a estos resultados o ya no están disponibles.'
                  : error.status === 401
                    ? 'Tu sesión ya no es válida. Vuelve a iniciar sesión.'
                    : 'No pudimos cargar los resultados. Intenta nuevamente.',
              );
              return EMPTY;
            }),
            finalize(() => this.loading.set(false)),
          );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((data) => {
        if (Array.isArray(data)) this.resultados.set(data);
        else this.resultado.set(data);
      });
  }

  load(): void {
    if (!this.loading()) this.retry.next();
  }
}
