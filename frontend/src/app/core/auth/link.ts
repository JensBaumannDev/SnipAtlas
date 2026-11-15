import { Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';

export interface MailLink {
  uid: string;
  token: string;
}

export function readMailLink(route: ActivatedRoute, location: Location): MailLink | undefined {
  const params = route.snapshot.queryParamMap;
  const uid = params.get('uid');
  const token = params.get('token');
  location.replaceState(location.path().split('?')[0]);
  return uid && token ? { uid, token } : undefined;
}
