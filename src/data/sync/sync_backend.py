from abc import ABC, abstractmethod


class SyncBackend(ABC):
    """
    Abstrakte Schnittstelle für spätere Synchronisations-Backends (v1: Stub).

    Konfliktstrategie laut ARCHITECTURE.md 3.4: Last-Writer-Wins je Eintrag
    anhand edited_at; Soft-Deletes (Tombstones) gewinnen gegen Updates.
    """

    @abstractmethod
    def push(self) -> None:
        """Lokale Änderungen an das Backend übertragen."""

    @abstractmethod
    def pull(self) -> None:
        """Ferne Änderungen vom Backend übernehmen."""
