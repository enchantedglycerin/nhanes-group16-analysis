// Local Thai word segmentation for counting and PDF line-break opportunities.
import fs from 'node:fs';
const [input, output] = process.argv.slice(2);
const texts = JSON.parse(fs.readFileSync(input, 'utf8'));
const segmenter = new Intl.Segmenter('th', {granularity: 'word'});
const result = {};
for (const text of texts) {
  const segments = [...segmenter.segment(text)];
  result[text] = {
    count: segments.filter(s => s.isWordLike).length,
    display: segments.map((s, i) => s.segment + (i < segments.length - 1 && /[\u0E00-\u0E7F]/u.test(s.segment) ? '\u200b' : '')).join(''),
  };
}
fs.writeFileSync(output, JSON.stringify(result), 'utf8');
