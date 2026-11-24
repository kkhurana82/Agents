// Runs Google's own kcmd OKF converter (toolbox/mdcode/src/libts/okf) over a
// build's bundle and prints the Knowledge Catalog Entry each concept becomes.
// No GCP call is made. Usage (from a knowledge-catalog checkout, toolbox/mdcode):
//   bun <kit>/catalog/kcmd_preview/preview.ts <build-dir> [entry-id]
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as yaml from 'yaml';
import {fileContentToConcept} from './src/libts/okf/concept';
import {conceptToEntry} from './src/libts/okf/concept_to_entry';

const [buildDir, only] = process.argv.slice(2);
const scope = yaml.parse(fs.readFileSync(path.join(buildDir, 'catalog.yaml'), 'utf8')).scope as string;
const [, project, location, group] = scope.split('.');
const groupName = `projects/${project}/locations/${location}/entryGroups/${group}`;
const bundle = path.join(buildDir, 'bundle');

function walk(d: string): string[] {
  return fs.readdirSync(d, {withFileTypes: true}).flatMap(e =>
    e.isDirectory() ? walk(path.join(d, e.name)) : e.name.endsWith('.md') ? [path.join(d, e.name)] : []);
}
const out: Record<string, unknown> = {};
for (const file of walk(bundle).sort()) {
  const id = path.relative(bundle, file).replace(/\.md$/, '');
  if (only && id !== only) continue;
  const entry = conceptToEntry(fileContentToConcept(fs.readFileSync(file, 'utf8'), id), groupName);
  out[id] = entry;
}
console.log(JSON.stringify(out, null, 2));
