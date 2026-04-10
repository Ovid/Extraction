import { describe, it, expect } from 'vitest';
import { filterEntries } from '../../js/lib.js';

describe('filterEntries', () => {
  const entries = [
    { code: 'USA', name: 'United States', composite: 35 },
    { code: 'GBR', name: 'United Kingdom', composite: 20 },
    { code: 'DNK', name: 'Denmark', composite: 15 },
    { code: 'ARE', name: 'United Arab Emirates', composite: 30 },
  ];

  it('returns all entries for empty query', () => {
    expect(filterEntries(entries, '')).toEqual(entries);
  });

  it('filters by case-insensitive substring', () => {
    const result = filterEntries(entries, 'united');
    expect(result.map((e) => e.code)).toEqual(['USA', 'GBR', 'ARE']);
  });

  it('returns empty array when nothing matches', () => {
    expect(filterEntries(entries, 'zzz')).toEqual([]);
  });

  it('matches partial names', () => {
    const result = filterEntries(entries, 'den');
    expect(result.map((e) => e.code)).toEqual(['DNK']);
  });
});
