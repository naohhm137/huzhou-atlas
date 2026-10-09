import { describe, expect, it } from 'vitest';
import { adjustCompare } from '../cityInteraction';

describe('Nanxun visual comparison', () => {
  it('moves five points per arrow and clamps at either end', () => {
    expect(adjustCompare(50, 'ArrowLeft')).toBe(45);
    expect(adjustCompare(50, 'ArrowRight')).toBe(55);
    expect(adjustCompare(2, 'ArrowLeft')).toBe(0);
    expect(adjustCompare(98, 'ArrowRight')).toBe(100);
  });

  it('supports keyboard endpoints without changing state on unrelated keys', () => {
    expect(adjustCompare(46, 'Home')).toBe(0);
    expect(adjustCompare(46, 'End')).toBe(100);
    expect(adjustCompare(46, 'Escape')).toBe(46);
  });
});
