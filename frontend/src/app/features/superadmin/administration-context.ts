import {InjectionToken} from '@angular/core';

export const ADMINISTRATION_CONTEXT = new InjectionToken('AdministrationContext', {
  providedIn:'root',
  factory:()=>({apiSegment:'superadmin',panel:'/dashboard/superadmin',global:true}),
});
