import { CodeLanguage } from '../models/entry';

export type TokenKind =
  | 'plain'
  | 'command'
  | 'keyword'
  | 'function'
  | 'string'
  | 'flag'
  | 'property'
  | 'number'
  | 'tag'
  | 'comment';

export interface CodeToken {
  text: string;
  kind: TokenKind;
}

export interface CodeLine {
  prompt: boolean;
  tokens: CodeToken[];
}

const COMMAND = /^(git|pip|python3?|django-admin|ng|npm|npx|ssh|sudo|scp|docker|cd|source)\b/;

const KEYWORDS = new Set([
  'from',
  'import',
  'class',
  'def',
  'return',
  'if',
  'else',
  'elif',
  'for',
  'in',
  'of',
  'True',
  'False',
  'None',
  'as',
  'with',
  'const',
  'let',
  'var',
  'function',
  'async',
  'await',
  'new',
  'throw',
  'export',
  'private',
  'true',
  'false',
  'null',
  'track',
  'interface',
  'type',
]);

const TERMINAL_TOKENS =
  /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(\s--?[A-Za-z][\w-]*)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_][\w.\\-]*)/g;

const CODE_TOKENS =
  /((?:^|\s)\/\/.*$)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)|(<\/?[A-Za-z][\w-]*|\/?>)|(\b\d+(?:\.\d+)?(?:px)?\b)|(@?[A-Za-z_$][\w$-]*)/g;

export function highlight(code: string, language: CodeLanguage): CodeLine[] {
  return code.split('\n').map((line) => highlightLine(line, language));
}

export function firstCodeLine(code: string): string {
  const lines = code.split('\n').map((line) => line.trim());
  const index = lines.findIndex((line) => line && !line.startsWith('#') && !line.startsWith('//'));
  if (index === -1) {
    return '';
  }
  const hasMore = lines.slice(index + 1).some(Boolean);
  return hasMore ? `${lines[index]} …` : lines[index];
}

function highlightLine(line: string, language: CodeLanguage): CodeLine {
  const trimmed = line.trim();
  if (!trimmed) {
    return { prompt: false, tokens: [] };
  }
  if (isComment(trimmed, language)) {
    return singleToken(line, 'comment');
  }
  if (language === 'terminal' || COMMAND.test(trimmed)) {
    return { prompt: true, tokens: terminalTokens(line) };
  }
  if (language === 'gitignore' || language === 'env') {
    return singleToken(line, 'plain');
  }
  return { prompt: false, tokens: lineTokens(line, language) };
}

function singleToken(text: string, kind: TokenKind): CodeLine {
  return { prompt: false, tokens: [{ text, kind }] };
}

function lineTokens(line: string, language: CodeLanguage): CodeToken[] {
  const commentStart = language === 'python' ? line.indexOf('  #') : -1;
  if (commentStart <= 0) {
    return codeTokens(line, language);
  }
  return [
    ...codeTokens(line.slice(0, commentStart), language),
    { text: line.slice(commentStart), kind: 'comment' },
  ];
}

function firstGroup(groups: readonly [string | undefined, TokenKind][]): TokenKind | undefined {
  return groups.find(([group]) => group)?.[1];
}

function isComment(trimmed: string, language: CodeLanguage): boolean {
  return trimmed.startsWith('//') || (trimmed.startsWith('#') && language !== 'css');
}

function terminalTokens(line: string): CodeToken[] {
  let commandFound = false;
  return tokenize(line, TERMINAL_TOKENS, ([, string, flag, number, word]) => {
    const kind = firstGroup([
      [string, 'string'],
      [flag, 'flag'],
      [number, 'number'],
    ]);
    if (kind || !word || commandFound) {
      return kind ?? 'plain';
    }
    commandFound = true;
    return 'command';
  });
}

function codeTokens(line: string, language: CodeLanguage): CodeToken[] {
  return tokenize(line, CODE_TOKENS, ([, comment, string, tag, number, word], rest) => {
    const kind = firstGroup([
      [comment, 'comment'],
      [string, 'string'],
      [tag, language === 'html' ? 'tag' : 'plain'],
      [number, 'number'],
    ]);
    return kind ?? wordKind(word, rest, language);
  });
}

function wordKind(word: string | undefined, rest: string, language: CodeLanguage): TokenKind {
  if (!word) {
    return 'plain';
  }
  if (word.startsWith('@') || KEYWORDS.has(word)) {
    return 'keyword';
  }
  if (language === 'css' && /^\s*:/.test(rest)) {
    return 'property';
  }
  return /^\s*\(/.test(rest) ? 'function' : 'plain';
}

function tokenize(
  line: string,
  pattern: RegExp,
  classify: (match: RegExpExecArray, rest: string) => TokenKind,
): CodeToken[] {
  const tokens: CodeToken[] = [];
  let last = 0;
  for (const match of line.matchAll(pattern)) {
    pushPlain(tokens, line.slice(last, match.index));
    const end = match.index + match[0].length;
    tokens.push({ text: match[0], kind: classify(match, line.slice(end)) });
    last = end;
  }
  pushPlain(tokens, line.slice(last));
  return tokens;
}

function pushPlain(tokens: CodeToken[], text: string): void {
  if (text) {
    tokens.push({ text, kind: 'plain' });
  }
}
