import { HttpClient } from '@angular/common/http';
import { Service, effect, inject, signal, untracked } from '@angular/core';
import { Entry } from './entry';
import { AuthEvent, Session } from './session';

export interface Favorite {
  topic: string;
  subtopic: string;
  slug: string;
  title: string;
}

const URL = '/api/me/favorites/';

@Service()
export class Favorites {
  private readonly http = inject(HttpClient);
  private readonly session = inject(Session);
  private readonly favorites = signal<readonly Favorite[]>([]);

  readonly list = this.favorites.asReadonly();

  constructor() {
    effect(() => {
      const event = this.session.authEvent();
      untracked(() => this.sync(event));
    });
  }

  has(entry: Entry): boolean {
    return this.list().some((favorite) => isSame(favorite, entry));
  }

  toggle(entry: Entry): void {
    const previous = this.favorites();
    const active = this.has(entry);
    const url = `${URL}${entry.slug}/`;
    this.favorites.set(
      active
        ? previous.filter((favorite) => !isSame(favorite, entry))
        : [...previous, toFavorite(entry)],
    );
    const request = active ? this.http.delete<void>(url) : this.http.put<void>(url, null);
    request.subscribe({ error: () => this.favorites.set(previous) });
  }

  private sync(event: AuthEvent | undefined): void {
    this.favorites.set([]);
    if (event === 'login' || event === 'restore') {
      this.http.get<Favorite[]>(URL).subscribe({
        next: (favorites) => this.favorites.set(favorites),
        error: () => undefined,
      });
    }
  }
}

function toFavorite(entry: Entry): Favorite {
  return { topic: entry.topic, subtopic: entry.subtopic, slug: entry.slug, title: entry.title };
}

function isSame(favorite: Favorite, entry: Entry): boolean {
  return favorite.topic === entry.topic && favorite.slug === entry.slug;
}
