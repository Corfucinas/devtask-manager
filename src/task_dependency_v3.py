"""Dependency layering for parallel execution planning."""
from collections import defaultdict
from typing import Dict, List, Optional, Set


class DependencyLayers:
    """Groups tasks into layers by dependency depth."""
    def __init__(self):
        self._deps: Dict[int, Set[int]] = defaultdict(set)
        self._reverse: Dict[int, Set[int]] = defaultdict(set)
        self._nodes: Set[int] = set()

    def add(self, task_id: int, depends_on: int):
        """task_id depends on depends_on."""
        self._nodes.add(task_id)
        self._nodes.add(depends_on)
        self._deps[task_id].add(depends_on)
        self._reverse[depends_on].add(task_id)

    def add_node(self, task_id: int):
        self._nodes.add(task_id)

    def dependencies_of(self, task_id: int) -> List[int]:
        return sorted(self._deps.get(task_id, set()))

    def dependents_of(self, task_id: int) -> List[int]:
        return sorted(self._reverse.get(task_id, set()))

    def node_count(self) -> int:
        return len(self._nodes)

    def layers(self) -> List[List[int]]:
        """Compute execution layers: layer 0 = no deps."""
        remaining_deps = {n: len(self._deps.get(n, set())) for n in self._nodes}
        result: List[List[int]] = []
        placed: Set[int] = set()
        while len(placed) < len(self._nodes):
            layer = sorted(n for n in self._nodes
                           if n not in placed and remaining_deps[n] == 0)
            if not layer:
                break  # cycle
            result.append(layer)
            for n in layer:
                placed.add(n)
                for dep in self._reverse.get(n, set()):
                    remaining_deps[dep] -= 1
        return result

    def depth_of(self, task_id: int) -> Optional[int]:
        for i, layer in enumerate(self.layers()):
            if task_id in layer:
                return i
        return None

    def max_parallelism(self) -> int:
        layers = self.layers()
        return max((len(l) for l in layers), default=0)

    def critical_layer(self) -> Optional[List[int]]:
        layers = self.layers()
        return layers[-1] if layers else None

    def has_cycle(self) -> bool:
        layers = self.layers()
        counted = sum(len(l) for l in layers)
        return counted < len(self._nodes)

    def layer_count(self) -> int:
        return len(self.layers())


def layer_stats(dl: DependencyLayers) -> Dict:
    layers = dl.layers()
    return {"total_nodes": dl.node_count(),
            "layer_count": len(layers),
            "max_parallelism": dl.max_parallelism(),
            "has_cycle": dl.has_cycle(),
            "layers": [{"depth": i, "size": len(l), "tasks": l}
                       for i, l in enumerate(layers)]}
