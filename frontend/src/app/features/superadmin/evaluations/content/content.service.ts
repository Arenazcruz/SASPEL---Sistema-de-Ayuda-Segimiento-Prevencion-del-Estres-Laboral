import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { EMPTY, expand, reduce } from 'rxjs';
import { API_URL } from '../../../../core/auth/api-url';
import { Instrument } from '../instruments/instruments.models';
import { ContentPage, ContentRow, ContentScope, ContentValue } from './content.models';

@Injectable({ providedIn: 'root' })
export class InstrumentContentService {
  private readonly http = inject(HttpClient);
  private readonly base = `${inject(API_URL)}/superadmin`;
  private path(scope: ContentScope) {
    if (scope.kind === 'scales') return `${this.base}/scales/`;
    const parent = scope.kind === 'options' ? 'scales' : 'instruments';
    return `${this.base}/${parent}/${scope.parentId}/${scope.kind}/`;
  }
  list(scope: ContentScope, filters: Record<string, string | number>) {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters))
      if (value !== '') params = params.set(key, value);
    return this.http.get<ContentPage>(this.path(scope), { params });
  }
  get(scope: ContentScope, id: string) {
    return this.http.get<ContentRow>(`${this.path(scope)}${id}/`);
  }
  create(scope: ContentScope, data: Record<string, ContentValue>) {
    return this.http.post<ContentRow>(this.path(scope), data);
  }
  update(scope: ContentScope, id: string, data: Record<string, ContentValue>) {
    return this.http.patch<ContentRow>(`${this.path(scope)}${id}/`, data);
  }
  active(scope: ContentScope, id: string, active: boolean) {
    return this.http.post<ContentRow>(
      `${this.path(scope)}${id}/${active ? 'activate' : 'deactivate'}/`,
      {},
    );
  }
  move(scope: ContentScope, id: string, direction: 'up' | 'down') {
    return this.http.post<ContentRow>(`${this.path(scope)}${id}/move/`, { direction });
  }
  private all<T>(path: string) {
    const page = (index: number) =>
      this.http.get<ContentPage<T>>(`${this.base}/${path}/`, { params: { page: index } });
    return page(1).pipe(
      expand((result) =>
        result.page * result.page_size < result.count ? page(result.page + 1) : EMPTY,
      ),
      reduce((items, result) => [...items, ...result.results], [] as T[]),
    );
  }
  instruments() {
    return this.all<Instrument>('instruments');
  }
  scales() {
    return this.all<ContentRow>('scales');
  }
}
