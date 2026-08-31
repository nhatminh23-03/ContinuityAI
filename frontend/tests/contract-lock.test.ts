/**
 * The contract lock (Phase 5, item 3).
 *
 * Every file in the repository-root `fixtures/` directory must validate against
 * its Zod schema — strictly: unknown fields fail. The map in schemas.ts must
 * cover every fixture, and every mapped fixture must exist, so a fixture added
 * or removed on either side breaks this test instead of breaking a screen.
 *
 * This must pass before any UI work continues.
 */

import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { fixtureSchemas } from '../lib/api/schemas';

const FIXTURES_DIR = resolve(__dirname, '../../fixtures');

const fixtureFiles = readdirSync(FIXTURES_DIR)
  .filter((name) => name.endsWith('.json'))
  .map((name) => name.replace(/\.json$/, ''))
  .sort();

describe('contract lock — fixtures/ vs docs/API_CONTRACT.md schemas', () => {
  it('covers every fixture file with a schema', () => {
    expect(fixtureFiles).toEqual(Object.keys(fixtureSchemas).sort());
  });

  for (const name of fixtureFiles) {
    it(`fixtures/${name}.json satisfies its contract schema`, () => {
      const schema = fixtureSchemas[name as keyof typeof fixtureSchemas];
      expect(schema, `no schema mapped for fixture '${name}'`).toBeDefined();

      const payload = JSON.parse(readFileSync(join(FIXTURES_DIR, `${name}.json`), 'utf8'));
      const result = schema.safeParse(payload);

      if (!result.success) {
        const issues = result.error.issues
          .map((issue) => `  ${issue.path.join('.') || '(root)'}: ${issue.message}`)
          .join('\n');
        throw new Error(`fixture '${name}' violates the contract:\n${issues}`);
      }
    });
  }
});
