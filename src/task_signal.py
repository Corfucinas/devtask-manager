"""Signal/slot mechanism for decoupled updates."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Connection:
    """A single slot connected to a signal."""
    id: int
    signal: str
    slot: Callable
    active: bool = True
    call_count: int = 0
    last_error: Optional[str] = None


class SignalHub:
    """In-process publish/subscribe hub."""
    def __init__(self):
        self._connections: Dict[int, Connection] = {}
        self._by_signal: Dict[str, List[int]] = {}
        self._next_id = 1

    def connect(self, signal: str, slot: Callable) -> Connection:
        conn = Connection(id=self._next_id, signal=signal, slot=slot)
        self._connections[self._next_id] = conn
        self._by_signal.setdefault(signal, []).append(self._next_id)
        self._next_id += 1
        return conn

    def disconnect(self, conn_id: int) -> bool:
        if conn_id not in self._connections:
            return False
        conn = self._connections.pop(conn_id)
        ids = self._by_signal.get(conn.signal, [])
        if conn_id in ids:
            ids.remove(conn_id)
        return True

    def disconnect_signal(self, signal: str) -> int:
        ids = list(self._by_signal.get(signal, []))
        for cid in ids:
            self._connections.pop(cid, None)
        self._by_signal[signal] = []
        return len(ids)

    def emit(self, signal: str, *args, **kwargs) -> List[Dict]:
        results = []
        for cid in list(self._by_signal.get(signal, [])):
            conn = self._connections.get(cid)
            if not conn or not conn.active:
                continue
            try:
                res = conn.slot(*args, **kwargs)
                conn.call_count += 1
                results.append({"conn_id": cid, "result": res, "error": None})
            except Exception as e:
                conn.last_error = str(e)
                results.append({"conn_id": cid, "result": None, "error": str(e)})
        return results

    def connections_for(self, signal: str) -> List[Connection]:
        return [self._connections[cid] for cid in self._by_signal.get(signal, [])
                if cid in self._connections]

    def signals(self) -> List[str]:
        return sorted(self._by_signal.keys())

    def connection_count(self, signal: str = None) -> int:
        if signal:
            return len(self.connections_for(signal))
        return len(self._connections)

    def total_emissions(self) -> int:
        return sum(c.call_count for c in self._connections.values())

    def clear(self):
        self._connections.clear()
        self._by_signal.clear()


def signal_report(hub: SignalHub) -> Dict:
    return {"signals": hub.signals(),
            "total_connections": hub.connection_count(),
            "total_emissions": hub.total_emissions(),
            "per_signal": {s: hub.connection_count(s) for s in hub.signals()}}
