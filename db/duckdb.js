// db/duckdb.js
// Centralized DuckDB connection helper for the Backroom app.
const path = require('path');
const fs = require('fs');
const duckdb = require('duckdb');

// Resolve DB path from env or default to project root
const DB_PATH = process.env.DUCKDB_PATH || path.resolve(process.cwd(), 'mydb.duckdb');

// Make sure directory exists
fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

const db = new duckdb.Database(DB_PATH);
const con = db.connect();

// Optional: pragma tuning
con.run("PRAGMA threads=4");

// Initialize schema if not exists
con.run(`
  CREATE TABLE IF NOT EXISTS items(
    id INTEGER,
    label TEXT
  );
`);

module.exports = {
  con,
  get dbPath() { return DB_PATH; }
};
