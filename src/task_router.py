"""Task router for dispatching to handlers."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Route:
    """A route from task type to handler."""
    id: int
    name: str
    handler: Callable
    filter_fn: Optional[Callable] = None
    priority: int = 0
    enabled: bool = True
    dispatched_count: int = 0
    error_count: int = 0

    def matches(self, task) -> bool:
        """Check if a task matches this route."""
        if not self.enabled:
            return False
        if self.filter_fn:
            try:
                return self.filter_fn(task)
            except Exception:
                return False
        return True

    def dispatch(self, task):
        """Dispatch a task to this handler."""
        try:
            result = self.handler(task)
            self.dispatched_count += 1
            return {"dispatched": True, "result": result, "route": self.name}
        except Exception as e:
            self.error_count += 1
            return {"dispatched": False, "error": str(e), "route": self.name}


class TaskRouter:
    """Routes tasks to appropriate handlers."""
    def __init__(self):
        self._routes: Dict[int, Route] = {}
        self._next_id = 1
        self._history: List[Dict] = []

    def add_route(self, name: str, handler: Callable, filter_fn: Callable = None,
                  priority: int = 0) -> Route:
        route = Route(id=self._next_id, name=name, handler=handler,
                       filter_fn=filter_fn, priority=priority)
        self._routes[self._next_id] = route
        self._next_id += 1
        return route

    def remove_route(self, route_id: int) -> bool:
        if route_id in self._routes:
            del self._routes[route_id]
            return True
        return False

    def get_route(self, route_id: int) -> Optional[Route]:
        return self._routes.get(route_id)

    def all_routes(self) -> List[Route]:
        return sorted(self._routes.values(), key=lambda r: -r.priority)

    def enabled_routes(self) -> List[Route]:
        return [r for r in self.all_routes() if r.enabled]

    def route_count(self) -> int:
        return len(self._routes)

    def dispatch(self, task) -> Dict:
        """Dispatch a task to the first matching route."""
        for route in self.all_routes():
            if route.matches(task):
                result = route.dispatch(task)
                self._history.append({
                    "route_id": route.id, "route_name": route.name,
                    "task_id": getattr(task, "id", None), **result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return result
        return {"dispatched": False, "error": "No matching route"}

    def dispatch_all(self, task) -> List[Dict]:
        """Dispatch to all matching routes."""
        results = []
        for route in self.all_routes():
            if route.matches(task):
                result = route.dispatch(task)
                results.append(result)
                self._history.append({
                    "route_id": route.id, "route_name": route.name,
                    "task_id": getattr(task, "id", None), **result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
        return results

    def enable_route(self, route_id: int) -> bool:
        if route_id in self._routes:
            self._routes[route_id].enabled = True
            return True
        return False

    def disable_route(self, route_id: int) -> bool:
        if route_id in self._routes:
            self._routes[route_id].enabled = False
            return True
        return False

    def clear_history(self):
        self._history = []

    def history(self) -> List[Dict]:
        return list(self._history)

    def dispatch_count(self) -> int:
        return len(self._history)


def routing_stats(router: TaskRouter) -> Dict:
    """Generate routing statistics."""
    return {
        "total_routes": router.route_count(),
        "total_dispatches": router.dispatch_count(),
        "by_route": {
            r.name: {"dispatched": r.dispatched_count, "errors": r.error_count,
                      "enabled": r.enabled}
            for r in router.all_routes()
        },
        "error_rate": round(
            sum(r.error_count for r in router.all_routes()) /
            max(sum(r.dispatched_count + r.error_count for r in router.all_routes()), 1) * 100, 1),
    }


def default_router() -> TaskRouter:
    """Create a router with default routes."""
    r = TaskRouter()
    r.add_route("default", lambda t: {"handled": "default"}, priority=0)
    return r
