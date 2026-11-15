import { Location, NgTemplateOutlet } from '@angular/common';
import { Component, afterNextRender, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslatePipe } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { EmailConfirmation } from '../../../core/auth/email-confirmation';
import { MailLink, readMailLink } from '../../../core/auth/link';
import { LoginDialog } from '../../../core/auth/login-dialog';
import { Session } from '../../../core/auth/session';
import { ApiError, formErrorText, toApiError } from '../../../core/http/api-error';

export type MailLinkKind = 'activation' | 'email';

type ConfirmStatus = 'pending' | 'done' | 'invalid' | 'failed';

const NEXT_LINKS: Record<MailLinkKind, string> = { activation: '/', email: '/profil' };

@Component({
  imports: [NgTemplateOutlet, RouterLink, TranslatePipe],
  selector: 'app-confirm-link',
  styleUrl: './confirm-link.scss',
  templateUrl: './confirm-link.html',
})
export class ConfirmLink {
  private readonly route = inject(ActivatedRoute);
  private readonly session = inject(Session);
  private readonly emailConfirmation = inject(EmailConfirmation);
  private readonly loginDialog = inject(LoginDialog);
  private readonly link = readMailLink(this.route, inject(Location));

  protected readonly kind: MailLinkKind = this.route.snapshot.data['link'];
  protected readonly texts = `confirmLink.${this.kind}`;
  protected readonly nextLink = NEXT_LINKS[this.kind];
  protected readonly status = signal<ConfirmStatus>(this.link ? 'pending' : 'invalid');
  protected readonly signedIn = computed(() => !!this.session.user());
  protected readonly error = signal<ApiError | undefined>(undefined);
  protected readonly errorText = computed(() => formErrorText(this.error()));

  constructor() {
    afterNextRender(() => this.confirm());
  }

  protected login(): void {
    this.loginDialog.open();
  }

  private confirm(): void {
    if (!this.link) {
      return;
    }
    this.request(this.link).subscribe({
      next: () => this.status.set('done'),
      error: (error: unknown) => this.fail(toApiError(error)),
    });
  }

  private request(link: MailLink): Observable<void> {
    return this.kind === 'activation'
      ? this.session.activate(link)
      : this.emailConfirmation.confirmEmail(link);
  }

  private fail(error: ApiError): void {
    this.status.set(error.code === 'invalid_link' ? 'invalid' : 'failed');
    this.error.set(error);
  }
}
