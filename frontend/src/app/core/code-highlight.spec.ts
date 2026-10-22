import { firstCodeLine, highlight } from './code-highlight';

describe('highlight', () => {
  it('marks terminal lines with a prompt and colors the command and flags', () => {
    const [line] = highlight('git commit -m "Text"', 'terminal');

    expect(line.prompt).toBe(true);
    expect(line.tokens.find((token) => token.kind === 'command')?.text).toBe('git');
    expect(line.tokens.find((token) => token.kind === 'flag')?.text).toBe(' -m');
    expect(line.tokens.find((token) => token.kind === 'string')?.text).toBe('"Text"');
  });

  it('keeps the original text in the tokens', () => {
    const code = "def greet(name, greeting='Hallo'):\n    return f'{greeting}, {name}!'";
    const text = highlight(code, 'python')
      .map((line) => line.tokens.map((token) => token.text).join(''))
      .join('\n');

    expect(text).toBe(code);
  });

  it('shows comments without a prompt', () => {
    const [, comment] = highlight('git switch main\n# zurück zu main', 'terminal');

    expect(comment.prompt).toBe(false);
    expect(comment.tokens).toEqual([{ text: '# zurück zu main', kind: 'comment' }]);
  });

  it('adds a prompt only to commands inside code', () => {
    const lines = highlight("pip install django\nINSTALLED_APPS = ['app']", 'python');

    expect(lines.map((line) => line.prompt)).toEqual([true, false]);
  });

  it('colors keywords, functions and strings in code', () => {
    const [line] = highlight("const big = prices.filter(p => p > 15);", 'javascript');
    const kinds = Object.fromEntries(line.tokens.map((token) => [token.text, token.kind]));

    expect(kinds['const']).toBe('keyword');
    expect(kinds['filter']).toBe('function');
    expect(kinds['15']).toBe('number');
  });
});

describe('firstCodeLine', () => {
  it('skips comments and marks further lines', () => {
    expect(firstCodeLine('# views.py\nfrom x import y\nprint(y)')).toBe('from x import y …');
  });

  it('returns a single line unchanged', () => {
    expect(firstCodeLine('git pull')).toBe('git pull');
  });
});
