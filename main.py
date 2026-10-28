import asyncio
import time
from typing import Literal

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing_extensions import Annotated

from store import MemoryStore, get_current_user, get_store

app = FastAPI(title="School Catalogue")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def home():
    return {"catalogue": "School Catalogue"}


@app.get("/items")
def list_items(
    category: str | None = None,
    sort: Literal["title", "year"] = "title",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    store: MemoryStore = Depends(get_store),
):
    items = store.all()
    if category is not None:
        items = [item for item in items if item["category"] == category]
    items = sorted(items, key=lambda item: item[sort])
    return items[:limit]


@app.get("/items/{item_id}")
def get_item(item_id: int, store: MemoryStore = Depends(get_store)):
    item = store.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.post("/items")
def create_item(
    title: Annotated[str, Form(min_length=1)],
    category: Annotated[str, Form(min_length=1)],
    year: Annotated[int, Form(ge=1900, le=2100)],
    user: str = Depends(get_current_user),
    store: MemoryStore = Depends(get_store),
):
    new_id = store.add(title, category, year)
    return RedirectResponse(url=f"/items/{new_id}", status_code=303)


@app.get("/slow-async")
async def slow_async():
    time.sleep(3)
    return {"route": "slow-async"}


@app.get("/slow-sync")
def slow_sync():
    time.sleep(3)
    return {"route": "slow-sync"}


@app.get("/fine-async")
async def fine_async():
    await asyncio.sleep(3)
    return {"route": "fine-async"}


@app.get("/ping")
def ping():
    return {"pong": True}


@app.get("/catalogue")
def catalogue(request: Request, store: MemoryStore = Depends(get_store)):
    return templates.TemplateResponse(request, "catalogue.html", {"items": store.all()})
