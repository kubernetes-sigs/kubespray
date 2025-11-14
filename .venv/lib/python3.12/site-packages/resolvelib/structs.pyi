from abc import ABCMeta
from typing import (
    Callable,
    Container,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Tuple,
    TypeVar,
    Union,
)

KT = TypeVar("KT")  # Identifier.
RT = TypeVar("RT")  # Requirement.
CT = TypeVar("CT")  # Candidate.
_T = TypeVar("_T")

Matches = Union[Iterable[CT], Callable[[], Iterable[CT]]]

class IteratorMapping(Mapping[KT, _T], metaclass=ABCMeta):
    pass

class IterableView(Container[CT], Iterable[CT], metaclass=ABCMeta):
    pass

class DirectedGraph(Generic[KT]):
    def __iter__(self) -> Iterator[KT]: ...
    def __len__(self) -> int: ...
    def __contains__(self, key: KT) -> bool: ...
    def copy(self) -> "DirectedGraph[KT]": ...
    def add(self, key: KT) -> None: ...
    def remove(self, key: KT) -> None: ...
    def connected(self, f: KT, t: KT) -> bool: ...
    def connect(self, f: KT, t: KT) -> None: ...
    def iter_edges(self) -> Iterable[Tuple[KT, KT]]: ...
    def iter_children(self, key: KT) -> Iterable[KT]: ...
    def iter_parents(self, key: KT) -> Iterable[KT]: ...

def build_iter_view(matches: Matches) -> IterableView[CT]: ...
