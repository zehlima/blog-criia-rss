import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';
const { PGlite } = await import(pathToFileURL(process.env.BORIS_PGLITE_MODULE).href);
const db = new PGlite();
for await (const line of createInterface({ input: process.stdin, crlfDelay: Infinity })) {
  try {
    const request = JSON.parse(line);
    if (request.close) { await db.close(); process.exit(0); }
    const result = request.exec ? await db.exec(request.sql) : await db.query(request.sql, request.params || []);
    process.stdout.write(JSON.stringify({ ok: true, rows: result.rows || [] }, (_, v) => typeof v === 'bigint' ? String(v) : v)+'\n');
  } catch (error) { process.stdout.write(JSON.stringify({ ok: false, error: error.message })+'\n'); }
}
