import { CodeLanguage } from './entry';

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
    return { prompt: false, tokens: [{ text: line, kind: 'comment' }] };
  }
  if (language === 'terminal' || COMMAND.test(trimmed)) {
    return { prompt: true, tokens: terminalTokens(line) };
  }
  if (language === 'gitignore') {
    return { prompt: false, tokens: [{ text: line, kind: 'plain' }] };
  }

  const commentStart = language === 'python' ? line.indexOf('  #') : -1;
  if (commentStart > 0) {
    return {
      prompt: false,
      tokens: [
        ...codeTokens(line.slice(0, commentStart), language),
        { text: line.slice(commentStart), kind: 'comment' },
      ],
    };
  }
  return { prompt: false, tokens: codeTokens(line, language) };
}

function isComment(trimmed: string, language: CodeLanguage): boolean {
  return trimmed.startsWith('//') || (trimmed.startsWith('#') && language !== 'css');
}

function terminalTokens(line: string): CodeToken[] {
  let commandFound = false;
  return tokenize(line, TERMINAL_TOKENS, ([, string, flag, number, word]) => {
    if (string) {
      return 'string';
    }
    if (flag) {
      return 'flag';
    }
    if (number) {
      return 'number';
    }
    if (word && !commandFound) {
      commandFound = true;
      return 'command';
    }
    return 'plain';
  });
}

function codeTokens(line: string, language: CodeLanguage): CodeToken[] {
  return tokenize(line, CODE_TOKENS, ([, comment, string, tag, number, word], rest) => {
    if (comment) {
      return 'comment';
    }
    if (string) {
      return 'string';
    }
    if (tag) {
      return language === 'html' ? 'tag' : 'plain';
    }
    if (number) {
      return 'number';
    }
    if (word?.startsWith('@') || (word && KEYWORDS.has(word))) {
      return 'keyword';
    }
    if (word && language === 'css' && /^\s*:/.test(rest)) {
      return 'property';
    }
    if (word && /^\s*\(/.test(rest)) {
      return 'function';
    }
    return 'plain';
  });
}

function tokenize(
  line: string,
  pattern: RegExp,
  classify: (match: RegExpExecArray, rest: string) => TokenKind,
): CodeToken[] {
  const tokens: CodeToken[] = [];
  let last = 0;

  for (const match of line.matchAll(pattern)) {
    if (match.index > last) {
      tokens.push({ text: line.slice(last, match.index), kind: 'plain' });
    }
    const end = match.index + match[0].length;
    tokens.push({ text: match[0], kind: classify(match, line.slice(end)) });
    last = end;
  }

  if (last < line.length) {
    tokens.push({ text: line.slice(last), kind: 'plain' });
  }
  return tokens;
}
