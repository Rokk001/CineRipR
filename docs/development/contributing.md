# Contributing

Thanks for your interest in improving CineRipR!

## Development setup
- Python 3.11+
- 7-Zip available on PATH (or configure via `--seven-zip`)
- Install dev deps: `pip install -e .[dev]`
- Run tests: `pytest`

## Code style
- Keep functions focused and readable
- Avoid deep nesting; prefer early returns
- Add comments only for non-obvious logic

## Commit and PR guidelines
- Small, focused PRs
- Include a clear description and reproduction steps if fixing a bug
- If changing output format, include before/after examples

## Debugging
- Use `--debug` to print directory traversal and decision logs

## Reporting issues
- Use the GitHub issue templates and include logs with `--debug` when possible
