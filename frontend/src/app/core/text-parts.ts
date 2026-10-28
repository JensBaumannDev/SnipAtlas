export function pushText(parts: { text: string }[], text: string): void {
  if (text) {
    parts.push({ text });
  }
}
