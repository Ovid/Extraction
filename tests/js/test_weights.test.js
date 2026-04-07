import { describe, it, expect } from 'vitest';
import { normalizeWeights, DOMAIN_KEYS } from '../../js/lib.js';

describe('normalizeWeights', () => {
  it('normalizes slider values to sum to 1.0', () => {
    const raw = {};
    DOMAIN_KEYS.forEach(k => raw[k] = 50);
    const result = normalizeWeights(raw);
    const sum = Object.values(result).reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1.0, 10);
  });

  it('handles all sliders at zero without division by zero', () => {
    const raw = {};
    DOMAIN_KEYS.forEach(k => raw[k] = 0);
    const result = normalizeWeights(raw);
    Object.values(result).forEach(v => expect(v).toBe(0));
  });

  it('one at max, rest at zero gives weight 1.0', () => {
    const raw = {};
    DOMAIN_KEYS.forEach(k => raw[k] = 0);
    raw.political_capture = 100;
    const result = normalizeWeights(raw);
    expect(result.political_capture).toBe(1.0);
    DOMAIN_KEYS.filter(k => k !== 'political_capture').forEach(k => {
      expect(result[k]).toBe(0);
    });
  });

  it('equal values produce equal weights', () => {
    const raw = {};
    DOMAIN_KEYS.forEach(k => raw[k] = 42);
    const result = normalizeWeights(raw);
    const expected = 1 / DOMAIN_KEYS.length;
    DOMAIN_KEYS.forEach(k => {
      expect(result[k]).toBeCloseTo(expected, 10);
    });
  });
});
