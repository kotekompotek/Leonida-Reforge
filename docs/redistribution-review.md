# Redistribution and inherited material

This is a repository audit, not a legal determination. The continuation preserves the recovered Git history,
its contributor attribution, the original [GPL license text](../LICENSE), and existing third-party notices.
Leonida's GPLv3-or-later notice applies to its own code; it is not a claim that external dependencies, artwork,
trademarks, or proprietary inputs are licensed under those terms.

| Material | Finding and handling |
|---|---|
| Inherited artwork | The archived `assets/logo.png` was credited to SlyDevil on SteamGridDB; Git records a later change to `assets/logo.svg`. A credit or a vector version is not evidence of permission to redistribute. Both files are excluded from the current tree; the credit and Git history are preserved. Do not include the artwork in new branding, releases, or replicas without verifying rights. |
| Game inputs and generated outputs | Do not redistribute executables, archives, extracted assets, game-derived shaders, caches, saves, decryption keys, or logs quoting game data. Build only from lawfully available local inputs. Synthetic fixtures must have documented provenance. The version manifest describes package files with metadata, not game payloads. |
| Dependencies | Keep the submodule pin and review its license separately. Preserve the included notices for [XTaskQueue](../third_party/xtaskqueue/LICENSE), [bcpack-rs (MIT)](../third_party/bcpack-rs/LICENSE-MIT) and [bcpack-rs (Apache)](../third_party/bcpack-rs/LICENSE-APACHE), and the [XMA reference notice](../third_party/xma/NOTICE.md) and [LGPL text](../third_party/xma/COPYING.LGPLv2.1). Before distributing any built release, review the dependency versions, licenses, corresponding source and notices applicable to that release. |
| Original hosting | No authenticated notice or description of the scope of a prior removal was reviewed. Repository unavailability does not establish a reason or grant permission. Do not infer that any path was affected or cleared. |

## Before any release or replica

- Review the exact tree, build artifacts, submodules, and reachable history that would be published. Scan for
  unexpected binaries, archives, media, generated outputs and keys. The repository's no-game-data check is a
  safeguard, not proof of provenance or a license review.
- Verify source and redistribution permission for non-code assets and third-party materials; preserve notices.
  Do not publish unresolved material. Removing a path from the current tree does not remove historical objects.
- If an authenticated notice or credible concern identifies specific paths or commits, preserve the evidence
  privately, pause redistribution of affected material, and review the scope with the maintainer and host
  before taking further action. Follow applicable obligations and platform procedures. Do not bypass moderation.
- For a rights concern, contact [@JokerDreamerCoder](https://github.com/JokerDreamerCoder) or use the host's
  designated reporting process. Identify paths or commits and the basis for the concern without reproducing the
  disputed content in an issue or pull request.
