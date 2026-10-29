import { Service, signal } from '@angular/core';

@Service()
export class ServerStatus {
  readonly unreachable = signal(false);
}
