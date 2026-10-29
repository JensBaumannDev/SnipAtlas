import { ContentArea } from '../content/content-index';

export interface SearchResult {
  area: ContentArea;
  title: string;
  text: string;
  link: string[];
  fragment?: string;
}
