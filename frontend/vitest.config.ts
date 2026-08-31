import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vitest/config';

/**
 * The `@/` alias is a project-wide convention declared in tsconfig.json, but
 * vitest resolves imports itself and does not read that file. Until now no test
 * had noticed: the tested modules imported only types under the alias, and a
 * type-only import is erased before anything has to resolve it. The first
 * runtime import under `@/` in a tested module failed to load its whole suite.
 *
 * Declaring the alias here keeps test files and application files writing
 * imports the same way.
 */
export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('.', import.meta.url)),
    },
  },
});
