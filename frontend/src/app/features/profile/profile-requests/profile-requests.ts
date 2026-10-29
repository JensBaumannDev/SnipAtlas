import { DatePipe } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { Preferences } from '../../../core/user-data/preferences';
import { UserRequestApi } from '../../../core/api/user-request-api';

@Component({
  imports: [DatePipe, RouterLink, TranslatePipe],
  selector: 'app-profile-requests',
  styleUrl: './profile-requests.scss',
  templateUrl: './profile-requests.html',
})
export class ProfileRequests {
  protected readonly language = inject(Preferences).language;
  protected readonly requests = toSignal(inject(UserRequestApi).getMine(), { initialValue: [] });

  protected readonly openCount = computed(
    () => this.requests().filter((request) => request.status === 'open').length,
  );
  protected readonly doneCount = computed(() => this.requests().length - this.openCount());
}
