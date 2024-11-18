import argparse
from contextlib import chdir, contextmanager
from functools import lru_cache
import os
from subprocess import run, call
import sys

from rich.console import Console
from rich.table import Table
from rich.theme import Theme

from .config import load_rack_config
from .output import VerbosityLogger, msgout_v

logger = VerbosityLogger.getLogger(__name__)


@contextmanager
def error_recovery(debug: bool = False):
    must_exit = False

    def error(msg: str, exception: Exception = None):
        nonlocal must_exit
        logger.error(msg)
        if exception:
            logger.exception(exception)
        if debug:
            must_exit = True

    yield error

    if must_exit:
        sys.exit(1)


@lru_cache
def git_status_files(repo_path, show_untracked=False, debug=False):
    """Return a list of (status_char, file_path)"""

    return_dir = os.path.abspath(os.getcwd())
    os.chdir(repo_path)
    try:
        msgout_v(f"Checking git status and diff: {repo_path}")
        result = run(["git", "status", "--porcelain"], capture_output=True)
        diff_stat_out = run(["git", "diff", "--stat"], capture_output=True)
        diff_stat: dict[str, int] = {}
        if diff_stat_out.returncode == 0:
            diff_output = diff_stat_out.stdout.decode("utf-8")
            for line in diff_output.splitlines():
                if "|" not in line:
                    continue
                try:
                    file_path, changes = line.split("|")
                except ValueError:
                    continue
                with error_recovery(debug=debug) as recover:
                    line_status = changes.strip().split(" ")[0]
                    if line_status.lower().startswith("bin"):
                        # diff output for binary files is like this:
                        #   file | Bin 100 -> 200 bytes
                        # So calculate the difference in bytes
                        try:
                            _, old_size, _, new_size, _ = changes.strip().split(" ")
                            lc = int(new_size) - int(old_size)
                        except ValueError as e:
                            if not recover(
                                f"Error parsing diff stat line: {line!r}", e
                            ):
                                print("Failing diff status output:")
                                print(diff_output)
                                print("END OF DIFF STATUS OUTPUT")
                            lc = float("NaN")
                        diff_stat[file_path.strip()] = lc
                        continue
                    else:
                        try:
                            lc = int(line_status)
                        except ValueError as e:
                            if not recover(
                                f"Error parsing diff stat line: {line!r}", e
                            ):
                                print("Failing diff status output:")
                                print(diff_output)
                                print("END OF DIFF STATUS OUTPUT")
                            lc = float("NaN")
                diff_stat[file_path.strip()] = lc
    finally:
        os.chdir(return_dir)

    if result.returncode != 0:
        print(f"git status failed for {repo_path}")
        return []

    lines = result.stdout.decode("utf-8").splitlines()
    status_filenames = [line.strip().split(" ", 1) for line in lines]
    return [
        (
            "U" if status == "??" else status,
            file_path,
            diff_stat.get(file_path, 0),
        )
        for status, file_path in status_filenames
        if show_untracked or status != "??"
    ]


@lru_cache
def git_diff(repo_path):
    """Return diff of all uncommited changed files in the repo.

    Takes output like this from git-diff:
        diff --git a/setup.py b/setup.py
        index 21d76d2..44df869 100644
        --- a/setup.py
        +++ b/setup.py
        @@ -13,7 +13,7 @@ with open(os.path.join(_project_root, 'README.md'), encoding='utf-8') as f:

        setup(
            name='orionutils',
        -    version='0.1.5',
        +    version='0.1.7',
            author='Red Hat PEAQE Team',
            # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
            classifiers=[
        @@ -45,6 +45,7 @@ setup(
            ],
            license='Apache',
            long_description=long_description,
        +    long_description_content_type="text/markdown",
            packages=find_packages(include=['orionutils*']),
            include_package_data=True,
            url='https://github.com/peaqe/orion-utils/',

    And parses out the filenames involved and the changed files, + or -,
    from that files diff.

    Returns {
        file_path: [
            ("+"|"-"|"@", diff_line),
            ...
        ],
    }
    """

    # change dir to repo_path
    with chdir(repo_path):
        result = run(["git", "diff"], capture_output=True)
        if result.returncode != 0:
            print(f"git diff failed for {repo_path}")
            return []
        file_diffs = {}
        current_file = None
        for line in result.stdout.decode("utf-8").splitlines():
            if line.startswith("diff --git"):
                current_file = line.split(" ", 3)[2]
                file_diffs[current_file] = []
            elif line.startswith("@@"):
                file_diffs[current_file].append(("@", line.split(" ", 1)[1].strip()))
            elif line.startswith("+ "):
                file_diffs[current_file].append(("+", line.split(" ", 1)[1].strip()))
            elif line.startswith("- "):
                file_diffs[current_file].append(("-", line.split(" ", 1)[1].strip()))
        return file_diffs


@lru_cache
def get_list_remotes(repo_path):
    """Get list of remotes for repo"""
    os.chdir(repo_path)
    result = run(["git", "remote"], capture_output=True)
    if result.returncode != 0:
        print(f"git remote failed for {repo_path}")
        return []
    return result.stdout.decode("utf-8").splitlines()


def git_reset(repo_path):
    """Reset repo to HEAD"""
    os.chdir(repo_path)
    result = run(["git", "reset", "--hard", "HEAD"], capture_output=True)
    if result.returncode != 0:
        print(f"git reset failed for {repo_path}")
        return False
    return True


def git_pull(repo_path):
    """Pull repo"""
    os.chdir(repo_path)
    result = run(["git", "pull"], capture_output=True)
    if result.returncode != 0:
        print(f"git pull failed for {repo_path}")
        return False
    return True


def git_push(repo_path):
    """Push repo"""
    os.chdir(repo_path)
    result = run(["git", "push"], capture_output=True)
    if result.returncode != 0:
        print(f"git push failed for {repo_path}")
        return False
    return True


ACTIONS = [
    "list",
    "status",
    "pull",
    "push",
    "diff",
    "reset",
    "branch",
]

parser = argparse.ArgumentParser()
# parser.add_argument(
#     "action",
#     help="action to perform",
#     choices=ACTIONS,
#     default="list",
#     action="store",
#     nargs="?",
# )

parser.add_argument(
    "-u",
    "--show-untracked",
    help="show untracked files",
    action="store_true",
)
parser.add_argument(
    "-d",
    "--working-dir",
    help="working directory",
    default=os.getcwd(),
    required=False,
    nargs="?",  # 0 or 1
)
parser.add_argument(
    "-r",
    "--repo",
    help="repo(s) to check",
    required=False,
    nargs="*",  # 0 or more
)
parser.add_argument(
    "-C",
    "--changed",
    help="focus only on repos with changes",
    action="store_true",
)
parser.add_argument(
    "-n",
    "--next",
    help="focus only on the next repo with changes",
    action="store_true",
)
# All -v -vv -vvv etc to calculate verbosity level
parser.add_argument(
    "-v",
    "--verbose",
    help="show more output",
    action="count",
    default=0,
    required=False,
    dest="verbosity",
)
parser.add_argument(
    "-D",
    "--die-and-debug",
    dest="debug",
    help="show debug output and exit at error",
    action="store_true",
    required=False,
)

subparsers = parser.add_subparsers(help="sub-command help", dest="action")

# Subparser for 'list' command
list_parser = subparsers.add_parser("list", help="list repos")
list_parser.add_argument(
    "-s",
    "--status",
    help="show status of repos",
    action="store_true",
)
list_parser.add_argument(
    "-u",
    "--show-untracked",
    help="show untracked files",
    action="store_true",
)
list_parser.add_argument(
    "-R",
    "--show-remotes",
    help="show remotes",
    action="store_true",
)
list_parser.add_argument(
    "-N",
    "--non-repos",
    help="show non-repos",
    action="store_true",
    dest="non_repos",
)
list_parser.add_argument(
    "-O",
    "--only-non-repos",
    help="show only non-repos",
    action="store_true",
    dest="non_repos_only",
)

# subparser for 'status' command
status_parser = subparsers.add_parser("status", help="status sub-command")

# subparser for 'pull' command
pull_parser = subparsers.add_parser("pull", help="pull sub-command")

# subparser for 'push' command
push_parser = subparsers.add_parser("push", help="push sub-command")

# subparser for 'diff' command
diff_parser = subparsers.add_parser("diff", help="diff sub-command")

# subparser for 'reset' command
reset_parser = subparsers.add_parser("reset", help="reset sub-command")

# subparser for 'branch' command
branch_parser = subparsers.add_parser("branch", help="branch sub-command")


def main(argv=None):
    argv = argv or sys.argv[1:]
    ns = parser.parse_args(argv)

    # Prepare logging and other pre-work setup steps
    logger.setVerbosity(ns.verbosity)

    os.chdir(ns.working_dir)
    rack_config = load_rack_config(ns.working_dir)

    if ns.next and ns.repo:
        print("Cannot specify both --next and --repo")
        return 1

    if ns.repo:
        repos = ns.repo
    elif "repos" in rack_config:
        repos = rack_config["repos"]
    else:
        # If not told explicitly, then find all the repos that exist in the
        # current working directory.
        repos = [
            repo
            for repo in os.listdir(ns.working_dir)
            if os.path.isdir(os.path.join(ns.working_dir, repo))
            and ".git" in os.listdir(os.path.join(ns.working_dir, repo))
        ]

    if ns.changed:
        repos = [
            repo
            for repo in repos
            if git_status_files(
                os.path.join(ns.working_dir, repo), ns.show_untracked, debug=ns.debug
            )
        ]

    if ns.next:
        for repo in repos:
            repo_path = os.path.join(os.environ["HOME"], "projects", repo)
            files = git_status_files(repo_path, ns.show_untracked, debug=ns.debug)
            if files:
                repos = [repo]
                break

    match ns.action:
        case "list":
            if ns.non_repos_only and not ns.non_repos:
                logger.error(
                    "Cannot specify -O/--only-non-repos without -N/--non-repos"
                )
                return 1
            if ns.non_repos_only and ns.status:
                logger.error("Cannot specify -O/--only-non-repos with -s/--status")
                return 1
            if not ns.non_repos_only:
                directories = [*repos]
            else:
                directories = []
            if ns.non_repos:
                non_repos = [
                    repo
                    for repo in os.listdir(ns.working_dir)
                    if os.path.isdir(os.path.join(ns.working_dir, repo))
                    and ".git" not in os.listdir(os.path.join(ns.working_dir, repo))
                ]
                directories.extend(non_repos)
                directories.sort()

            custom_theme = Theme(
                {
                    "row-even": "on black",
                    "row-odd": "on #222222",
                }
            )
            console = Console(theme=custom_theme)
            table = Table(expand=False, show_header=False)
            columns = ["changes", "folder"]
            if ns.show_remotes:
                columns.append("remotes")
            for i, directory in enumerate(directories):
                row = {}
                directory_path = os.path.join(ns.working_dir, directory)
                if ns.show_remotes:
                    remotes = [
                        f"[bright_black]{r}[/]" if r == "origin" else f"{r}"
                        for r in get_list_remotes(directory_path)
                    ]
                    list_text = "\n".join(f"{r}" for r in remotes)
                    row["remotes"] = list_text
                if ns.status:
                    # Count the number of files with changes
                    files = git_status_files(
                        directory_path, ns.show_untracked, debug=ns.debug
                    )
                    changes = len(files)
                    row["changes"] = str(changes)
                    row["folder"] = directory
                else:
                    row["folder"] = directory
                row_values = [row.get(column, "") for column in columns]
                if i % 2 == 0:
                    style = "row-even"
                else:
                    style = "row-odd"
                table.add_row(*row_values, style=style)

            console.print(table)

        case "status":
            for repo in repos:
                repo_path = os.path.join(ns.working_dir, repo)
                files = git_status_files(repo_path, ns.show_untracked, debug=ns.debug)
                if not files:
                    continue

                print(f"Status for Repo: {repo}")
                for status, file_path, diff in files:
                    # print(f"! {status!r} - {file_path!r} - {diff!r}")
                    diff_str = f"±{diff:<4}" if diff else "    "
                    print(f"  {status} {diff_str}\t{file_path}")

        case "diff":
            for repo in repos:
                repo_path = os.path.join(ns.working_dir, repo)
                file_diffs = git_diff(repo_path)
                if not file_diffs:
                    if len(repos) == 1:
                        print(f"Repository {repo} has no changes.")
                else:
                    print(f"Status for Repo: {repo}")
                    for file_path, diff in file_diffs.items():
                        print(f"Diff for {file_path!r}")
                        for code, line in diff:
                            if code == "@":
                                print(f"  {line}")
                            else:
                                print(f"  {code}\t{line}")

        case "reset":
            for repo in repos:
                repo_path = os.path.join(ns.working_dir, repo)
                print(f"Resetting Repo: {repo}")
                git_reset(repo_path)

        case "pull":
            for repo in repos:
                repo_path = os.path.join(ns.working_dir, repo)
                print(f"Pulling Repo: {repo}")
                git_pull(repo_path)

        case "push":
            for repo in repos:
                repo_path = os.path.join(ns.working_dir, repo)
                print(f"Pushing Repo: {repo}")
                git_push(repo_path)

        case _:
            raise NotImplementedError(f"Action {ns.action!r} not implemented")
