# Backroom ⇄ DuckDB Integration (Drop-in)

This folder contains a minimal, production-friendly way to integrate DuckDB into your existing **Backroom** Node project.

## Files
- `db/duckdb.js` — creates/opens `mydb.duckdb`, tunes pragmas, and ensures `items` table exists.
- `repositories/itemsRepo.js` — simple data-access helpers.
- `routes/items.js` — optional Express routes (`GET /items`, `POST /items`, `PUT /items/:id`).
- `scripts/init-duckdb.js` — one-time seed to insert an example row.

## Install
From your Backroom repo root:
```bash
npm install duckdb
```

Copy these files into your project (preserving folders):
```
/db/duckdb.js
/repositories/itemsRepo.js
/routes/items.js           # optional if you use Express
/scripts/init-duckdb.js
```

## Wire it up (Express)
In your main server file (e.g., `app.js` or `server.js`):
```js
const express = require('express');
const app = express();

app.use(express.json());

// Mount items API
app.use('/items', require('./routes/items'));

const port = process.env.PORT || 3000;
app.listen(port, () => console.log('Backroom listening on', port));
```

## Scripts
Add to `package.json`:
```json
{
  "scripts": {
    "db:init": "node scripts/init-duckdb.js",
    "db:read": "node -e \"(async()=>{const { con }=require('./db/duckdb');con.all('SELECT * FROM items',(e,r)=>{if(e)throw e;console.log(r);con.close();});})()\""
  }
}
```

Seed and test:
```bash
npm run db:init
npm run db:read
# Expect: [ { id: 1, label: 'slime' } ]
```

## Configuration
- **DB path**: set `DUCKDB_PATH=/absolute/or/relative/path/to/mydb.duckdb`. Defaults to `<repo>/mydb.duckdb`.
- Add to `.gitignore`:
```
mydb.duckdb
mydb.duckdb.wal
```
- For Docker, **mount a volume** so the DB persists:
```dockerfile
# Example snippet
RUN npm install duckdb
VOLUME /data
ENV DUCKDB_PATH=/data/mydb.duckdb
```
```yaml
# docker-compose.yml
volumes:
  backroom_db:

services:
  backroom:
    volumes:
      - backroom_db:/data
    environment:
      - DUCKDB_PATH=/data/mydb.duckdb
```

## Notes
- Avoid `CREATE TEMP TABLE` for persistent data.
- Use `con.run("CHECKPOINT;")` after bulk inserts if you want to force WAL merge, though closing cleanly is usually enough.
- You can inspect the DB with the DuckDB CLI: `duckdb mydb.duckdb` → `SELECT * FROM items;`

