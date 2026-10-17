# 2026-10-17: CLI and File Discovery

The CLI (src/mdbed/cli.py) is a click group with a custom `DefaultCommandGroup`
that makes `embed` the default subcommand. Any first argument that is not a known
subcommand name and does not start with `-` gets `embed` inserted before it
(cli.py:18-35), so `mdbed foo.md` means `mdbed embed foo.md`. File discovery goes
through polars-ls (`pols.ls`) in `get_files` (utils.py:12-79). Running the CLI against
real inputs surfaced several divergences from its own help text, each small on its
own.

## `mdbed list` does not exist

The `list` command is defined as `def list_files(...)` with no explicit name
(cli.py:242). click derives command names from the function name, so it registers as
`list-files` (`mdbed --help` shows `embed` and `list-files`). The help text and
docstring examples say `mdbed list .` and `mdbed list file1.md file2.md`
(cli.py:223, 226). Because `list` is not a recognised subcommand, `DefaultCommandGroup`
rewrites `mdbed list .` into `mdbed embed list .`, which fails with
`Error: Invalid value for '[PATHS]...': Path 'list' does not exist.` Checked with
click 8.5.0, but click has used the function name with `_` → `-` for a long time, so
this has likely been broken since it was written.

## The `.md` filter does not work

`list-files` defaults to the filter `'{name}.str.ends_with(".md")'` (cli.py:253-254),
passed to `pols.ls(with_filter=...)`. With polars-ls 0.5.4 that raises
`ValueError: Filter '{name}.str.ends_with(".md")' failed, skipped`, so
`mdbed list-files .` crashes. The template syntax apparently does not match what
polars-ls 0.5.4 expects. The exact accepted syntax was not dug into.

## `embed` embeds everything

`embed` has no default filter (`filter_expr` defaults to `None`, cli.py:132), so it
processes every non-directory file it finds. Its help says "Embed markdown files"
and "Process markdown files in current directory: mdbed embed ." (cli.py:43-69). With
a `zz_notes.txt` dropped into `example/data/`, `mdbed embed .` reports "Found 5
files", processes `zz_notes.txt` through the markdown parser, and extracts 124 nodes
from 5 files. Plain text happens to parse as markdown paragraphs. Binary files or
large logs in a recursive scan would not be so benign.

## Directories outside the current working directory crash

`mdbed embed <dir>` where `<dir>` is not under the current working directory crashes
inside polars-ls: `pols/resegment.py: resegment_raw_path` calls
`raw_dir.relative_to(raw_top_dir.absolute())` and raises
`ValueError: '<dir>/notes.txt' is not in the subpath of '/home/user/mdbed'`. Explicit
file paths outside the cwd, and directories under the cwd (`cd example/data && mdbed
embed .`), both work. This looks like a polars-ls bug triggered by `as_path=True` /
`merge_all=True` (utils.py:37-45) rather than an mdbed bug, but mdbed is where it
surfaces.

## polars-ls prints to stdout

Each `get_files` call prints a polars-ls DataFrame (`path`, `name`, `is_dir`,
`source`) to **stdout**, in addition to returning it. The table still appears with
`2>/dev/null`, so it goes to file descriptor 1. Wrapping `get_files` in
`contextlib.redirect_stdout` captures nothing, so the print bypasses `sys.stdout`
(written to the original stream or the raw descriptor) and cannot be silenced from
Python by the usual redirect. mdbed deliberately sends all its
progress messages to stderr (`click.echo(..., err=True)` throughout cli.py) and
reserves stdout for the result table (cli.py:209). The polars-ls print contaminates
that, so `mdbed embed . > pairs.txt` would capture the file listing too. The `ls`
call passes no option to suppress printing (utils.py:37-45). Whether polars-ls 0.5.4
has one was not checked.

## Current State

- `DefaultCommandGroup.parse_args` inserts `embed` before the first argument when the argument is neither a registered subcommand nor an option (src/mdbed/cli.py:18-35)
- `mdbed --help` lists two subcommands: `embed` and `list-files` (src/mdbed/cli.py:43-119, cli.py:212-242)
- `get_files` calls `pols.ls` with `R=recursive`, `with_filter=filter_expr`, `merge_all`, `as_path=True`, `keep="path,name,is_dir"`, `to_dict=True` (src/mdbed/utils.py:37-45)
- `mdbed embed` writes progress messages to stderr and the result table to stdout, or to CSV with `-o` (src/mdbed/cli.py:122-209)
- `mdbed embed .` run from inside `example/data/` finds the 4 example files and embeds their 123 nodes before failing in `find_similar_nodes`

## Missing

- A default markdown-only file filter for `embed` has no code — `filter_expr` defaults to `None`, so `mdbed embed .` processes `.txt` and any other file type (src/mdbed/cli.py:104-109, cli.py:128-133)
- Suppression of polars-ls stdout output has no code — each `get_files` call prints a DataFrame to stdout ahead of mdbed's own results (src/mdbed/utils.py:37-45)
- Directory scanning outside the current working directory has no working path — polars-ls `resegment_raw_path` raises `ValueError` from `Path.relative_to` (src/mdbed/utils.py:37-45)

## Divergence

- Help text and docstring examples for the listing command show `mdbed list .` and `mdbed list file1.md file2.md`, but click registers the command as `list-files`, and `DefaultCommandGroup` reroutes `mdbed list .` to `embed`, failing with "Path 'list' does not exist" (src/mdbed/cli.py:212-242)
- The listing command's default filter `'{name}.str.ends_with(".md")'` raises `ValueError: Filter ... failed, skipped` in polars-ls 0.5.4, so `mdbed list-files .` crashes (src/mdbed/cli.py:253-254)
- `embed` help says "Embed markdown files" but `embed` without `-f` embeds every file type found (src/mdbed/cli.py:43-69, cli.py:128-133)
