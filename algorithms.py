"""커밋 사이를 찾아다니고, 목록을 정리하는 도구들입니다."""


def merge_sort(items, key):
    """목록을 반씩 나눈 뒤, 작은 것부터 합치는 병합 정렬입니다."""
    if len(items) <= 1:
        return list(items)

    middle = len(items) // 2
    left = merge_sort(items[:middle], key)
    right = merge_sort(items[middle:], key)
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        # 값이 같으면 왼쪽을 먼저 꺼내 원래 순서를 지킵니다.
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


def parent_first(commits):
    """부모가 모두 나온 커밋부터 꺼냅니다. 이것이 위상 정렬입니다."""
    remaining = {hash_: len(commit.parents) for hash_, commit in commits.items()}
    children = {hash_: [] for hash_ in commits}
    for hash_, commit in commits.items():
        for parent in commit.parents:
            children[parent].append(hash_)

    queue = [hash_ for hash_ in commits if remaining[hash_] == 0]
    result = []
    position = 0
    while position < len(queue):
        hash_ = queue[position]
        position += 1
        result.append(commits[hash_])
        for child in children[hash_]:
            remaining[child] -= 1
            if remaining[child] == 0:
                queue.append(child)
    return result


def shortest_path(commits, start, end):
    """가까운 이웃부터 살펴보는 BFS로 가장 짧은 길을 찾습니다."""
    neighbors = {hash_: [] for hash_ in commits}
    for hash_, commit in commits.items():
        for parent in commit.parents:
            # PATH에서는 부모와 자식 사이를 양쪽으로 갈 수 있습니다.
            neighbors[hash_].append(parent)
            neighbors[parent].append(hash_)

    queue = [start]
    previous = {start: None}
    position = 0
    while position < len(queue):
        current = queue[position]
        position += 1
        if current == end:
            path = []
            while current is not None:
                path.append(current)
                current = previous[current]
            return path[::-1]

        # 같은 길이라면 경로 문자열의 사전순으로 먼저 오는 길을 고릅니다.
        for neighbor in merge_sort(neighbors[current], key=lambda value: value + " → "):
            if neighbor not in previous:
                previous[neighbor] = current
                queue.append(neighbor)
    return []


def find_ancestors(commits, start):
    """부모 방향으로만 올라갑니다. 이미 만난 조상은 다시 세지 않습니다."""
    stack = list(commits[start].parents)
    visited = set()
    result = []
    while stack:
        hash_ = stack.pop()
        if hash_ in visited:
            continue
        visited.add(hash_)
        result.append(commits[hash_])
        stack.extend(commits[hash_].parents)
    return result
