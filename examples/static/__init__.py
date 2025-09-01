from fastapi import APIRouter
from flux0_api.auth import AuthedUser
from flux0_nanodb.api import DocumentDatabase
from lagom import Container

from examples.static.static_store import ExampleStaticDocumentStore

from .static_agent import StaticAgentRunner


async def init_module(container: Container) -> None:
    container[StaticAgentRunner] = StaticAgentRunner

    example_store = ExampleStaticDocumentStore(container[DocumentDatabase])
    await example_store.setup()
    container[ExampleStaticDocumentStore] = example_store


async def shutdown_module() -> None:
    print("Shutdown!")


async def get_routers(container: Container) -> list[APIRouter]:
    router = APIRouter(prefix="/static")

    @router.get("/hello")
    async def hello_world(user: AuthedUser):
        example_store: ExampleStaticDocumentStore = container[ExampleStaticDocumentStore]
        doc = await example_store.create()
        return {
            "message": f"Hello {user.name}. Your id is {user.id}. We created a static doc for you: {doc}"
        }

    return [router]
