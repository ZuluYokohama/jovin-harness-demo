"""Self-tests use fabricated records only; no submitted Python is executed."""

import copy
import tempfile
import unittest
from pathlib import Path

import verify_evidence as verifier


class DemoFixture:
    def __init__(self, root, wrong_failed_test=False, cleanup="removed"):
        self.root, self.records = root, []
        self.names = [f"test_case_{index}" for index in range(1, 12)]
        self.names[3] = verifier.SELF_APPROVAL_TEST
        self.good = b"def evaluate_change():\n    return 'good'\n"
        self.bad = b"def evaluate_change():\n    return 'bad'\n"
        self.tests = ("\n\n".join(f"def {name}():\n    assert True" for name in self.names) + "\n").encode()
        self.module = {
            "path": "approval_policy.py",
            "tests": self.tests.decode(),
            "tests_sha256": verifier.sha(self.tests),
            "plan": {
                "format": "jovin-harness.qa-plan.v1",
                "project_id": "fabricated-self-test",
                "module": "solution",
                "prompt": "Self-test records only",
                "objective": "Exercise verifier",
                "acceptance": [
                    {"id": f"TEAM{index:02}", "description": name, "test": name}
                    for index, name in enumerate(self.names, 1)
                ],
                "policy": {"network": "none", "isolation": "process"},
            },
        }
        self.policy = {
            "repository": "example/synthetic-demo",
            "branch": "demo",
            "app_id": 12,
            "installation_id": 34,
            "modules": [self.module],
            "runtime": {
                "image": "sha256:" + "a" * 64,
                "runner_sha256": "b" * 64,
                "package_sha256": "c" * 64,
                "harness_version": "self-test",
                "container_command": ["docker"],
                "runtime": "docker",
                "limits": {"memory_bytes": 536870912, "pids": 64},
            },
        }
        self.policy_hash = verifier.sha(verifier.canonical(self.policy))
        self.write("evidence/policy.json", verifier.canonical(self.policy))
        self.write("tests.py", self.tests)
        plan = self.append(
            {
                "tool": "plan_qa",
                "integrity": "plan",
                "plan": self.module["plan"],
                "inputs": {"tests_sha256": self.module["tests_sha256"]},
                "result": {"status": "planned"},
            }
        )
        self.append(
            {
                "tool": "gate.enroll",
                "policy_sha256": self.policy_hash,
                "bindings": [
                    {"path": self.module["path"], "plan_receipt_id": plan["id"], "plan_receipt_sha256": plan["sha256"]}
                ],
                "result": {"status": "enrolled"},
            }
        )
        self.append(
            {
                "tool": "gate.repository",
                "policy_sha256": self.policy_hash,
                "repository": self.policy["repository"],
                "repository_id": 123,
            }
        )
        stages = {}
        commits = {"baseline": "1" * 40, "bad": "2" * 40, "fixed": "3" * 40}
        for label in ("baseline", "bad", "fixed"):
            passed = label != "bad"
            source = self.good if passed else self.bad
            source_path = "evidence/candidates/" + label + ".py"
            self.write(source_path, source)
            inputs = {"code_sha256": verifier.sha(source), "tests_sha256": self.module["tests_sha256"]}
            qas = []
            attempt = label

            def qa(name, status, result=None):
                record = self.append(
                    {
                        "tool": "check_qa",
                        "integrity": "workflow",
                        "inputs": inputs,
                        "qa": {
                            "attempt_id": attempt,
                            "plan_receipt_id": plan["id"],
                            "plan_sha256": plan["sha256"],
                            "stage": name,
                            "previous_stage_receipt_id": qas[-1]["id"] if qas else None,
                        },
                        "result": {"status": status, **(result or {})},
                    }
                )
                qas.append(record)
                return record

            for name in verifier.QA_STAGES[:3]:
                qa(name, "passed")
            failed = self.names[1] if wrong_failed_test else verifier.SELF_APPROVAL_TEST
            outcomes = [
                {"name": name, "message": "", "outcome": "failed" if not passed and name == failed else "passed"}
                for name in ["<module>", *self.names]
            ]
            outcome = {
                "mode": "verify",
                "isolation": "process",
                "status": "passed" if passed else "failed",
                "timed_out": False,
                "output_truncated": False,
                "exit_code": 0,
                "code_exit_code": 0,
                "total": 12,
                "passed_count": 12 if passed else 11,
                "tests": outcomes,
                "kernel": {"memory_max": "536870912", "pids_max": "64"},
            }
            execution = self.append(
                {
                    "tool": "check_qa.functional",
                    "integrity": "process_isolated",
                    "inputs": inputs,
                    "result": outcome,
                    "sandbox": {
                        "inspect_verified": True,
                        "kernel_verified": True,
                        "cleanup": cleanup,
                        "image": {
                            "id": self.policy["runtime"]["image"],
                            "runner_sha256": self.policy["runtime"]["runner_sha256"],
                        },
                        "limits": self.policy["runtime"]["limits"],
                    },
                }
            )
            qa(
                "functional",
                "passed" if passed else "failed",
                {
                    "execution_receipt_id": execution["id"],
                    "execution_receipt_sha256": execution["sha256"],
                    "result": outcome,
                    "problems": [] if passed else ["intentional fabricated failure"],
                },
            )
            if passed:
                qa("process_network", "passed")
                qa(
                    "final",
                    "passed",
                    {
                        "execution_receipt_id": execution["id"],
                        "gate_receipts": [item["id"] for item in qas],
                        "acceptance": [{**item, "outcome": "passed"} for item in self.module["plan"]["acceptance"]],
                    },
                )
            candidate = {"head_sha": commits[label]}
            if label != "baseline":
                candidate.update(number=7, base_sha=commits["baseline"])
            report = {
                "path": self.module["path"],
                "passed": passed,
                "status": "passed" if passed else "failed",
                "source_sha256": inputs["code_sha256"],
                "tests_sha256": inputs["tests_sha256"],
                "receipt_id": qas[-1]["id"],
                "receipt_sha256": qas[-1]["sha256"],
                "stages": [
                    {
                        "stage": item["qa"]["stage"],
                        "status": item["result"]["status"],
                        "receipt_id": item["id"],
                        "receipt_sha256": item["sha256"],
                    }
                    for item in qas
                ],
            }
            gate = self.append(
                {
                    "tool": "gate.baseline" if label == "baseline" else "gate.attempt",
                    "integrity": "controller",
                    "repository": self.policy["repository"],
                    "repository_id": 123,
                    "branch": "demo",
                    "policy_sha256": self.policy_hash,
                    "runtime": self.policy["runtime"],
                    "mode": "shadow",
                    "candidate": candidate,
                    "checked_paths": [self.module["path"]],
                    "modules": [report],
                    "result": {"passed": passed, "reason": None, "observed": label != "baseline"},
                }
            )
            stages[label] = {
                "commit": commits[label],
                "source": source_path,
                "gate_receipt_id": gate["id"],
                "gate_receipt_sha256": gate["sha256"],
            }
        self.manifest = {
            "format": verifier.FORMAT,
            "classification": "synthetic-public-demo",
            "repository": {"full_name": self.policy["repository"], "id": 123},
            "branch": "demo",
            "pull_request": 7,
            "modules": [{"path": self.module["path"], "tests": "tests.py"}],
            "policy": {"path": "evidence/policy.json", "sha256": self.policy_hash},
            "chain": {
                "index": "evidence/receipts/index.jsonl",
                "count": len(self.records),
                "head_id": self.records[-1]["id"],
                "head_sha256": self.records[-1]["sha256"],
            },
            "stages": stages,
            "artifacts": [],
        }
        self.write_index()
        self.refresh()

    def append(self, body):
        record = {
            "format": verifier.RECEIPT_FORMAT,
            "id": f"20261119T000000Z-{len(self.records) + 1:012x}",
            "created_at": "2026-11-19T00:00:00.000Z",
            "notice": "FABRICATED SELF-TEST DATA",
            "prev_sha256": self.records[-1]["sha256"] if self.records else None,
            **copy.deepcopy(body),
        }
        record["sha256"] = verifier.sha(verifier.canonical(record))
        self.records.append(record)
        self.write("evidence/receipts/" + record["id"] + ".json", verifier.canonical(record))
        return record

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def write_index(self, records=None):
        records = self.records if records is None else records
        self.write(
            "evidence/receipts/index.jsonl",
            b"".join(
                verifier.canonical({key: record[key] for key in ("id", "sha256", "prev_sha256")}) + b"\n"
                for record in records
            ),
        )

    def refresh(self):
        self.manifest["artifacts"] = [
            {
                "path": path.relative_to(self.root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": verifier.sha(path.read_bytes()),
            }
            for path in sorted(self.root.rglob("*"))
            if path.is_file() and path.name != "evidence-manifest.json"
        ]
        self.save()

    def save(self):
        self.write("evidence-manifest.json", verifier.canonical(self.manifest))

    def verify(self):
        return verifier.verify(self.root / "evidence-manifest.json")


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="jovin-public-verifier-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = DemoFixture(self.root)

    def test_valid_complete_demo_reports_limited_claim(self):
        result = self.fixture.verify()
        self.assertTrue(result["valid"])
        self.assertEqual(result["receipt_count"], 25)
        self.assertEqual(result["verification"], "internal_consistency_only")
        self.assertFalse(result["github_checked"])
        self.assertEqual(result["stages"]["bad"]["failed_criteria"], ["TEAM04"])
        self.assertEqual(result["stages"]["fixed"]["passed_criteria"], 11)

    def test_tampered_source_artifact_is_rejected(self):
        self.fixture.write("evidence/candidates/bad.py", b"changed bytes\n")
        with self.assertRaisesRegex(verifier.EvidenceError, "artifact hash or size"):
            self.fixture.verify()

    def test_missing_chain_file_is_rejected(self):
        (self.root / ("evidence/receipts/" + self.fixture.records[0]["id"] + ".json")).unlink()
        with self.assertRaises((verifier.EvidenceError, OSError)):
            self.fixture.verify()

    def test_missing_middle_chain_entry_is_rejected_even_with_updated_inventory(self):
        self.fixture.write_index(self.fixture.records[:5] + self.fixture.records[6:])
        self.fixture.manifest["chain"]["count"] -= 1
        self.fixture.refresh()
        with self.assertRaisesRegex(verifier.EvidenceError, "broken chain"):
            self.fixture.verify()

    def test_non_genesis_suffix_is_rejected(self):
        self.fixture.write_index(self.fixture.records[1:])
        self.fixture.manifest["chain"]["count"] -= 1
        self.fixture.refresh()
        with self.assertRaisesRegex(verifier.EvidenceError, "non-genesis"):
            self.fixture.verify()

    def test_receipt_tamper_fails_after_artifact_hash_is_refreshed(self):
        record = copy.deepcopy(self.fixture.records[-1])
        record["result"]["passed"] = False
        self.fixture.write("evidence/receipts/" + record["id"] + ".json", verifier.canonical(record))
        self.fixture.refresh()
        with self.assertRaisesRegex(verifier.EvidenceError, "receipt hash"):
            self.fixture.verify()

    def test_wrong_source_binding_is_rejected(self):
        self.fixture.manifest["stages"]["bad"]["source"] = "evidence/candidates/baseline.py"
        self.fixture.save()
        with self.assertRaisesRegex(verifier.EvidenceError, "source/tests binding"):
            self.fixture.verify()

    def test_wrong_commit_binding_is_rejected(self):
        self.fixture.manifest["stages"]["bad"]["commit"] = "f" * 40
        self.fixture.save()
        with self.assertRaisesRegex(verifier.EvidenceError, "commit binding"):
            self.fixture.verify()

    def test_wrong_failed_test_is_rejected_in_consistent_chain(self):
        fixture = DemoFixture(self.root, wrong_failed_test=True)
        with self.assertRaisesRegex(verifier.EvidenceError, "functional outcomes"):
            fixture.verify()

    def test_unconfirmed_cleanup_is_rejected_in_consistent_chain(self):
        fixture = DemoFixture(self.root, cleanup="unconfirmed")
        with self.assertRaisesRegex(verifier.EvidenceError, "cleanup unconfirmed"):
            fixture.verify()

    def test_policy_digest_drift_is_rejected(self):
        policy = copy.deepcopy(self.fixture.policy)
        policy["branch"] = "other"
        self.fixture.write("evidence/policy.json", verifier.canonical(policy))
        self.fixture.refresh()
        with self.assertRaisesRegex(verifier.EvidenceError, "policy digest"):
            self.fixture.verify()

    def test_unsafe_artifact_path_is_rejected(self):
        self.fixture.manifest["artifacts"][0]["path"] = "../escape.json"
        self.fixture.save()
        with self.assertRaisesRegex(verifier.EvidenceError, "unsafe artifact path"):
            self.fixture.verify()

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(verifier.EvidenceError, "duplicate JSON"):
            verifier.parse(b'{"format": "first", "format": "second"}')

    def test_nonfinite_json_is_rejected(self):
        with self.assertRaisesRegex(verifier.EvidenceError, "non-finite"):
            verifier.parse(b'{"value": NaN}')


if __name__ == "__main__":
    unittest.main()
