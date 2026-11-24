"""python main.py로 실행하면 명령어를 하나씩 입력할 수 있습니다."""

import shlex

from repository import Repository


def print_commits(commits):
    """기록 카드들을 같은 모양으로 보여 줍니다."""
    if not commits:
        print("No commits")
    for commit in commits:
        print(f"commit {commit.hash} ({commit.author}, {commit.timestamp.isoformat()})")
        print(f"  {commit.message}")


def execute(repository, line):
    """입력 한 줄을 처리하고, 저장소와 계속 실행할지를 돌려줍니다."""
    try:
        # 따옴표 안의 공백은 한 인자의 일부로 남겨 둡니다.
        parts = shlex.split(line)
    except ValueError:
        raise ValueError("Invalid args") from None
    if not parts:
        return repository, True

    command = parts[0].upper()
    args = parts[1:]
    counts = {
        "INIT": (1,), "BRANCH": (1,), "SWITCH": (1,), "COMMIT": (1,),
        "LOG": (0, 1), "PATH": (2,), "ANCESTORS": (1,), "SEARCH": (1,),
        "EXIT": (0,), "QUIT": (0,),
    }
    if command not in counts:
        raise ValueError(f"Unknown command: {parts[0]}")
    if len(args) not in counts[command] or any(not arg.strip() for arg in args):
        raise ValueError("Invalid args")

    if command in ("EXIT", "QUIT"):
        return repository, False
    if command == "INIT":
        if repository is not None:
            raise ValueError("Repository already initialized")
        repository = Repository(args[0])
        print(f"Initialized repository.\nCurrent branch: main\nCurrent user: {args[0]}")
        return repository, True
    if repository is None:
        raise ValueError("Run INIT first")

    if command == "BRANCH":
        repository.branch(args[0])
        print(f"Created branch: {args[0]}")
    elif command == "SWITCH":
        repository.switch(args[0])
        print(f"Switched to branch: {args[0]}")
    elif command == "COMMIT":
        commit = repository.commit(args[0])
        print(f"[{repository.head} {commit.hash}] {commit.message}")
    elif command == "LOG":
        sort_by = None
        if args:
            if args[0] not in ("--sort-by=date", "--sort-by=author"):
                raise ValueError("Invalid args")
            sort_by = args[0].split("=", 1)[1]
        print_commits(repository.log(sort_by))
    elif command == "PATH":
        path = repository.path(*args)
        print("Path: " + " → ".join(path) if path else "No path")
    elif command == "ANCESTORS":
        print_commits(repository.ancestors(args[0]))
    elif command == "SEARCH":
        query = args[0]
        if query.startswith("--author="):
            author = query.split("=", 1)[1]
            if not author.strip():
                raise ValueError("Invalid args")
            print_commits(repository.search_author(author))
        elif query.startswith("--"):
            raise ValueError("Invalid args")
        else:
            print_commits(repository.search(query))
    return repository, True


def main():
    """입력 → 실행 → 출력 순서를 종료 명령이 올 때까지 반복합니다."""
    repository = None
    print('Mini Git: INIT "사용자 이름"으로 시작하세요. 종료: exit 또는 quit')
    while True:
        try:
            line = input("mini-git> ")
            repository, running = execute(repository, line)
            if not running:
                break
        except ValueError as error:
            # 잘못 입력해도 프로그램은 꺼지지 않습니다.
            print(error)
        except (EOFError, KeyboardInterrupt):
            print()
            break


if __name__ == "__main__":
    main()
