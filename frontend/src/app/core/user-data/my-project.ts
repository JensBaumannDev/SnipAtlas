import { HttpClient } from '@angular/common/http';
import { Service, computed, effect, inject, signal } from '@angular/core';
import { Observable, map, tap } from 'rxjs';
import { UserProject } from '../models/roadmap';
import { Session } from '../auth/session';

const URL = '/api/me/project/';

@Service()
export class MyProject {
  private readonly http = inject(HttpClient);
  private readonly session = inject(Session);

  readonly project = signal<UserProject | null | undefined>(undefined);
  readonly ready = computed(() => !!this.session.user() && this.project() !== undefined);
  readonly blocks = computed(() => this.project()?.blocks ?? []);

  constructor() {
    effect((onCleanup) => {
      const event = this.session.authEvent();
      this.project.set(undefined);
      if (event === 'login' || event === 'restore') {
        const request = this.http.get<UserProject>(URL).subscribe({
          next: (project) => this.project.set(project),
          error: () => this.project.set(null),
        });
        onCleanup(() => request.unsubscribe());
      }
    });
  }

  isDone(phase: string, step: string): boolean {
    return this.project()?.completed[phase]?.includes(step) ?? false;
  }

  note(phase: string, step: string): string {
    return this.project()?.notes[phase]?.[step] ?? '';
  }

  choose(blocks: string[]): Observable<void> {
    return this.http.put<UserProject>(URL, { blocks }).pipe(
      tap((project) => this.project.set(project)),
      map(() => undefined),
    );
  }

  remove(): Observable<void> {
    return this.http.delete<void>(URL).pipe(tap(() => this.project.set(null)));
  }

  toggle(phase: string, step: string): void {
    const done = this.isDone(phase, step);
    this.updateCompleted(phase, step, !done);
    const url = `${URL}steps/${phase}/${step}/`;
    const request = done ? this.http.delete<void>(url) : this.http.put<void>(url, null);
    request.subscribe({ error: () => this.updateCompleted(phase, step, done) });
  }

  saveNote(phase: string, step: string, text: string): Observable<void> {
    const url = `${URL}notes/${phase}/${step}/`;
    const clean = text.trim();
    const request = clean ? this.http.put<void>(url, { text: clean }) : this.http.delete<void>(url);
    return request.pipe(tap(() => this.updateNote(phase, step, clean)));
  }

  private updateCompleted(phase: string, step: string, done: boolean): void {
    this.project.update((project) => {
      if (!project) {
        return project;
      }
      const steps = (project.completed[phase] ?? []).filter((slug) => slug !== step);
      const completed = { ...project.completed, [phase]: done ? [...steps, step] : steps };
      return { ...project, completed };
    });
  }

  private updateNote(phase: string, step: string, text: string): void {
    this.project.update((project) => {
      if (!project) {
        return project;
      }
      const notes = { ...(project.notes[phase] ?? {}) };
      if (text) {
        notes[step] = text;
      } else {
        delete notes[step];
      }
      return { ...project, notes: { ...project.notes, [phase]: notes } };
    });
  }
}
