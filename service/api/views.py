from random import sample
from typing import List

from fastapi import APIRouter, FastAPI, Request, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyQuery, APIKeyHeader, APIKey
from pydantic import BaseModel

from service.api.exceptions import UserNotFoundError, ModelNotFoundError, \
    NotAuthorizedError
from service.log import app_logger
from service.settings import ServiceConfig, get_config


class RecoResponse(BaseModel):
    user_id: int
    items: List[int]


router = APIRouter()

API_KEY_NAME = "SECRET_TOKEN"

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
token_bearer = HTTPBearer(auto_error=False)


async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    token: HTTPAuthorizationCredentials = Security(token_bearer),
    config: ServiceConfig = Depends(get_config)
):
    SECRET_TOKEN = config.secret_token

    if api_key_query == SECRET_TOKEN:
        return api_key_query
    elif api_key_header == SECRET_TOKEN:
        return api_key_header
    if token is not None and token.credentials == SECRET_TOKEN:
        return token.credentials

    raise NotAuthorizedError()


@router.get(
    path="/health",
    tags=["Health"],
    response_model=str
)
async def health() -> str:
    return "I am alive"


@router.get(
    path="/reco/{model_name}/{user_id}",
    tags=["Recommendations"],
    response_model=RecoResponse,
    responses={404: {"description": "User/model not found"},
               401: {"description": "Authorization failed"}},
)
async def get_reco(
    request: Request,
    model_name: str,
    user_id: int,
    api_key: APIKey = Depends(get_api_key)
) -> RecoResponse:
    app_logger.info(f"Request for model: {model_name}, user_id: {user_id}")

    # проверка на существование модели, если нет - выдать ошибку
    if model_name not in request.app.state.model:
        raise ModelNotFoundError(error_message=f"Model {model_name} not found")

    # проверка допустимости пользователя, если нет - ошибка
    if user_id > 10 ** 9:
        raise UserNotFoundError(error_message=f"User {user_id} not found")

    # получаем данные по пользователям и позициям из настроек
    items = request.app.state.items
    item_list = request.app.state.item_list
    # получаем данные по количеству позиций в выдаче
    k_recs = request.app.state.k_recs

    # формируем массив с рекомендациями
    rec = items[items["user_id"] == user_id]["item_id"].values
    # проверяем на пустой результат
    if len(rec) == 0:
        rec = sample(item_list, k=k_recs)
    else:
        rec = rec[0][:k_recs]
        if len(rec) < k_recs:
            rec.extend(
                sample(list(set(item_list) - set(rec)), k=k_recs - len(rec)))
    return RecoResponse(user_id=user_id, items=rec)


def add_views(app: FastAPI) -> None:
    app.include_router(router)
