# Rack

Rack is a developer tool for managing all the different projects and repositories
you have on your computer. It's a command line tool that allows you to quickly
get overviews of the the state across repositories, find projects that aren't
setup with repos at all or aren't safely pushed somewhere, and perform cross-repo
operations like commits, branch changes, and more.

Rack is very much a work in progress, very much alpha, and has only been tested
on my machine. Everyone's setups are different, and I want Rack to work with
them all, so please file issues if you run into problems or even contribute if
you have the time and inclination.

## Installation

Simply install with pip. There is no packaging for now.

```shell
pip install .
```

## Usage

Rack is a command line tool. It has a few subcommands, but the main one is
`rack status`. This command will print out a table of all the repositories
it finds in the current directory. It will show the current branch, whether
there are uncommitted changes, and whether the repo is clean or not. It will
also show the status of the remote, if there is one.

```shell
$ rack status
+-----------------+--------------+--------------+----------------+
|      Repo       |     Branch   |     Remote   |  Changes       |
+-----------------+--------------+--------------+----------------+
| rack            | master       | origin       | +13            |
| my-app          | master       | origin       | +5/-305        |
+-----------------+--------------+--------------+----------------+
```

The full list of subcommands is:

- `list`    - Which lists details about all project folders, not just repos.
- `status`  - Which shows detailed, configurable status summaries across
                your repositories.
- `diff`    - Which shows in repositories that have changes.
- `reset`   - Which resets all repositories to the state of their remotes.
    one step.

    *(\*note: this works well with issue-based naming schemes)*

Planned:

- `pull`    - Which pulls from the remotes of all repositories.
- `push`    - Which pushes to the remotes of all repositories.
- `branch`  - Which shows and allows changing branches across repositories as
- `stash`   - Which stashes all repositories.
- `commit`  - Which allows committing across repositories as one step.

### Global Options

- `-u / --show-untracked`

    Show untracked files in the status output, which are hidden by default.

- `-d / --working-dir`

    Set the working directory to use. Defaults to the current directory.    This is where Rack will look for repositories.

- `-r / --repo`

    Manually specify one or more repositories to operate on.

- `-C / --changed`

    Filter the list of repositories to only those with changes.

- `-n / --next`

    Focus on the next repository with changes only.

