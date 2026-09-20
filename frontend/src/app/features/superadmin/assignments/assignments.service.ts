/** HTTP de T23. JWT y renovación se delegan al interceptor existente de autenticación. */
import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { API_URL } from '../../../core/auth/api-url';
import {
  AssignmentPage,
  AssignmentPerson,
  ProfessionalAssignment,
  PsychologistLoad,
} from './assignments.models';

@Injectable({ providedIn: 'root' })
export class AssignmentsService {
  private readonly http = inject(HttpClient);
  private readonly base = `${inject(API_URL)}/superadmin/assignments`;

  list(filters: Record<string, string | number>) {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== '') params = params.set(key, value);
    }
    return this.http.get<AssignmentPage<ProfessionalAssignment>>(`${this.base}/`, { params });
  }

  unassigned(search = '', page = 1) {
    return this.http.get<AssignmentPage<AssignmentPerson>>(`${this.base}/unassigned-workers/`, {
      params: { search, page },
    });
  }

  psychologists() {
    return this.http.get<PsychologistLoad[]>(`${this.base}/psychologists/`);
  }

  assign(trabajador_id: number, psicologo_id: number) {
    return this.http.post<ProfessionalAssignment>(`${this.base}/`, { trabajador_id, psicologo_id });
  }

  reassign(id: number, psicologo_id: number, motivo_fin: string) {
    return this.http.post<ProfessionalAssignment>(`${this.base}/${id}/reassign/`, {
      psicologo_id,
      motivo_fin,
    });
  }

  finish(id: number, motivo_fin: string) {
    return this.http.post<ProfessionalAssignment>(`${this.base}/${id}/finish/`, { motivo_fin });
  }
}
