from __future__ import annotations

from pathlib import Path

import dalaran as dl
import semver
import tomli


def test_version() -> None:
    cargo_toml_path = Path(__file__).parent.parent.parent.parent / "Cargo.toml"
    # ensure Cargo.toml file is loaded as UTF-8 (this can fail on Windows otherwise)
    cargo_toml = tomli.loads(cargo_toml_path.read_text(encoding="utf-8"))
    assert dl.__version__ == cargo_toml["workspace"]["package"]["version"]

    ver = semver.VersionInfo.parse(dl.__version__)

    assert len(dl.__version_info__) == 4

    assert ver.major == dl.__version_info__[0]
    assert ver.minor == dl.__version_info__[1]
    assert ver.patch == dl.__version_info__[2]

    if ver.prerelease:
        assert ver.prerelease == dl.__version_info__[3]
    else:
        # The last field is `None` if there is no prerelease.
        assert dl.__version_info__[3] is None

    assert dl.__version__ in dl.version()


if __name__ == "__main__":
    test_version()
