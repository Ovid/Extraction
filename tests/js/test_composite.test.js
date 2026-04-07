import { describe, it, expect } from 'vitest';
import { computeComposite, DOMAIN_KEYS } from '../../js/lib.js';

describe('computeComposite', () => {
  const allDomains = {
    political_capture: { score: 40 },
    economic_concentration: { score: 60 },
    financial_extraction: { score: 50 },
    institutional_gatekeeping: { score: 30 },
    information_capture: { score: 70 },
    resource_capture: { score: 20 },
    transnational_facilitation: { score: 80 },
  };

  it('computes weighted average with equal weights', () => {
    const weights = {};
    DOMAIN_KEYS.forEach((k) => (weights[k] = 1 / 7));
    const result = computeComposite(allDomains, weights, DOMAIN_KEYS);
    expect(result).toBe(50);
  });

  it('handles custom weights with some zeroed', () => {
    const weights = {};
    DOMAIN_KEYS.forEach((k) => (weights[k] = 0));
    weights.political_capture = 0.5;
    weights.economic_concentration = 0.5;
    const result = computeComposite(allDomains, weights, DOMAIN_KEYS);
    expect(result).toBe(50);
  });

  it('excludes missing domains from average', () => {
    const partial = {
      political_capture: { score: 40 },
      economic_concentration: { score: 60 },
    };
    const weights = {};
    DOMAIN_KEYS.forEach((k) => (weights[k] = 1 / 7));
    const result = computeComposite(partial, weights, DOMAIN_KEYS);
    expect(result).toBe(50);
  });

  it('returns null when all domains missing', () => {
    const weights = {};
    DOMAIN_KEYS.forEach((k) => (weights[k] = 1 / 7));
    const result = computeComposite({}, weights, DOMAIN_KEYS);
    expect(result).toBeNull();
  });

  it('returns null when all weights are zero', () => {
    const weights = {};
    DOMAIN_KEYS.forEach((k) => (weights[k] = 0));
    const result = computeComposite(allDomains, weights, DOMAIN_KEYS);
    expect(result).toBeNull();
  });

  it('single domain equals that score', () => {
    const single = { political_capture: { score: 73 } };
    const weights = {};
    DOMAIN_KEYS.forEach((k) => (weights[k] = 1 / 7));
    const result = computeComposite(single, weights, DOMAIN_KEYS);
    expect(result).toBe(73);
  });
});
