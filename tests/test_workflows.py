"""Workflows use only actions this organization runs, and uv comes from one exact pin.

Shorewood-Analytics allows only GitHub-created actions and actions it owns: any other `uses:` makes
the whole workflow fail at startup. uv is installed by the local `.github/actions/uv` action, which
must assert its exact pin before anything reaches PATH. Static checks only (no network).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITHUB = ROOT / ".github"
ACTION = GITHUB / "actions/uv/action.yml"
LOCAL_UV = "./.github/actions/uv"
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(\S+)", re.MULTILINE)
SHA_PINNED = re.compile(r"^(actions|github)/[\w.-]+(/[\w.-]+)*@[0-9a-f]{40}$")


def test_only_sha_pinned_github_actions_or_the_local_uv_action():
    files = [*GITHUB.glob("workflows/*.yml"), *GITHUB.glob("actions/*/action.yml")]
    refs = [(p.relative_to(ROOT), ref) for p in files for ref in USES.findall(p.read_text())]
    assert refs
    bad = [(path, ref) for path, ref in refs if ref != LOCAL_UV and not SHA_PINNED.match(ref)]
    assert not bad


def test_uv_workflows_install_uv_only_through_the_pinned_action():
    for name in ("ci.yml", "auto-release.yml", "release.yml"):
        text = (GITHUB / "workflows" / name).read_text()
        assert f"uses: {LOCAL_UV}\n" in text, name
        assert "pipx" not in text and "setup-uv" not in text, name


def test_uv_action_installs_the_exact_pin_and_asserts_it_before_path():
    text = ACTION.read_text()
    assert re.search(r'^    default: "\d+\.\d+\.\d+"$', text, re.MULTILINE)
    install = text[text.index("pipx install") : text.index("- name:", text.index("pipx install"))]
    assert 'pipx install --force "uv==$UV_VERSION"' in install
    assert install.index("test ") < install.index("GITHUB_PATH")
