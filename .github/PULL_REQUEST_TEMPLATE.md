<!--
Thanks for opening a pull request. Please fill this in — it is what a reviewer
reads first. See CONTRIBUTING.md for the dev setup, commit conventions, and the
DCO sign-off requirement.

Please also allow maintainers to push to your branch, so small fixes do not
need a round-trip:
https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/allowing-changes-to-a-pull-request-branch-created-from-a-fork
-->

### Related

<!-- Link related issues and PRs, e.g.
* Closes #1234
* Part of #1337
-->

### What

<!-- What does this change do? One or two paragraphs is usually right. -->

### Why

<!-- Why is this change worth making? What problem does it solve, for whom?
A reviewer can read the diff to see what you did; they cannot infer the reason. -->

### How it was tested

<!-- Which suites you ran, and anything you could not run and why (for example
image comparison tests need a Vulkan/Metal capable driver).

  cargo nextest run --all-targets --all-features
  pixi run py-test
  pixi run -e cpp cpp-test
  pixi run fast-lint
-->

### What to review

<!-- Point reviewers at what you actually want scrutinised: the API shape, the
architecture, the UX, or just the code. Say how confident you are — "simple fix
in an area I know well" and "outside my domain, please check carefully" are
both useful and both fine. -->

### Screenshots / video

<!-- Required for anything that changes what the viewer looks like or how it
behaves. -->

### Checklist

- [ ] The PR title is a conventional-commit subject, e.g. `feat(robot): …`
- [ ] Commits are signed off (`git commit -s`) per the DCO
- [ ] `pixi run fast-lint` passes
- [ ] Tests were added or updated, or there is a reason none were needed
- [ ] Public APIs have doc comments with a runnable example
- [ ] Docs under `docs/content/` updated if this is user-facing
- [ ] New names follow the `dl_*` / `dalaran` conventions and reintroduce no
      upstream naming for first-party things
- [ ] No new dependency, or the PR explains why the new one is needed and that
      its licence is Apache-2.0 compatible

### Agent disclosure

<!-- If a coding agent wrote a meaningful part of this PR, say so and name the
model. Agent-assisted work is welcome; unreviewed agent output is not. Delete
this section if it does not apply. -->
