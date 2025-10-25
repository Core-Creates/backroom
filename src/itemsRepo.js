// repositories/itemsRepo.js
const { con } = require('../db/duckdb');

function insertItem(id, label) {
  return new Promise((resolve, reject) => {
    con.run("INSERT INTO items VALUES (?, ?)", [id, label], (err) => {
      if (err) return reject(err);
      resolve();
    });
  });
}

function listItems() {
  return new Promise((resolve, reject) => {
    con.all("SELECT id, label FROM items ORDER BY id", (err, rows) => {
      if (err) return reject(err);
      resolve(rows);
    });
  });
}

function upsertItem(id, label) {
  // Simple upsert using DELETE+INSERT (DuckDB supports MERGE, but keep it minimal here)
  return new Promise((resolve, reject) => {
    con.run("DELETE FROM items WHERE id = ?", [id], (err) => {
      if (err) return reject(err);
      con.run("INSERT INTO items VALUES (?, ?)", [id, label], (err2) => {
        if (err2) return reject(err2);
        resolve();
      });
    });
  });
}

module.exports = { insertItem, listItems, upsertItem };
