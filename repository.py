"""커밋과 브랜치를 메모리에 보관합니다. 종료하면 기록은 사라집니다."""

from dataclasses import dataclass
from datetime import datetime, timezone

from algorithms import find_ancestors, merge_sort, parent_first, shortest_path


@dataclass(frozen=True)
class Commit:
    """커밋은 누가, 언제, 무엇을 했는지 적은 작은 기록 카드입니다."""

    hash: str
    message: str
    author: str
    timestamp: datetime
    parents: tuple[str, ...]


class SearchIndex:
    """책 뒤의 찾아보기처럼, 단어와 작성자별로 커밋 번호를 모읍니다."""

    def __init__(self):
        self.keywords = {}
        self.authors = {}

    def add(self, commit):
        """새 카드가 생기면 찾아보기에도 번호를 적습니다."""
        # 같은 단어가 여러 번 나와도 커밋 번호는 한 번만 넣습니다.
        for word in set(commit.message.lower().split()):
            self.keywords.setdefault(word, []).append(commit.hash)
        self.authors.setdefault(commit.author, []).append(commit.hash)

    def search(self, commits, keyword):
        """첫 단어의 후보만 확인합니다. 여러 단어는 이어진 구절로 찾습니다."""
        words = keyword.lower().split()
        if not words:
            return []
        candidates = self.keywords.get(words[0], [])
        phrase = " ".join(words)
        result = []
        for hash_ in candidates:
            commit = commits[hash_]
            message = " ".join(commit.message.lower().split())
            # 양옆 공백은 'log'가 'login'에 잘못 맞는 일을 막습니다.
            if f" {phrase} " in f" {message} ":
                result.append(commit)
        return result


class Repository:
    """브랜치는 마지막 커밋의 번호, HEAD는 현재 브랜치의 이름입니다."""

    def __init__(self, author):
        self.author = author
        self.commits = {}
        self.branches = {"main": None}
        self.head = "main"
        self.index = SearchIndex()
        self.next_number = 1

    def branch(self, name):
        """현재 위치에 이름표를 하나 더 붙입니다. 커밋을 복사하지 않습니다."""
        if name in self.branches:
            raise ValueError(f"Branch already exists: {name}")
        self.branches[name] = self.branches[self.head]

    def switch(self, name):
        """앞으로 작업할 브랜치를 바꿉니다."""
        if name not in self.branches:
            raise ValueError(f"Unknown branch: {name}")
        self.head = name

    def commit(self, message):
        """현재 커밋 뒤에 새 카드를 붙이고, 현재 브랜치의 이름표를 옮깁니다."""
        parent = self.branches[self.head]
        # 번호를 하나씩 늘려 같은 저장소에서 중복되지 않게 합니다.
        hash_ = f"{self.next_number:08x}"
        self.next_number += 1
        commit = Commit(
            hash_, message, self.author, datetime.now(timezone.utc),
            () if parent is None else (parent,),
        )
        self.commits[hash_] = commit
        self.branches[self.head] = hash_
        self.index.add(commit)
        return commit

    def log(self, sort_by=None):
        """기본은 부모 먼저, 옵션을 주면 날짜나 작성자 오름차순입니다."""
        if sort_by is None:
            return parent_first(self.commits)
        if sort_by == "date":
            return merge_sort(list(self.commits.values()), key=lambda c: c.timestamp)
        if sort_by == "author":
            return merge_sort(list(self.commits.values()), key=lambda c: c.author)
        raise ValueError("Invalid args")

    def check_commit(self, hash_):
        """없는 커밋 번호라면 알아보기 쉬운 오류를 냅니다."""
        if hash_ not in self.commits:
            raise ValueError(f"Unknown commit: {hash_}")

    def path(self, start, end):
        """두 커밋이 있는지 확인한 뒤 길을 찾습니다."""
        self.check_commit(start)
        self.check_commit(end)
        return shortest_path(self.commits, start, end)

    def ancestors(self, hash_):
        """자기 자신을 제외한 모든 조상을 찾습니다."""
        self.check_commit(hash_)
        return find_ancestors(self.commits, hash_)

    def search(self, keyword):
        """메시지의 단어나 구절로 찾습니다."""
        return self.index.search(self.commits, keyword)

    def search_author(self, author):
        """작성자 이름은 대소문자를 포함해 정확하게 비교합니다."""
        return [self.commits[hash_] for hash_ in self.index.authors.get(author, [])]
