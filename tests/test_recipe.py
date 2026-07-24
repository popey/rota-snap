from hashlib import sha256
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).parents[1]
RECIPE = ROOT / "snap" / "snapcraft.yaml"
WORKFLOW = ROOT / ".github" / "workflows" / "build-and-smoke-test.yml"
BINARY = ROOT / "snap" / "local" / "bin" / "ROTA.x86_64"
PACK = ROOT / "snap" / "local" / "bin" / "ROTA.pck"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


class RecipeTest(unittest.TestCase):
    def test_recipe_and_assets_pin_rota_2026_03_12(self):
        recipe = yaml.safe_load(RECIPE.read_text())

        self.assertEqual(recipe["version"], "2026.03.12")
        self.assertEqual(recipe["base"], "core22")
        self.assertEqual(recipe["confinement"], "strict")
        self.assertEqual(recipe["license"], "GPL-3.0")
        self.assertEqual(recipe["architectures"], [{"build-on": "amd64"}])
        self.assertEqual(recipe["apps"]["rota"]["command"], "bin/launch")
        self.assertIn("VK_ICD_FILENAMES", recipe["apps"]["rota"]["environment"])
        self.assertNotIn("VK_ICD_FILENAMESr", recipe["apps"]["rota"]["environment"])
        self.assertEqual(
            digest(BINARY),
            "178d0c020b6e0daf7cdc7512d3ae8917b85ebce9312415bdc58e6ab794dca901",
        )
        self.assertEqual(
            digest(PACK),
            "0b70f687fcf0f762a1fdba97fdbd73b67d2999b69f47bff53ac77bf34740d20b",
        )
        self.assertTrue(BINARY.stat().st_mode & 0o111)


class WorkflowTest(unittest.TestCase):
    def test_workflow_builds_reviews_and_smokes_the_exact_artifact(self):
        workflow_text = WORKFLOW.read_text()
        workflow = yaml.safe_load(workflow_text)
        triggers = workflow[True]
        steps = workflow["jobs"]["build"]["steps"]
        names = [step["name"] for step in steps]
        by_name = {step["name"]: step for step in steps}

        self.assertEqual(workflow["jobs"]["build"]["runs-on"], "ubuntu-22.04")
        self.assertEqual(triggers["pull_request"]["branches"], ["main"])
        self.assertEqual(triggers["push"]["branches"], ["main"])
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        self.assertFalse(by_name["Checkout code"]["with"]["persist-credentials"])
        self.assertLess(names.index("Build snap"), names.index("Review snap"))
        self.assertLess(names.index("Review snap"), names.index("Install and smoke-test snap"))
        self.assertLess(names.index("Install and smoke-test snap"), names.index("Upload artifact"))
        self.assertNotIn("uses", by_name["Build snap"])
        self.assertIn("snapcraft pack --destructive-mode", by_name["Build snap"]["run"])
        self.assertIn('test "${#BEFORE[@]}" -eq 0', by_name["Build snap"]["run"])
        self.assertIn('test "${#ARTIFACTS[@]}" -eq 1', by_name["Build snap"]["run"])
        self.assertIn("review-tools.snap-review", by_name["Review snap"]["run"])
        dependencies = by_name["Install test dependencies"]["run"]
        self.assertIn("xvfb", dependencies)
        self.assertIn("xauth", dependencies)
        smoke = by_name["Install and smoke-test snap"]["run"]
        self.assertIn("snap install --dangerous", smoke)
        self.assertIn("snap run rota --version", smoke)
        self.assertIn("xvfb-run --auto-servernum", smoke)
        self.assertIn("-screen 0 1280x720x24", smoke)
        self.assertIn("snap run rota --headless --quit", smoke)
        self.assertEqual(
            by_name["Upload artifact"]["uses"],
            "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
        )


if __name__ == "__main__":
    unittest.main()
