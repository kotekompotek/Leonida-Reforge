# Project governance

`LeonidaReforge/Leonida` is an independent continuation owned by [LeonidaReforge](https://github.com/LeonidaReforge).
[@JokerDreamerCoder](https://github.com/JokerDreamerCoder) is its maintainer. Historical authorship and credits
do not confer current administrative roles. No former owner or external company is represented by this project.

## Decisions and review

- Use [issues](https://github.com/LeonidaReforge/Leonida/issues) for scope and technical decisions and
  [pull requests](https://github.com/LeonidaReforge/Leonida/pulls) for changes. Record decisions and reasons there
  unless publishing would disclose security, personal, or rights-sensitive information.
- Maintainers triage reports, request review, and record why changes are accepted or deferred. They may invite
  reviewers with relevant subsystem knowledge. Only organization-authorized maintainers may merge or
  administer the repository.
- Changes go through a PR. Require an independent technical review and passing applicable CI before merging.
  If an independent maintainer review is not available, leave the PR open. `CODEOWNERS` routes review requests;
  it does not grant permissions or enforce approval on its own.
- Review correctness, failure behavior, reproducibility, and provenance. Require a regression test where
  appropriate and a stated reason for unavailable checks. A historical result, a synthetic test, and a
  successful retail run are not interchangeable evidence.
- Keep contributions focused. Preserve attribution and third-party notices, and follow the
  [redistribution review](docs/redistribution-review.md) before any release or replica.

## Recommended hosting and continuity controls

These are recommendations, not a claim that protections, extra maintainers, or replicas have been configured.

1. Protect `main`: require PR review, dismiss stale approvals on new changes, require review conversations to be
   resolved, and disallow force pushes and branch deletion. Require the no-game-data check and an always-reported
   CI result. Use a stable summary check before requiring path-filtered Windows/runtime or workflow checks; a
   skipped workflow must not leave the PR waiting for a status that cannot report.
2. Authorize at least two maintainers with separate accounts, MFA and least-privilege access. Record coverage and
   succession privately. Review access and recovery credentials periodically; do not share tokens.
3. Keep dated, access-controlled backups on independent storage. Use a Git mirror clone and `git bundle create
   <backup.bundle> --all` for the approved refs; verify with `git bundle verify` inside a repository. Record
   ref names, commit IDs, bundle checksums and the date. Restore to an isolated directory and run `git fsck
   --full`; compare refs and verify that pinned submodules are separately recoverable. Git does not capture
   issues, settings, or CI artifacts; back up eligible metadata separately with restricted access.
4. Exercise recovery periodically. Freeze publication if provenance or integrity is in doubt; compare a restored
   mirror against the last verified manifest, check submodule pins, rebuild synthetic checks, and restore
   protections before reopening contributions. Publish the recovery decision and verified commit without secrets.
5. Evaluate an independent Forgejo instance or Radicle replica only after authorization and a review of the
   exact material that would be copied, including reachable history. Never mirror disputed content or use a
   replica to evade platform restrictions. Do not copy personal histories, private reports or credentials into
   a public replica.

For security incidents see [SECURITY.md](SECURITY.md); for licensing and rights reports see
[Redistribution review](docs/redistribution-review.md).

## Contributor access

These are intended repository roles, not automatic promotions or organization ownership:

| Role | Access | Intended work |
|---|---|---|
| External contributor | Forks and pull requests | Contribute changes and reproducible evidence. |
| Contributors | Triage | Help categorize, deduplicate, and follow up on reports. |
| Developers | Write | Collaborate on branches and review code; follow `main` protections. |
| Maintainers | Maintain | Coordinate reviews and releases without full repository administration. |
| Core Team | Admin | Maintain repository security and access policy; review sensitive changes. |

An organization owner approves each access change based on a documented need and a track record of reviewed
contributions. Grant only the lowest role needed, preserve separate organization ownership, and re-evaluate
access when duties change. New or unknown contributors do not receive write access or administrative
permissions automatically.
