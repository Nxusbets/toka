import { describe, it, expect } from 'vitest';
import { formatDate, formatDateTime, formatCost, formatTokens } from '../../src/utils/format';

describe('formatDate', () => {
  it('returns formatted date string', () => {
    const result = formatDate('2024-01-15T10:30:00Z');
    expect(result).toBe('Jan 15, 2024');
  });
});

describe('formatDateTime', () => {
  it('returns formatted datetime string', () => {
    const result = formatDateTime('2024-01-15T10:30:00Z');
    expect(result).toContain('Jan 15, 2024');
    expect(result).toMatch(/AM|PM/);
  });
});

describe('formatCost', () => {
  it('returns $0.0000 format for positive cost', () => {
    const result = formatCost(0.0123);
    expect(result).toBe('$0.0123');
  });

  it('returns <$0.01 for very small cost', () => {
    const result = formatCost(0.001);
    expect(result).toBe('<$0.01');
  });
});

describe('formatTokens', () => {
  it('returns comma-separated number for small values', () => {
    const result = formatTokens(500);
    expect(result).toBe('500');
  });

  it('returns K format for thousands', () => {
    const result = formatTokens(1500);
    expect(result).toBe('1.5K');
  });

  it('returns M format for millions', () => {
    const result = formatTokens(2500000);
    expect(result).toBe('2.5M');
  });
});
