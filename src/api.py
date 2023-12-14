import json
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import sqlite3

from core.data_structures import FeaturesStructure, Task
from core.utils import (
    check_task_state,
    get_or_create_task,
    get_task_result,
    verify_task_table,
    verify_data_table,
    verify_prescore_table,
)

CONFIG = json.load(open("./configs/api_config.json", "r", encoding="utf-8"))
app = FastAPI()

folder = CONFIG["folder_data_base"]
if not os.path.exists(folder):
    os.makedirs(folder, exist_ok=True)

connection_db = sqlite3.connect(CONFIG["data_base"])
cursor_db = connection_db.cursor()

verify_data_table(cursor_db=cursor_db, connection_db=connection_db, columns=CONFIG["features"])
verify_prescore_table(cursor_db=cursor_db, connection_db=connection_db, columns=CONFIG["banks"])
verify_task_table(cursor_db=cursor_db, connection_db=connection_db)


@app.get("/", response_class=HTMLResponse, status_code=200)
async def main_page(request: Request) -> HTMLResponse:
    """Редирект на страницу документации

    Args:
        request (Request): запрос (от браузера)

    Returns:
        HTMLResponse: ответ в формате HTML страницы
    """
    return RedirectResponse(url="/docs")


@app.post("/upload_features", status_code=201)
async def upload_features(request: FeaturesStructure) -> Task:
    """Добавление текста для аннотации.

    Args:
        request (FeaturesStructure): запрос, в теле которого содержаться фичи, в соответсвии с FeaturesStructure.
            headers: {"content-type": "application/json"}
            body: {features: {структуру см. в FeaturesStructure}}

    Returns:
        Task: объект задачи (см. Task)
    """
    return get_or_create_task(features=request, connection_db=connection_db, cursor_db=cursor_db)


@app.get("/check_task", status_code=200)
async def check_task(task_id: str) -> bool:
    """Проверка состояния задачи

    Args:
        task_id (str): id задачи

    Returns:
        bool: флаг is_complete (Task), если True - задача выполнена
    """
    task_state = check_task_state(task_id=task_id, connection_db=connection_db, cursor_db=cursor_db)
    if task_state == -1:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_state == 1


@app.get("/get_result", status_code=200)
async def get_result(task_id: str) -> str:
    """Получение результата пре-скоринга

    Args:
        task_id (str): id задачи

    Returns:
        str: аннотация
    """
    result = get_task_result(task_id, connection_db=connection_db, cursor_db=cursor_db)
    if result:
        reuslt = {k: v for k, v in zip(["task_id"] + CONFIG["banks"], result)}
        json_compatible_item_data = jsonable_encoder(reuslt)
        return JSONResponse(content=json_compatible_item_data)
    else:
        raise HTTPException(status_code=404, detail="Task not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=CONFIG["host"], port=int(CONFIG["port"]))
