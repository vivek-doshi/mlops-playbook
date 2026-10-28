// yaml-renderer.worker.ts
interface Token {
  text: string;
  type: string;
}

function tokenizeLine(line: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;
  while (i < line.length) {
    // Comment
    if (line[i] === '#') {
      tokens.push({ text: line.slice(i), type: 'comment' });
      break;
    }
    // String
    if (line[i] === '"' || line[i] === "'") {
      const quote = line[i];
      let j = i + 1;
      while (j < line.length && line[j] !== quote) {
        j++;
      }
      j++; // include closing quote
      tokens.push({ text: line.slice(i, j), type: 'string' });
      i = j;
      continue;
    }
    // Key
    const keyMatch = line.slice(i).match(/^\s*[\w.-]+:/);
    if (keyMatch) {
      tokens.push({ text: keyMatch[0], type: 'key' });
      i += keyMatch[0].length;
      continue;
    }
    // Boolean
    if (line.slice(i, i + 4) === 'true') {
      tokens.push({ text: 'true', type: 'boolean' });
      i += 4;
      continue;
    }
    if (line.slice(i, i + 5) === 'false') {
      tokens.push({ text: 'false', type: 'boolean' });
      i += 5;
      continue;
    }
    // Number
    const numMatch = line.slice(i).match(/^\d+(\.\d+)?/);
    if (numMatch) {
      tokens.push({ text: numMatch[0], type: 'number' });
      i += numMatch[0].length;
      continue;
    }
    // Default
    tokens.push({ text: line[i], type: 'default' });
    i++;
  }
  return tokens;
}

const COLOR_MAP: Record<string, string> = {
  key: '#E06C75',
  string: '#98C379',
  number: '#D19A66',
  boolean: '#D19A66',
  comment: '#5C6370',
  default: '#ABB2BF',
};

self.onmessage = (e: MessageEvent) => {
  const { canvas, text, pixelRatio = 1, fontFamily = 'Courier New', fontSize = 14, lineHeight = 1.65, maxWidth = 800 } = e.data as any;
  
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  // Parse font
  const fontMatch = `${fontSize}px ${fontFamily}`.match(/(\d+)px/);
  const baseFontSize = fontMatch ? parseInt(fontMatch[1], 10) : fontSize;
  const fontFamilyName = fontFamily.replace(/(\d+)px/, '').trim();
  
  ctx.font = `${baseFontSize}px ${fontFamilyName}`;
  ctx.scale(pixelRatio, pixelRatio);
  
  const linePx = baseFontSize * lineHeight;
  const padding = 24;

  // Split content into lines
  const rawLines = text.split('\n');
  const wrappedLines: string[] = [];

  for (const line of rawLines) {
    if (line.length === 0) {
      wrappedLines.push('');
      continue;
    }
    // Measure and wrap long lines
    const words = line.split(' ');
    let current = '';
    for (const word of words) {
      const test = current ? `${current} ${word}` : word;
      const metrics = ctx.measureText(test);
      if (metrics.width > maxWidth && current) {
        wrappedLines.push(current);
        current = word;
      } else {
        current = test;
      }
    }
    if (current) wrappedLines.push(current);
  }

  const totalHeight = wrappedLines.length * linePx + padding * 2;
  const totalWidth = Math.max(
    ...wrappedLines.map(l => ctx.measureText(l).width),
    0
  ) + padding * 2;

  // Set canvas size for HiDPI
  canvas.width = Math.ceil(totalWidth * pixelRatio);
  canvas.height = Math.ceil(totalHeight * pixelRatio);

  // Clear
  ctx.clearRect(0, 0, totalWidth, totalHeight);

  // Draw text
  ctx.textBaseline = 'top';
  ctx.font = `${baseFontSize}px ${fontFamilyName}`;

  let y = padding;
  for (let lineIndex = 0; lineIndex < wrappedLines.length; lineIndex++) {
    const line = wrappedLines[lineIndex];
    const tokens = tokenizeLine(line);
    let x = padding;
    for (const token of tokens) {
      const tokenText = token.text;
      const textWidth = ctx.measureText(tokenText).width;
      // Handle wrapping within token
      if (x + textWidth > totalWidth - padding) {
        y += linePx;
        x = padding;
      }
      ctx.fillStyle = COLOR_MAP[token.type] || COLOR_MAP.default;
      ctx.fillText(tokenText, x, y);
      x += textWidth;
    }
    y += linePx;
  }
};
