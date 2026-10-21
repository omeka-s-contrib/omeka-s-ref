from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def workflow():
    return yaml.safe_load((ROOT / ".github/workflows/pages.yml").read_text())


def steps(job):
    return workflow()["jobs"][job]["steps"]


def test_build_runs_build_py_and_uploads_the_site():
    build = steps("build")
    runs = " ".join(s.get("run", "") for s in build)
    assert "pip install rdflib" in runs
    assert "python build.py _site" in runs
    upload = next(s for s in build if s.get("uses", "").startswith("actions/upload-pages-artifact@"))
    assert upload["uses"] == "actions/upload-pages-artifact@v4"
    assert upload["with"]["path"] == "_site"


def test_deploys_only_from_main():
    deploy = workflow()["jobs"]["deploy"]
    assert deploy["if"] == "github.ref == 'refs/heads/main'"
    assert deploy["needs"] == "build"
    assert deploy["steps"][0]["uses"] == "actions/deploy-pages@v4"
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}
