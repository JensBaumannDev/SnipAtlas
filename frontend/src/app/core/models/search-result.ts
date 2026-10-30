import { ContentArea } from '../content/content-index';

export type SearchArea = ContentArea | 'glossary';

export interface SearchResult {
  area: SearchArea;
  title: string;
  text: string;
  link: string[];
  fragment?: string;
  query?: string;
  glossaryMatchCount?: number;
}
