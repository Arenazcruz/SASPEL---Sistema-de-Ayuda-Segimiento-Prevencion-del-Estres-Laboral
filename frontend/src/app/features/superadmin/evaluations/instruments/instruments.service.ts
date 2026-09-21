import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { API_URL } from '../../../../core/auth/api-url';
import { Instrument, InstrumentData, InstrumentPage } from './instruments.models';

@Injectable({ providedIn: 'root' })
export class InstrumentsService {
  private readonly http = inject(HttpClient);
  private readonly base = `${inject(API_URL)}/superadmin/instruments/`;

  list(filters: Record<string, string | number>) {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== '') params = params.set(key, value);
    }
    return this.http.get<InstrumentPage>(this.base, { params });
  }
  get(id: number) {
    return this.http.get<Instrument>(`${this.base}${id}/`);
  }
  create(data: InstrumentData) {
    return this.http.post<Instrument>(this.base, data);
  }
  update(id: number, data: InstrumentData) {
    return this.http.patch<Instrument>(`${this.base}${id}/`, data);
  }
  active(id: number, active: boolean) {
    return this.http.post<Instrument>(
      `${this.base}${id}/${active ? 'activate' : 'deactivate'}/`,
      {},
    );
  }
}
