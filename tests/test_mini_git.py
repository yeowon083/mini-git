"""작은 예시로 미션의 중요한 약속들을 확인합니다."""

from contextlib import redirect_stdout
from datetime import datetime, timezone
from io import StringIO
import unittest

from algorithms import find_ancestors, merge_sort, parent_first, shortest_path
from main import execute, main
from repository import Commit, Repository
from unittest.mock import patch


class MiniGitTests(unittest.TestCase):
    def test_branch_history_and_search(self):
        repo = Repository("김 민수")
        root = repo.commit("Start")
        repo.branch("feature")
        repo.switch("feature")
        feature = repo.commit("Add LOGIN login feature")
        repo.switch("main")
        payment = repo.commit("Add payment feature")
        self.assertEqual(feature.parents, (root.hash,))
        self.assertEqual(payment.parents, (root.hash,))
        self.assertEqual(repo.branches["feature"], feature.hash)
        self.assertEqual(repo.path(feature.hash, payment.hash),
                         [feature.hash, root.hash, payment.hash])
        self.assertEqual(repo.search("login"), [feature])
        self.assertEqual(repo.search("LOGIN feature"), [feature])
        self.assertEqual(repo.search("log"), [])
        self.assertEqual(repo.search("missing"), [])
        self.assertEqual(repo.search_author("김 민수"), [root, feature, payment])
        self.assertEqual(repo.search_author("다른 사람"), [])

    def test_disconnected_roots_and_empty_repository(self):
        repo = Repository("Alice")
        self.assertEqual(repo.log(), [])
        repo.branch("other")
        first = repo.commit("First")
        repo.switch("other")
        second = repo.commit("Second")
        self.assertEqual(repo.path(first.hash, second.hash), [])
        self.assertEqual(repo.path(first.hash, first.hash), [first.hash])
        self.assertEqual(repo.ancestors(first.hash), [])
        self.assertNotEqual(first.hash, second.hash)

    def test_multiple_parents_and_path_tie(self):
        # 일부러 자식을 먼저 넣어도 부모 우선 로그가 나와야 합니다.
        now = datetime.now(timezone.utc)
        commits = {
            "d": Commit("d", "Merge", "Zoe", now, ("c", "b")),
            "c": Commit("c", "Right", "Alice", now, ("a",)),
            "b": Commit("b", "Left", "Alice", now, ("a",)),
            "a": Commit("a", "Root", "Zoe", now, ()),
        }
        order = [commit.hash for commit in parent_first(commits)]
        for commit in commits.values():
            for parent in commit.parents:
                self.assertLess(order.index(parent), order.index(commit.hash))
        self.assertEqual(shortest_path(commits, "a", "d"), ["a", "b", "d"])
        self.assertEqual(shortest_path(commits, "d", "a"), ["d", "b", "a"])
        ancestors = find_ancestors(commits, "d")
        self.assertEqual({c.hash for c in ancestors}, {"a", "b", "c"})
        self.assertEqual(len(ancestors), 3)

    def test_merge_sort_is_stable_and_does_not_change_input(self):
        items = [(2, "first"), (1, "second"), (2, "third"), (0, "last")]
        self.assertEqual(merge_sort(items, key=lambda item: item[0]),
                         [(0, "last"), (1, "second"), (2, "first"), (2, "third")])
        self.assertEqual(items[0], (2, "first"))
        self.assertEqual(merge_sort([], key=lambda item: item), [])

    def test_log_sort_criteria(self):
        repo = Repository("Alice")
        early = datetime(2020, 1, 1, tzinfo=timezone.utc)
        late = datetime(2021, 1, 1, tzinfo=timezone.utc)
        repo.commits = {
            "a": Commit("a", "One", "Zoe", late, ()),
            "b": Commit("b", "Two", "Alice", early, ("a",)),
            "c": Commit("c", "Three", "Alice", early, ("b",)),
        }
        for criterion in ("date", "author"):
            self.assertEqual([c.hash for c in repo.log(criterion)], ["b", "c", "a"])

    def test_cli_quotes_options_and_errors(self):
        output = StringIO()
        with redirect_stdout(output):
            repo, running = execute(None, 'iNiT "Alice Kim"')
            execute(repo, 'commit "Add login feature"')
            execute(repo, 'search --author="Alice Kim"')
            execute(repo, 'search "login feature"')
            execute(repo, 'log --sort-by=date')
            execute(repo, 'log --sort-by=author')
            self.assertTrue(running)
            self.assertFalse(execute(repo, "QUIT")[1])
        self.assertIn("Alice Kim", output.getvalue())
        for command in ('commit', 'commit ""', 'commit "broken', 'log extra',
                        'search --author=', 'search --bad=x', 'path one', 'exit extra'):
            with self.subTest(command=command):
                with self.assertRaisesRegex(ValueError, "Invalid args"):
                    execute(repo, command)
        for command, error in (
            ("switch missing", "Unknown branch"),
            ("branch main", "Branch already exists"),
            ("ancestors missing", "Unknown commit"),
            ("path missing 00000001", "Unknown commit"),
            ("init Bob", "already initialized"),
            ("hello", "Unknown command"),
        ):
            with self.subTest(command=command):
                with self.assertRaisesRegex(ValueError, error):
                    execute(repo, command)
        with self.assertRaisesRegex(ValueError, "Run INIT first"):
            execute(None, "log")

    def test_repl_continues_after_error(self):
        output = StringIO()
        with patch("builtins.input", side_effect=["log", "init Alice", "commit One", "quit"]):
            with redirect_stdout(output):
                main()
        self.assertIn("Run INIT first", output.getvalue())
        self.assertIn("[main 00000001] One", output.getvalue())


if __name__ == "__main__":
    unittest.main()
