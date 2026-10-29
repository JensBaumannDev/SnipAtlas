import { RequestKind } from './contact-request';

export type UserRequestStatus = 'open' | 'done';

export interface UserRequest {
  id: number;
  kind: RequestKind;
  subject: string;
  date: string;
  status: UserRequestStatus;
  answer?: string;
}
