import {Routes} from '@angular/router';
import {ADMINISTRATION_CONTEXT} from '../superadmin/administration-context';
import {SUPERADMIN_ROUTES} from '../superadmin/superadmin.routes';
import {SuperadminService} from '../superadmin/superadmin.service';
import {InstrumentsService} from '../superadmin/evaluations/instruments/instruments.service';
import {InstrumentContentService} from '../superadmin/evaluations/content/content.service';
import {AssignmentsService} from '../superadmin/assignments/assignments.service';

export const ADMIN_PROVIDERS = [
 {provide:ADMINISTRATION_CONTEXT,useValue:{apiSegment:'institucional',panel:'/dashboard/admin',global:false}},
 SuperadminService,InstrumentsService,InstrumentContentService,AssignmentsService,
];
export const ADMIN_ROUTES: Routes = SUPERADMIN_ROUTES.filter(r=>r.path!=='personas/administradores');
