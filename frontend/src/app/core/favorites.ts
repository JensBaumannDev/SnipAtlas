import { Service, computed, inject } from '@angular/core';
import { Entry } from './entry';
import { Favorite, Session } from './session';

@Service()
export class Favorites {
  private readonly session = inject(Session);

  readonly list = computed(() => this.session.user()?.favorites ?? []);

  has(entry: Entry): boolean {
    return this.list().some((favorite) => isSame(favorite, entry));
  }

  toggle(entry: Entry): void {
    const favorites = this.list();
    const next = this.has(entry)
      ? favorites.filter((favorite) => !isSame(favorite, entry))
      : [
          ...favorites,
          { topic: entry.topic, subtopic: entry.subtopic, slug: entry.slug, title: entry.title },
        ];
    this.session.update({ favorites: next });
  }
}

function isSame(favorite: Favorite, entry: Entry): boolean {
  return favorite.topic === entry.topic && favorite.slug === entry.slug;
}
