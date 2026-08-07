# Security policy

## Supported versions

Dalaran is pre-1.0 and under active development. Security fixes land on `main`
and go out in the next release. Only the latest released version is supported;
if you are running something older, the first thing we will ask is whether the
issue reproduces on the current release.

## Reporting a vulnerability

Please report vulnerabilities privately to <opensource@dalaran.dev>.

Do **not** open a public GitHub issue, discussion, or pull request for a
suspected vulnerability, and please do not contact individual contributors
directly — a single inbox means a report cannot be lost because one person is
on holiday.

You can also use GitHub's private reporting on
[the Security tab](https://github.com/Flaminis/Dalaran/security/advisories/new)
if you prefer to keep the whole exchange on GitHub.

### What to include

The more of this you can provide, the faster we can act:

- affected component and version (`dalaran --version`, or the SDK version and
  language);
- your platform: OS, architecture, and — for anything touching rendering — GPU
  and driver;
- a description of the impact: what an attacker gains, and what access they
  need to start with;
- a reproduction: a minimal script, a crafted `.dlr`/`.dbl`/MCAP file, or a
  network request sequence. Small attachments are fine by email;
- whether the issue is already public anywhere.

### What to expect

- We aim to acknowledge a report within three working days.
- We will tell you our assessment of severity and whether we agree it is a
  vulnerability, with reasoning either way.
- We will keep you updated while we work on a fix, and let you know when it
  ships.
- We will credit you in the advisory and the release notes unless you ask us
  not to.

We ask that you give us a reasonable window to ship a fix before disclosing
publicly. We do not run a bug bounty and cannot offer payment.

## Areas we consider in scope

Dalaran parses untrusted-ish input in several places, and problems there are
exactly what we want to hear about:

- recording, blueprint, MCAP, and other importer parsing (memory safety,
  panics that are reachable from a crafted file, decompression bombs);
- the gRPC transport and the catalog/data server, including authentication and
  path handling;
- the web viewer and anything that ends up executing in a browser context;
- the CLI's handling of paths, URIs, and archives;
- dependency vulnerabilities that are actually reachable from our code.

## Out of scope

- Reports from automated scanners with no demonstrated impact on Dalaran.
- Vulnerabilities that require an attacker to already have full control of the
  machine running the viewer.
- Denial of service caused by legitimately enormous recordings — that is a
  performance bug, and it belongs in the public issue tracker.
- Issues in upstream [Rerun](https://github.com/rerun-io/rerun) that do not
  affect this codebase; please report those to upstream. If an issue affects
  both, tell us and we will coordinate.

## Non-vulnerability security work

Ideas for security *features* — sandboxing, supply-chain hardening,
reproducible builds — are very welcome as public
[GitHub issues](https://github.com/Flaminis/Dalaran/issues).
