# routes/express_to_fastapi.py
"""
FastAPI router equivalent of the provided Express router snippet.

Original (Express):
-------------------
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

Python (FastAPI):
-----------------
- PUT /{id}
- JSON body: {"label": "<string>"}
- Returns {"ok": true} on success
- 400 if id/label invalid
- 500 if upsert_item raises an exception
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class UpdateBody(BaseModel):
    label: str

async def upsert_item(item_id: int, label: str) -> None:
    """
    Stub for database upsert logic.
    Replace this with your real persistence code.
    Should be an 'async' function to mirror the original.
    """
    # Example no-op (pretend success)
    return None

@router.put("/{id}")
async def update_item(id: int, body: UpdateBody):
    # FastAPI/Pydantic already validates types, but we keep the explicit check
    # to preserve the original behavior/message.
    if not isinstance(id, int) or not isinstance(body.label, str):
        raise HTTPException(status_code=400, detail="valid id param and label required")

    try:
        await upsert_item(id, body.label)
        return {"ok": True}
    except Exception as e:  # pragma: no cover
        # Mirror Express behavior: 500 with error message
        raise HTTPException(status_code=500, detail=str(e))
