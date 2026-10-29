const BROWSERS: readonly [RegExp, string][] = [
  [/Edg\/(\d+)/, 'Edge'],
  [/OPR\/(\d+)/, 'Opera'],
  [/Firefox\/(\d+)/, 'Firefox'],
  [/Chrome\/(\d+)/, 'Chrome'],
  [/Version\/(\d+).*Safari/, 'Safari'],
];

const SYSTEMS: readonly [RegExp, string][] = [
  [/Windows/, 'Windows'],
  [/Android/, 'Android'],
  [/iPhone|iPad/, 'iOS'],
  [/Mac OS X/, 'macOS'],
  [/Linux/, 'Linux'],
];

export function describeEnvironment(userAgent: string): string {
  const browser = BROWSERS.map(([pattern, name]) => {
    const match = pattern.exec(userAgent);
    return match ? `${name} ${match[1]}` : undefined;
  }).find(Boolean);
  const system = SYSTEMS.find(([pattern]) => pattern.test(userAgent))?.[1];
  return [browser, system].filter(Boolean).join(', ');
}
