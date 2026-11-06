"""Limiteur en mémoire (fenêtre glissante) — protège la génération et la force brute sur le jeton admin."""
import threading
import time
from collections import defaultdict, deque


class Limiter:
    def __init__(self, maxi: int, window: float):
        self.max, self.window = maxi, window
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def _trim(self, key, now):
        q = self._hits[key]
        while q and q[0] <= now - self.window:
            q.popleft()
        if not q:
            self._hits.pop(key, None)
        return self._hits.get(key)

    def blocked(self, key) -> bool:
        with self._lock:
            q = self._trim(key, time.monotonic())
            return bool(q) and len(q) >= self.max

    def add(self, key) -> None:
        with self._lock:
            self._hits[key].append(time.monotonic())

    def allow(self, key) -> bool:
        """Compte l'appel et retourne False si le quota est dépassé."""
        with self._lock:
            now = time.monotonic()
            q = self._trim(key, now)
            if q and len(q) >= self.max:
                return False
            self._hits[key].append(now)
            return True
