/**
 * Copies the shared contract fixtures into public/ so the mock adapter can fetch them.
 *
 * The fixtures live at the repository root because both the frontend and the backend
 * validate against the same files. This copy is generated and gitignored; never edit
 * the copy, edit ../fixtures and re-run.
 */

import { cp, mkdir, rm } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const source = resolve(here, '../../fixtures');
const target = resolve(here, '../public/fixtures');

await rm(target, { recursive: true, force: true });
await mkdir(target, { recursive: true });
await cp(source, target, { recursive: true, filter: (p) => !p.endsWith('.md') });

console.log(`fixtures synced: ${source} -> ${target}`);
