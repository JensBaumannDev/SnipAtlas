import { Service } from '@angular/core';
import { storedJson } from '../browser/browser-storage';

const NOTICE_KEY = 'snipatlas-ai-notice';

@Service()
export class AiCodingNotice {
  readonly confirmed = storedJson<boolean>(NOTICE_KEY, (value) => value === true);

  confirm(): void {
    this.confirmed.set(true);
  }
}
