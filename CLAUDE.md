# CLAUDE.md

This file provides guidance to Claude Code (and other AI assistants) when working in this repository.

## Repository status

**This repository is currently empty.** As of the last update there are no
source files, build configuration, or commit history — the repository has just
been initialized.

This file is a scaffold. As code is added, replace the placeholder sections
below with concrete, verified details. Do **not** invent commands, frameworks,
or conventions that are not actually present in the codebase — document only
what exists.

## How to keep this file accurate

When the project gains real content, update each section below with facts
drawn from the actual files. Good sources to check:

- **Language & tooling:** the manifest/lockfile (`package.json`, `pyproject.toml`,
  `go.mod`, `Cargo.toml`, `pom.xml`, etc.)
- **Build / test / lint commands:** scripts in the manifest, a `Makefile`,
  `Taskfile`, or CI workflow files under `.github/workflows/`
- **Structure:** the top-level directory layout and where the entry point lives
- **Conventions:** existing formatter/linter config (`.editorconfig`,
  `.prettierrc`, `.eslintrc`, `ruff.toml`, etc.) and patterns visible in the code

## Project overview

_TODO: One or two sentences on what this project does and who uses it._

## Architecture

_TODO: Describe the major components and how they fit together. Note the entry
point(s) and any non-obvious design decisions worth knowing before making
changes._

## Directory structure

_TODO: Map the top-level directories to their responsibilities once they exist._

## Development workflow

### Setup

_TODO: How to install dependencies and prepare a local environment._

### Common commands

_TODO: Fill in the real commands once tooling is configured. For example:_

```sh
# Install dependencies
# Run the app
# Run tests
# Lint / format
```

## Conventions

_TODO: Document coding style, naming conventions, commit message format, branch
naming, and any project-specific rules contributors are expected to follow._

## Git workflow

- Default development branch for AI-assisted work: `claude/claude-md-docs-j4uw85`
  (per current task configuration).
- Create feature branches off the main line; commit with clear, descriptive
  messages; push the branch and open a pull request when ready.
- Do not push directly to a shared branch without explicit permission.
