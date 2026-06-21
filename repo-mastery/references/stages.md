# Repo Mastery Stages

Load only the sections required by the user's goal.

## Discover and Select

Use GitHub discovery when no repository is supplied. Compare license, recent commits, releases, issue/PR activity, documentation, tests, and fit for the requested feature. Do not select by stars alone.

## Architecture and Domain

Identify entry points, primary packages, dependency direction, state/data flow, external integrations, tests, and operational boundaries. Use Codegraph before broad file searches when the repository is indexed. Build a persistent Understand Anything graph only when repeated exploration or visualization justifies its setup cost.

## Focused Learning Path

Order material by dependency on the requested feature:

1. User-visible behavior and acceptance criteria.
2. Entry point and request/event flow.
3. Core domain types and invariants.
4. Extension point and affected dependencies.
5. Existing tests demonstrating the intended pattern.

Use short exercises such as tracing one call path, predicting one test result, or making one reversible local change. Verify each exercise before proceeding.

## Implementation

For small changes, use a concise plan and direct implementation. For cross-module or long-running work, write a specification, isolate the worktree, implement test-first, and retain checkpoints. Do not modify unrelated files or silently change public behavior.

## Diff and Review

Summarize changed components, callers/dependents, affected layers, behavior changes, migration concerns, and rollback. Run the project's own checks and verify the target surface: browser for Web, simulator/device for App, command/API for CLI or services.

## Onboarding or Full Curriculum

Use only when explicitly requested. Cover project purpose, setup, architecture, domain flows, common tasks, debugging, testing, extension points, limitations, and a sequence of increasingly independent changes. Keep generated dashboards optional.
