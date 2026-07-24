# ROTA snap

Unofficial Snap packaging for [ROTA](https://github.com/HarmonyHoney/ROTA), a gravity-bending puzzle platformer by Harmony Honey.

## Upstream assets

The snap packages the `ROTA.x86_64` and `ROTA.pck` assets from the matching upstream GitHub release. Their release-provided SHA-256 digests are asserted by `tests/test_recipe.py`.

Upstream currently publishes a Linux x86_64 executable only, so the snap intentionally supports amd64 only.

## Verification

```bash
python3 -m unittest discover -s tests -v
snapcraft pack --use-lxd
review-tools.snap-review rota_*.snap
snap install --dangerous rota_*.snap
snap run rota --version
snap run rota --headless --quit
```

The GitHub Actions workflow builds on Ubuntu 22.04 for the core22 base, normalizes and reviews the exact snap, installs it under strict confinement, runs version and headless launch smoke tests, and uploads that same artifact.
