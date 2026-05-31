"""Recipes API — CRUD + run + recording."""
import uuid
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Recipe, RecipeCreate, RecipePublic, RecipeRun, RecipeRunPublic, Workspace
from app.services.recipes.validator import RecipeValidationError, parse_and_validate

router = APIRouter(prefix="/recipes", tags=["recipes"])


def _get_workspace(db: Session) -> Workspace:
    ws = db.exec(select(Workspace).limit(1)).first()
    if not ws:
        raise HTTPException(status_code=503, detail="Workspace not initialised")
    return ws


@router.get("/", response_model=list[RecipePublic])
def list_recipes(db: SessionDep, _current_user: CurrentUser) -> list[RecipePublic]:
    ws = _get_workspace(db)
    recipes = db.exec(select(Recipe).where(Recipe.workspace_id == ws.id)).all()
    return [RecipePublic(**r.model_dump()) for r in recipes]


@router.post("/", response_model=RecipePublic, status_code=201)
def create_recipe(body: RecipeCreate, db: SessionDep, _current_user: CurrentUser) -> RecipePublic:
    ws = _get_workspace(db)
    try:
        schema = parse_and_validate(body.yaml_content)
    except RecipeValidationError as e:
        raise HTTPException(status_code=422, detail={"errors": e.errors})
    import json
    recipe = Recipe(
        workspace_id=ws.id,
        name=body.name,
        version=schema.version,
        families_json=json.dumps(schema.families),
        yaml_content=body.yaml_content,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return RecipePublic(**recipe.model_dump())


@router.get("/{recipe_id}", response_model=RecipePublic)
def get_recipe(recipe_id: uuid.UUID, db: SessionDep, _current_user: CurrentUser) -> RecipePublic:
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RecipePublic(**recipe.model_dump())


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: uuid.UUID, db: SessionDep, _current_user: CurrentUser) -> None:
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    db.delete(recipe)
    db.commit()


@router.post("/{recipe_id}/runs", response_model=RecipeRunPublic, status_code=201)
async def run_recipe(
    recipe_id: uuid.UUID,
    device_id: uuid.UUID,
    db: SessionDep,
    _current_user: CurrentUser,
    inputs: dict = {},
) -> RecipeRunPublic:
    ws = _get_workspace(db)
    from app.services.recipes.runner import run_recipe as _run
    try:
        run = await _run(db, recipe_id, device_id, inputs, ws.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RecipeRunPublic(**run.model_dump())


@router.get("/{recipe_id}/runs", response_model=list[RecipeRunPublic])
def list_runs(recipe_id: uuid.UUID, db: SessionDep, _current_user: CurrentUser) -> list[RecipeRunPublic]:
    runs = db.exec(select(RecipeRun).where(RecipeRun.recipe_id == recipe_id)).all()
    return [RecipeRunPublic(**r.model_dump()) for r in runs]


@router.get("/{recipe_id}/runs/{run_id}", response_model=RecipeRunPublic)
def get_run(recipe_id: uuid.UUID, run_id: uuid.UUID, db: SessionDep, _current_user: CurrentUser) -> RecipeRunPublic:
    run = db.get(RecipeRun, run_id)
    if not run or run.recipe_id != recipe_id:
        raise HTTPException(status_code=404, detail="Run not found")
    return RecipeRunPublic(**run.model_dump())
