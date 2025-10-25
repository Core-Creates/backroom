// routes/items.js
// Optional Express router to expose items endpoints.
const express = require('express');
const router = express.Router();
const { insertItem, listItems, upsertItem } = require('../repositories/itemsRepo');

router.get('/', async (req, res) => {
  try {
    const rows = await listItems();
    res.json(rows);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.post('/', async (req, res) => {
  const { id, label } = req.body || {};
  if (typeof id !== 'number' || typeof label !== 'string') {
    return res.status(400).json({ error: "id (number) and label (string) required" });
  }
  try {
    await insertItem(id, label);
    res.status(201).json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

router.put('/:id', async (req, res) => {
  const id = Number(req.params.id);
  const { label } = req.body || {};
  if (!Number.isFinite(id) || typeof label !== 'string') {
    return res.status(400).json({ error: "valid id param and label required" });
  }
  try {
    await upsertItem(id, label);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;
