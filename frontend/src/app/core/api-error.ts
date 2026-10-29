import { HttpErrorResponse } from '@angular/common/http';

export interface ApiError {
  code: string;
  fields?: Record<string, string[]>;
  retryAfter?: number;
}

export interface ErrorText {
  key: string;
  params: { seconds?: number };
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof HttpErrorResponse && isApiError(error.error)) {
    return error.error;
  }
  return { code: 'network_error' };
}

export function isUnreachable(error: unknown): boolean {
  return error instanceof HttpErrorResponse && !isApiError(error.error);
}

export function hasCode(error: unknown, code: string): boolean {
  return error instanceof HttpErrorResponse && isApiError(error.error) && error.error.code === code;
}

export function formErrorText(error: ApiError | undefined): ErrorText | undefined {
  if (!error || error.code === 'validation_error') {
    return undefined;
  }
  return { key: `apiErrors.${error.code}`, params: { seconds: error.retryAfter } };
}

export function fieldErrorKey(error: ApiError | undefined, field: string): string | undefined {
  const code = error?.fields?.[field]?.[0];
  return code ? `apiErrors.fields.${code}` : undefined;
}

function isApiError(body: unknown): body is ApiError {
  return (
    typeof body === 'object' && body !== null && 'code' in body && typeof body.code === 'string'
  );
}
