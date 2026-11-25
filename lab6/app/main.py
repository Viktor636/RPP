from contextlib import asynccontextmanager

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from app.db.models import Base
from app.db.session import engine
from app.graphql.context import get_context
from app.graphql.schema import schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    graphiql=True,
)
app.include_router(graphql_app, prefix="/graphql")
