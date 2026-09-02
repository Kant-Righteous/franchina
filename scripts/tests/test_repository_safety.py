import unittest

import yaml

from scripts import check_repository_safety


class RepositorySafetyTests(unittest.TestCase):
    def test_sensitive_files_and_database_sidecars_are_rejected_at_any_depth(self):
        for name in (
            "rates.sqlite",
            "rates.sqlite3",
            "rates.db",
            "rates.sqlite-wal",
            "rates.sqlite3-shm",
            "rates.db-journal",
            "private.pem",
            "private.key",
            "bundle.p12",
            "bundle.pfx",
            "id_rsa",
            "id_rsa.pub",
            "id_ed25519",
            "id_ed25519.backup",
            ".env",
            ".env.production",
            "PRIVATE.KEY",
        ):
            for prefix in ("", "docs/assets/private/"):
                with self.subTest(name=name, prefix=prefix):
                    path = prefix + name
                    self.assertEqual(
                        check_repository_safety.find_sensitive_files([path]), [path]
                    )

    def test_source_and_sanitized_environment_examples_are_allowed(self):
        paths = [
            ".env.example",
            "mcp/.env.example",
            "docs/config.md",
            "mcp/database.py",
            "requirements.txt",
        ]
        self.assertEqual(check_repository_safety.find_sensitive_files(paths), [])

    def test_nested_action_and_reusable_workflow_tags_are_rejected(self):
        workflow = yaml.load(
            """
jobs:
  check:
    steps:
      - uses: actions/checkout@v4
      - uses: appleboy/ssh-action@main
      - uses: jakejarvis/cloudflare-purge-action@master
  reusable:
    uses: example/repo/.github/workflows/test.yml@v1
""",
            Loader=yaml.BaseLoader,
        )
        self.assertEqual(
            check_repository_safety.find_unpinned_actions(workflow),
            [
                "actions/checkout@v4",
                "appleboy/ssh-action@main",
                "jakejarvis/cloudflare-purge-action@master",
                "example/repo/.github/workflows/test.yml@v1",
            ],
        )

    def test_full_commit_refs_and_local_actions_are_allowed(self):
        workflow = {
            "steps": [
                {"uses": "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"},
                {"uses": "./.github/actions/local-check"},
                {"run": "python -m unittest"},
            ]
        }
        self.assertEqual(check_repository_safety.find_unpinned_actions(workflow), [])

    def test_short_hashes_and_malformed_references_are_rejected(self):
        for reference in (
            "actions/checkout@11d5960",
            "actions/checkout@" + "g" * 40,
            "${{ inputs.action }}",
        ):
            with self.subTest(reference=reference):
                self.assertEqual(
                    check_repository_safety.find_unpinned_actions({"uses": reference}),
                    [reference],
                )


if __name__ == "__main__":
    unittest.main()
