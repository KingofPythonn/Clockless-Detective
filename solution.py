"""Reference solution for «کارآگاه بی‌ساعت» (Fault Diagnosability).

Input:  one JSON object on stdin.
Output: one JSON object on stdout.

The core idea is a verifier/product graph: its vertices (p, q, b) pair
an arbitrary execution with a fault-free one.  The bit b remembers whether
the first execution has already experienced a fault.  Observed transitions
are synchronized; invisible transitions may occur on either side alone.
Each synchronized observable step has weight b; all other steps have weight 0.

A reachable positive-weight cycle proves an unbounded delay.  Otherwise,
the weighted longest path in the graph's SCC condensation gives the exact
maximum delay.  Actual machine-transition certificates are reconstructed
for both cases.

Time:  O((|alphabet| + 1) * n**2) under the assignment's out-degree limits.
Space: O((|alphabet| + 1) * n**2).
"""

from __future__ import annotations

from array import array
from collections import deque
import json
import sys


def analyze(model: dict) -> dict:
    """Return the correct status, exact bound (if finite), and certificates.

    Does not mutate *model*.  The input is assumed valid as specified by the
    assignment.  A certificate contains zero-based indices into model['edges'].
    """
    n = model["n"]
    start = model["start"]
    alphabet = model["alphabet"]
    symbol_index = {symbol: i for i, symbol in enumerate(alphabet)}
    alphabet_size = len(alphabet)

    # Original transitions, indexed by source state and observable symbol.
    visible = [[[] for _ in range(alphabet_size)] for _ in range(n)]
    silent = [[] for _ in range(n)]
    faults = [[] for _ in range(n)]

    for eid, (u, label, v) in enumerate(model["edges"]):
        if label == "tau":
            silent[u].append((v, eid))
        elif label == "fault":
            faults[u].append((v, eid))
        else:
            visible[u][symbol_index[label]].append((v, eid))

    square = n * n
    vertex_count = 2 * square
    root = start * n + start  # (start, start, 0)

    # Product graph. Edge data is packed into arrays for reasonable memory
    # use when the input has the maximum 80 states and 6 visible symbols.
    forward: list[list[int]] = [[] for _ in range(vertex_count)]
    backward: list[list[int]] = [[] for _ in range(vertex_count)]
    edge_source = array("I")
    edge_target = array("I")
    edge_left = array("i")   # -1 means no left-side transition
    edge_right = array("i")  # -1 means no right-side transition
    edge_weight = bytearray()

    # Discovery parents also provide short paths from root to every vertex.
    discovery_parent = [-1] * vertex_count
    discovery_parent[root] = -2
    queue = deque([root])
    reached: list[int] = []

    def add_edge(u: int, v: int, left: int, right: int, weight: int) -> None:
        idx = len(edge_source)
        edge_source.append(u)
        edge_target.append(v)
        edge_left.append(left)
        edge_right.append(right)
        edge_weight.append(weight)
        forward[u].append(idx)
        backward[v].append(idx)
        if discovery_parent[v] == -1:
            discovery_parent[v] = idx
            queue.append(v)

    while queue:
        u = queue.popleft()
        reached.append(u)
        b, rem = divmod(u, square)
        p, q = divmod(rem, n)
        layer = b * square

        # Invisible left steps (including a possible first or repeated fault).
        for p_next, left_id in silent[p]:
            add_edge(u, layer + p_next * n + q, left_id, -1, 0)
        for p_next, left_id in faults[p]:
            add_edge(u, square + p_next * n + q, left_id, -1, 0)

        # Invisible right steps; this execution is NEVER permitted a fault.
        for q_next, right_id in silent[q]:
            add_edge(u, layer + p * n + q_next, -1, right_id, 0)

        # A visible event advances both executions with the same label.
        # It counts towards the delay only AFTER the first left-side fault.
        for p_moves, q_moves in zip(visible[p], visible[q]):
            for p_next, left_id in p_moves:
                left_base = layer + p_next * n
                for q_next, right_id in q_moves:
                    add_edge(u, left_base + q_next, left_id, right_id, b)

    if not any(u >= square for u in reached):
        return {"status": "unreachable"}

    # Kosaraju's SCC algorithm.  The first DFS is iterative to avoid Python's
    # recursion limit on long graph paths.
    visited = bytearray(vertex_count)
    finish_order: list[int] = []
    for root_dfs in reached:
        if visited[root_dfs]:
            continue
        visited[root_dfs] = 1
        dfs_stack = [(root_dfs, 0)]
        while dfs_stack:
            u, next_idx = dfs_stack[-1]
            if next_idx == len(forward[u]):
                finish_order.append(u)
                dfs_stack.pop()
                continue
            dfs_stack[-1] = (u, next_idx + 1)
            v = edge_target[forward[u][next_idx]]
            if not visited[v]:
                visited[v] = 1
                dfs_stack.append((v, 0))

    component = [-1] * vertex_count
    members: list[list[int]] = []
    for root_dfs in reversed(finish_order):
        if component[root_dfs] != -1:
            continue
        cid = len(members)
        group: list[int] = []
        component[root_dfs] = cid
        stack = [root_dfs]
        while stack:
            u = stack.pop()
            group.append(u)
            for eid in backward[u]:
                v = edge_source[eid]
                if component[v] == -1:
                    component[v] = cid
                    stack.append(v)
        members.append(group)

    def within_component_path(begin: int, end: int) -> list[int]:
        """Return a path of product-edge IDs within a single SCC."""
        if begin == end:
            return []
        cid = component[begin]
        local_parent = {begin: -1}
        pending = deque([begin])
        while pending and end not in local_parent:
            u = pending.popleft()
            for eid in forward[u]:
                v = edge_target[eid]
                if component[v] == cid and v not in local_parent:
                    local_parent[v] = eid
                    pending.append(v)
        if end not in local_parent:
            raise AssertionError("SCC connectivity invariant violated")
        path = []
        v = end
        while v != begin:
            eid = local_parent[v]
            path.append(eid)
            v = edge_source[eid]
        path.reverse()
        return path

    def original_routes(path: list[int]) -> dict:
        """Translate product edges to two original machine edge-ID lists."""
        faulty: list[int] = []
        healthy: list[int] = []
        for eid in path:
            left_id = edge_left[eid]
            right_id = edge_right[eid]
            if left_id >= 0:
                faulty.append(left_id)
            if right_id >= 0:
                healthy.append(right_id)
        return {"faulty": faulty, "healthy": healthy}

    # A positive internal SCC edge is equivalent to a reachable positive
    # cycle: its return path within the SCC closes a pumpable cycle.
    for eid, weight in enumerate(edge_weight):
        if weight and component[edge_source[eid]] == component[edge_target[eid]]:
            start_cycle = edge_source[eid]
            prefix_edges: list[int] = []
            u = start_cycle
            while u != root:
                parent_eid = discovery_parent[u]
                prefix_edges.append(parent_eid)
                u = edge_source[parent_eid]
            prefix_edges.reverse()

            cycle_edges = [eid]
            cycle_edges.extend(within_component_path(edge_target[eid], start_cycle))
            return {
                "status": "unbounded",
                "prefix": original_routes(prefix_edges),
                "cycle": original_routes(cycle_edges),
            }

    # No positive-weight cycle exists.  All edges *inside* each SCC have
    # weight zero, and the condensation graph is acyclic.
    count = len(members)
    indegree = [0] * count
    for eid in range(len(edge_source)):
        from_cid = component[edge_source[eid]]
        to_cid = component[edge_target[eid]]
        if from_cid != to_cid:
            indegree[to_cid] += 1

    # Longest path on the condensation DAG, via Kahn topological ordering.
    # Retain one optimal entering edge to reconstruct the full certificate.
    best = [-1] * count
    best[component[root]] = 0
    entering_edge = [-1] * count
    ready = deque(cid for cid, d in enumerate(indegree) if d == 0)

    while ready:
        cid = ready.popleft()
        for u in members[cid]:
            for eid in forward[u]:
                v_cid = component[edge_target[eid]]
                if v_cid == cid:
                    continue
                score = best[cid] + edge_weight[eid]
                if score > best[v_cid]:
                    best[v_cid] = score
                    entering_edge[v_cid] = eid
                indegree[v_cid] -= 1
                if indegree[v_cid] == 0:
                    ready.append(v_cid)

    # Strong connectivity never mixes b=0 and b=1, since b cannot decrease.
    # Pick the component with greatest observed delay after the first fault.
    winning_cid = max(
        (cid for cid, group in enumerate(members) if group[0] >= square),
        key=best.__getitem__,
    )
    bound = best[winning_cid]
    assert bound >= 0

    # Each entering edge crosses between distinct SCCs.  Reconnect adjacent
    # crossing edges by zero-weight paths inside the intermediate SCCs.
    crossings: list[int] = []
    current_cid = winning_cid
    start_cid = component[root]
    while current_cid != start_cid:
        eid = entering_edge[current_cid]
        if eid < 0:
            raise AssertionError("Missing predecessor of a reachable SCC")
        crossings.append(eid)
        current_cid = component[edge_source[eid]]
    crossings.reverse()

    product_path: list[int] = []
    current_node = root
    for eid in crossings:
        product_path.extend(within_component_path(current_node, edge_source[eid]))
        product_path.append(eid)
        current_node = edge_target[eid]

    return {
        "status": "bounded",
        "bound": bound,
        "witness": original_routes(product_path),
    }


def main() -> None:
    model = json.load(sys.stdin)
    json.dump(analyze(model), sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
