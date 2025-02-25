from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import NewType, Optional, TypedDict

UserId = NewType("UserId", str)


@dataclass(frozen=True)
class User:
    id: UserId
    sub: str
    name: str
    email: Optional[str]
    created_at: datetime


class UserUpdateParams(TypedDict, total=False):
    name: str


class UserStore(ABC):
    @abstractmethod
    async def create_user(
        self,
        sub: str,
        name: str,
        email: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> User: ...

    @abstractmethod
    async def read_user(
        self,
        user_id: UserId,
    ) -> Optional[User]: ...

    @abstractmethod
    async def read_user_by_sub(
        self,
        sub: str,
    ) -> Optional[User]: ...

    @abstractmethod
    async def update_user(
        self,
        user_id: UserId,
        params: UserUpdateParams,
    ) -> User: ...
