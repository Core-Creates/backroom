// scripts/init-duckdb.js
// Seed the DB once.
const { con, dbPath } = require('../db/duckdb');

con.run("INSERT INTO items VALUES (1,'slime')", (err) => {
  if (err && !/Duplicate/.test(String(err))) {
    console.error("Insert failed:", err);
  } else {
    console.log("Inserted seed row into items.");
  }
  con.close(() => {
    console.log("Closed connection. DB at", dbPath);
  });
});
