import { describe, it, expect } from 'vitest';

describe('Werkzeugkette', () => {
  it('führt Tests aus', () => {
    expect(1 + 1).toBe(2);
  });

  it('stellt die happy-dom-Umgebung bereit', () => {
    expect(typeof document).toBe('object');
  });
});
