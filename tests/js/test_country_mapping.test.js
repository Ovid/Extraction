import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { NUMERIC_MAP, COUNTRY_NAMES } from '../../js/lib.js';

describe('NUMERIC_MAP', () => {
  it('all values are valid 3-letter alpha-3 codes', () => {
    for (const alpha3 of Object.values(NUMERIC_MAP)) {
      expect(alpha3).toMatch(/^[A-Z]{3}$/);
    }
  });

  it('no duplicate numeric IDs mapping to different alpha-3', () => {
    const seen = {};
    for (const [numId, alpha3] of Object.entries(NUMERIC_MAP)) {
      if (seen[numId]) {
        expect(seen[numId]).toBe(alpha3);
      }
      seen[numId] = alpha3;
    }
  });
});

describe('COUNTRY_NAMES', () => {
  it('all keys are valid 3-letter alpha-3 codes', () => {
    for (const code of Object.keys(COUNTRY_NAMES)) {
      expect(code).toMatch(/^[A-Z]{3}$/);
    }
  });

  it('every country in scores.json has a COUNTRY_NAMES entry or is in scores data', () => {
    const scoresRaw = readFileSync('data/scores.json', 'utf-8');
    const scores = JSON.parse(scoresRaw);
    const missingNames = [];
    for (const code of Object.keys(scores.countries)) {
      if (!COUNTRY_NAMES[code] && !scores.countries[code].name) {
        missingNames.push(code);
      }
    }
    expect(missingNames).toEqual([]);
  });
});
