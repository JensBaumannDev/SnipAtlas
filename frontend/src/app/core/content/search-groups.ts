import { LucideIconData } from '@lucide/angular';
import { SearchArea, SearchResult } from '../models/search-result';
import { bookAIcon, bookTextIcon, routeIcon, terminalIcon, triangleAlertIcon } from '../ui/icons';

export interface SearchItem {
  result: SearchResult;
  index: number;
}

export interface SearchGroup {
  area: SearchArea;
  icon: LucideIconData;
  items: SearchItem[];
}

const AREA_ICONS: Readonly<Record<SearchArea, LucideIconData>> = {
  glossary: bookAIcon,
  commands: terminalIcon,
  concepts: bookTextIcon,
  blueprints: routeIcon,
  debugging: triangleAlertIcon,
};

const AREA_ORDER = Object.keys(AREA_ICONS) as SearchArea[];

export function groupByArea(results: readonly SearchResult[]): SearchGroup[] {
  const sorted = AREA_ORDER.flatMap((area) => results.filter((result) => result.area === area));
  const items = sorted.map((result, index) => ({ result, index }));
  return AREA_ORDER.map((area) => ({
    area,
    icon: AREA_ICONS[area],
    items: items.filter((item) => item.result.area === area),
  })).filter((group) => group.items.length > 0);
}
