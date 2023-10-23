from contextlib import asynccontextmanager, contextmanager
from typing import (
    Any,
    AsyncContextManager,
    AsyncGenerator,
    Callable,
    Generator,
    Generic,
    Optional,
    Sequence,
    Type,
)
from typing import ContextManager as ContextManagerType

from typing_extensions import Self

from permchain.channels.base import (
    Channel,
    EmptyChannelError,
    InvalidUpdateError,
    Value,
)


class ContextManager(Generic[Value], Channel[Value, None]):
    value: Value

    def __init__(
        self,
        ctx: Optional[Callable[[], ContextManagerType[Value]]] = None,
        actx: Optional[Callable[[], AsyncContextManager[Value]]] = None,
        typ: Optional[Type[Value]] = None,
    ) -> None:
        if ctx is None and actx is None:
            raise ValueError("Must provide either sync or async context manager.")

        self.typ = typ
        self.ctx = ctx
        self.actx = actx

    @property
    def ValueType(self) -> Any:
        """The type of the value stored in the channel."""
        return (
            self.typ
            or (self.ctx if hasattr(self.ctx, "__enter__") else None)
            or (self.actx if hasattr(self.actx, "__aenter__") else None)
            or None
        )

    @property
    def UpdateType(self) -> Type[None]:
        """The type of the update received by the channel."""
        raise InvalidUpdateError()

    @contextmanager
    def empty(self, checkpoint: Optional[str] = None) -> Generator[Self, None, None]:
        if self.ctx is None:
            raise ValueError("Cannot enter sync context manager.")

        empty = self.__class__(ctx=self.ctx, actx=self.actx, typ=self.typ)
        # ContextManager doesn't have a checkpoint
        ctx = self.ctx()
        empty.value = ctx.__enter__()
        try:
            yield empty
        finally:
            ctx.__exit__(None, None, None)

    @asynccontextmanager
    async def aempty(
        self, checkpoint: Optional[str] = None
    ) -> AsyncGenerator[Self, None]:
        if self.actx is not None:
            empty = self.__class__(ctx=self.ctx, actx=self.actx, typ=self.typ)
            # ContextManager doesn't have a checkpoint
            actx = self.actx()
            empty.value = await actx.__aenter__()
            try:
                yield empty
            finally:
                await actx.__aexit__(None, None, None)
        else:
            with self.empty() as empty:
                yield empty

    def update(self, values: Sequence[None]) -> None:
        raise InvalidUpdateError()

    def get(self) -> Value:
        try:
            return self.value
        except AttributeError:
            raise EmptyChannelError()

    def checkpoint(self) -> None:
        return None