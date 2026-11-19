"""Offline consistency checks for one synthetic baseline / bad / fixed demo.

This program reads JSON and bytes. It never imports or executes candidate/test
files, contacts GitHub, or verifies cryptographic signatures or real-world truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path, PurePosixPath

FORMAT = "jovin-demo.evidence.v1"
RECEIPT_FORMAT = "jovin-harness.receipt.v1"
RID = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
SELF_APPROVAL_TEST = "test_author_self_approval_is_denied_even_for_admin"
QA_STAGES = ["binding", "ast", "trace_requirements", "functional", "process_network", "final"]
MAX_FILE = 4 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
NOTICE = (
    "Verified internal consistency of the supplied artifacts and recorded outcomes only. "
    "Hashes are not signatures, host attestation, proof of correctness, customer evidence, "
    "or independent confirmation of GitHub state."
)


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _constant(_):
    raise EvidenceError("non-finite JSON number")


def parse(data):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise EvidenceError("invalid or excessively nested JSON") from error


def fields(value, required, optional=()):
    require(isinstance(value, dict), "expected JSON object")
    require(set(required) <= set(value) <= set(required) | set(optional), "unexpected or missing object fields")


def valid_sha(value):
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def relative(value):
    require(isinstance(value, str) and 0 < len(value) <= 512, "invalid artifact path")
    require(
        not any(char in value for char in "\\:\x00") and not any(ord(char) < 32 for char in value),
        "invalid artifact path",
    )
    require(all(part not in ("", ".", "..") for part in value.split("/")), "unsafe artifact path")
    return value


def read_file(root, name):
    name = relative(name)
    target = root
    for part in name.split("/"):
        target = target / part
        metadata = target.lstat()
        require(
            not stat.S_ISLNK(metadata.st_mode) and not getattr(metadata, "st_file_attributes", 0) & 0x400,
            "artifact paths must not traverse links or reparse points",
        )
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_size <= MAX_FILE, "artifact must be a bounded regular file")
    with target.open("rb") as handle:
        data = handle.read(MAX_FILE + 1)
    require(len(data) <= MAX_FILE, "artifact exceeds size limit")
    return data


def artifacts(root, manifest):
    entries = manifest["artifacts"]
    require(isinstance(entries, list) and 1 <= len(entries) <= 1000, "invalid artifact inventory")
    data, total = {}, 0
    for entry in entries:
        fields(entry, ("path", "bytes", "sha256"))
        name = relative(entry["path"])
        require(name not in data and valid_sha(entry["sha256"]), "duplicate artifact or invalid hash")
        require(type(entry["bytes"]) is int and 0 <= entry["bytes"] <= MAX_FILE, "invalid artifact size")
        raw = read_file(root, name)
        require(len(raw) == entry["bytes"] and sha(raw) == entry["sha256"], "artifact hash or size mismatch: " + name)
        total += len(raw)
        require(total <= MAX_TOTAL, "artifact bundle exceeds size limit")
        data[name] = raw
    return data


def chain(root, specification, data):
    fields(specification, ("index", "count", "head_id", "head_sha256"))
    index = relative(specification["index"])
    require(index in data, "receipt index is not inventoried")
    require(type(specification["count"]) is int and 1 <= specification["count"] <= 1000, "invalid chain count")
    entries = [parse(line) for line in data[index].splitlines() if line.strip()]
    require(len(entries) == specification["count"], "chain count mismatch")
    directory = PurePosixPath(index).parent
    records, positions, paths, previous = {}, {}, set(), None
    for position, entry in enumerate(entries):
        fields(entry, ("id", "sha256", "prev_sha256"))
        identifier = entry["id"]
        require(isinstance(identifier, str) and RID.fullmatch(identifier), "invalid receipt identifier")
        require(identifier not in records and valid_sha(entry["sha256"]), "duplicate receipt or invalid hash")
        name = (directory / (identifier + ".json")).as_posix()
        require(name in data, "receipt missing from artifact inventory")
        receipt = parse(data[name])
        require(isinstance(receipt, dict) and receipt.get("format") == RECEIPT_FORMAT, "invalid receipt format")
        require(receipt.get("id") == identifier, "receipt file identity mismatch")
        require(
            receipt.get("prev_sha256") == previous and entry["prev_sha256"] == previous,
            "broken chain or non-genesis export",
        )
        hashed = sha(canonical({key: value for key, value in receipt.items() if key != "sha256"}))
        require(hashed == entry["sha256"] == receipt.get("sha256"), "receipt hash mismatch")
        records[identifier], positions[identifier], previous = receipt, position, hashed
        paths.add(name)
    inventory = {name for name in data if PurePosixPath(name).parent == directory and name.endswith(".json")}
    require(inventory == paths, "unindexed receipt artifact")
    disk_names = {(directory / path.name).as_posix() for path in (root / directory).glob("*.json")}
    require(disk_names == paths, "unindexed receipt file")
    require(
        entries[-1]["id"] == specification["head_id"] and previous == specification["head_sha256"],
        "chain head mismatch",
    )
    return records, positions


def receipt(records, identifier, expected_hash=None):
    require(isinstance(identifier, str) and identifier in records, "referenced receipt missing from chain")
    result = records[identifier]
    if expected_hash is not None:
        require(result["sha256"] == expected_hash, "referenced receipt hash mismatch")
    return result


def inputs(record, source_hash, tests_hash):
    value = record.get("inputs", {})
    require(
        value.get("code_sha256") == source_hash and value.get("tests_sha256") == tests_hash,
        "source/tests receipt binding mismatch",
    )


def functional(record, policy, names, failed_name):
    require(
        record.get("tool") == "check_qa.functional" and record.get("integrity") == "process_isolated",
        "functional receipt is not process-isolated verification",
    )
    result, sandbox = record["result"], record["sandbox"]
    require(result.get("mode") == "verify" and result.get("isolation") == "process", "wrong execution mode")
    require(
        all(sandbox.get(key) is True for key in ("inspect_verified", "kernel_verified"))
        and sandbox.get("cleanup") == "removed",
        "container inspection, limits, or cleanup unconfirmed",
    )
    require(
        sandbox["image"]["id"] == policy["runtime"]["image"]
        and sandbox["image"]["runner_sha256"] == policy["runtime"]["runner_sha256"],
        "execution image/runner differs from policy",
    )
    limits, kernel = sandbox["limits"], result["kernel"]
    require(limits == policy["runtime"]["limits"], "execution limits differ from policy")
    require(
        kernel.get("memory_max") == str(limits["memory_bytes"]) and kernel.get("pids_max") == str(limits["pids"]),
        "recorded kernel limits mismatch",
    )
    require(
        result.get("timed_out") is False
        and result.get("output_truncated") is False
        and result.get("exit_code") == 0
        and result.get("code_exit_code") == 0,
        "functional execution did not finish cleanly",
    )
    outcomes = result.get("tests")
    require(isinstance(outcomes, list) and len(outcomes) == len(names) + 1, "unexpected test record count")
    mapping = {}
    for item in outcomes:
        require(
            isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"] not in mapping,
            "duplicate or malformed test record",
        )
        mapping[item["name"]] = item.get("outcome")
    require(set(mapping) == set(names) | {"<module>"}, "functional test identities differ from plan")
    expected = {name: "failed" if name == failed_name else "passed" for name in mapping}
    require(mapping == expected, "functional outcomes do not match the claimed demo")
    require(
        result.get("total") == len(mapping) and result.get("passed_count") == len(mapping) - bool(failed_name),
        "functional outcome counts mismatch",
    )
    require(result.get("status") == ("failed" if failed_name else "passed"), "functional status mismatch")


def stage(label, specification, manifest, policy, module, tests_hash, records, positions, data, plan_names):
    fields(specification, ("commit", "source", "gate_receipt_id", "gate_receipt_sha256"), ("check_url",))
    commit = specification["commit"]
    require(isinstance(commit, str) and COMMIT.fullmatch(commit), "invalid stage commit")
    source_name = relative(specification["source"])
    require(source_name in data, "stage source is not inventoried")
    source_hash = sha(data[source_name])
    gate = receipt(records, specification["gate_receipt_id"], specification["gate_receipt_sha256"])
    passed = label != "bad"
    require(
        gate.get("tool") == ("gate.baseline" if label == "baseline" else "gate.attempt")
        and gate.get("integrity") == "controller",
        "wrong gate receipt kind",
    )
    require(
        gate.get("repository") == manifest["repository"]["full_name"]
        and gate.get("repository_id") == manifest["repository"]["id"]
        and gate.get("branch") == manifest["branch"],
        "gate repository/branch binding mismatch",
    )
    require(
        gate.get("policy_sha256") == manifest["policy"]["sha256"]
        and gate.get("runtime") == policy["runtime"]
        and gate.get("mode") == "shadow",
        "gate policy/runtime/shadow mode binding mismatch",
    )
    candidate = gate["candidate"]
    require(candidate.get("head_sha") == commit, "candidate commit binding mismatch")
    if label != "baseline":
        require(
            candidate.get("number") == manifest["pull_request"]
            and candidate.get("base_sha") == manifest["stages"]["baseline"]["commit"],
            "pull request or observed base binding mismatch",
        )
        require(gate["result"].get("observed") is True, "candidate outcome was not observed")
    require(
        gate["result"].get("passed") is passed and gate["result"].get("reason") is None,
        "gate outcome differs from claimed demo",
    )
    require(
        gate.get("checked_paths") == [module["path"]] and len(gate.get("modules", [])) == 1,
        "gate module coverage mismatch",
    )
    report = gate["modules"][0]
    require(
        report.get("path") == module["path"]
        and report.get("source_sha256") == source_hash
        and report.get("tests_sha256") == tests_hash,
        "module source/tests binding mismatch",
    )
    require(
        report.get("passed") is passed and report.get("status") == ("passed" if passed else "failed"),
        "module outcome mismatch",
    )
    refs = report["stages"]
    expected_stages = QA_STAGES if passed else QA_STAGES[:4]
    require(
        isinstance(refs, list) and [ref.get("stage") for ref in refs] == expected_stages,
        "QA stages are incomplete or out of order",
    )
    previous, attempt, plan_id, plan_hash = None, None, None, None
    stage_records = []
    for index, ref in enumerate(refs):
        current = receipt(records, ref["receipt_id"], ref["receipt_sha256"])
        require(current.get("tool") == "check_qa" and current.get("integrity") == "workflow", "wrong QA receipt kind")
        inputs(current, source_hash, tests_hash)
        qa = current["qa"]
        if index == 0:
            attempt, plan_id, plan_hash = qa["attempt_id"], qa["plan_receipt_id"], qa["plan_sha256"]
        require(
            qa.get("attempt_id") == attempt
            and qa.get("plan_receipt_id") == plan_id
            and qa.get("plan_sha256") == plan_hash
            and qa.get("stage") == ref["stage"]
            and qa.get("previous_stage_receipt_id") == previous,
            "QA stage/attempt/plan linkage mismatch",
        )
        expected_status = "failed" if not passed and index == len(refs) - 1 else "passed"
        require(current["result"].get("status") == ref.get("status") == expected_status, "QA status mismatch")
        require(positions[current["id"]] < positions[gate["id"]], "QA receipt follows gate result")
        if previous:
            require(positions[previous] < positions[current["id"]], "QA receipt chronology mismatch")
        previous = current["id"]
        stage_records.append(current)
    require(
        report["receipt_id"] == previous and report["receipt_sha256"] == stage_records[-1]["sha256"],
        "module terminal QA receipt mismatch",
    )
    planned = receipt(records, plan_id, plan_hash)
    require(
        planned.get("tool") == "plan_qa"
        and planned.get("integrity") == "plan"
        and planned.get("plan") == module["plan"]
        and planned.get("inputs", {}).get("tests_sha256") == tests_hash
        and planned.get("result", {}).get("status") == "planned",
        "approved plan receipt binding mismatch",
    )
    require(positions[plan_id] < positions[stage_records[0]["id"]], "plan was not recorded before attempt")
    functional_stage = stage_records[3]
    execution = receipt(
        records,
        functional_stage["result"]["execution_receipt_id"],
        functional_stage["result"]["execution_receipt_sha256"],
    )
    inputs(execution, source_hash, tests_hash)
    require(
        positions[stage_records[2]["id"]] < positions[execution["id"]] < positions[functional_stage["id"]],
        "functional receipt chronology mismatch",
    )
    require(functional_stage["result"].get("result") == execution["result"], "embedded functional result mismatch")
    functional(execution, policy, plan_names, None if passed else SELF_APPROVAL_TEST)
    if passed:
        final = stage_records[-1]["result"]
        require(
            final.get("execution_receipt_id") == execution["id"]
            and final.get("gate_receipts") == [record["id"] for record in stage_records[:-1]]
            and final.get("acceptance")
            == [{**criterion, "outcome": "passed"} for criterion in module["plan"]["acceptance"]],
            "final QA acceptance/evidence linkage mismatch",
        )
    if "check_url" in specification:
        require(
            isinstance(specification["check_url"], str)
            and specification["check_url"].startswith("https://github.com/" + manifest["repository"]["full_name"] + "/")
            and not any(ord(char) < 32 for char in specification["check_url"]),
            "invalid check display link",
        )
    return {
        "commit": commit,
        "source_sha256": source_hash,
        "recorded_passed": passed,
        "passed_criteria": 11 if passed else 10,
        "failed_criteria": [] if passed else ["TEAM04"],
        "plan_receipt_id": plan_id,
        "plan_receipt_sha256": plan_hash,
        "gate_receipt_id": gate["id"],
    }


def verify(manifest_path):
    manifest_path = Path(manifest_path)
    root = manifest_path.parent.resolve(strict=True)
    manifest = parse(read_file(root, manifest_path.name))
    fields(
        manifest,
        (
            "format",
            "classification",
            "repository",
            "branch",
            "pull_request",
            "modules",
            "policy",
            "artifacts",
            "chain",
            "stages",
        ),
    )
    require(
        manifest["format"] == FORMAT and manifest["classification"] == "synthetic-public-demo",
        "unsupported evidence format or classification",
    )
    fields(manifest["repository"], ("full_name", "id"))
    require(
        isinstance(manifest["repository"]["full_name"], str)
        and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", manifest["repository"]["full_name"]),
        "invalid repository identity",
    )
    require(type(manifest["repository"]["id"]) is int and manifest["repository"]["id"] > 0, "invalid repository ID")
    require(type(manifest["pull_request"]) is int and manifest["pull_request"] > 0, "invalid PR number")
    require(isinstance(manifest["branch"], str) and manifest["branch"], "invalid branch")
    fields(manifest["policy"], ("path", "sha256"))
    fields(manifest["stages"], ("baseline", "bad", "fixed"))
    require(isinstance(manifest["modules"], list) and len(manifest["modules"]) == 1, "demo requires one module")
    descriptor = manifest["modules"][0]
    fields(descriptor, ("path", "tests"))
    relative(descriptor["path"])
    data = artifacts(root, manifest)
    require(manifest["policy"]["path"] in data and descriptor["tests"] in data, "policy/tests not inventoried")
    policy = parse(data[manifest["policy"]["path"]])
    require(sha(canonical(policy)) == manifest["policy"]["sha256"], "policy digest mismatch")
    require(
        policy.get("repository") == manifest["repository"]["full_name"] and policy.get("branch") == manifest["branch"],
        "manifest policy scope mismatch",
    )
    require(isinstance(policy.get("modules"), list) and len(policy["modules"]) == 1, "policy module count mismatch")
    module = policy["modules"][0]
    tests_hash = sha(data[descriptor["tests"]])
    require(
        module.get("path") == descriptor["path"]
        and module.get("tests_sha256") == tests_hash
        and module.get("tests", "").encode("utf-8") == data[descriptor["tests"]],
        "policy tests binding mismatch",
    )
    criteria = module["plan"]["acceptance"]
    require(isinstance(criteria, list) and len(criteria) == 11, "demo requires eleven acceptance criteria")
    names = [criterion["test"] for criterion in criteria]
    ids = [criterion["id"] for criterion in criteria]
    require(
        len(set(names)) == len(set(ids)) == 11
        and any(item["id"] == "TEAM04" and item["test"] == SELF_APPROVAL_TEST for item in criteria),
        "ambiguous criteria or wrong TEAM04 test",
    )
    records, positions = chain(root, manifest["chain"], data)
    results = {
        name: stage(
            name, manifest["stages"][name], manifest, policy, module, tests_hash, records, positions, data, names
        )
        for name in ("baseline", "bad", "fixed")
    }
    require(len({value["commit"] for value in results.values()}) == 3, "demo revisions must be distinct")
    require(
        results["baseline"]["source_sha256"] == results["fixed"]["source_sha256"] != results["bad"]["source_sha256"],
        "fixed source must restore baseline and differ from bad",
    )
    plan_ids = {(value["plan_receipt_id"], value["plan_receipt_sha256"]) for value in results.values()}
    require(len(plan_ids) == 1, "demo stages use different approved plans")
    require(
        positions[results["baseline"]["gate_receipt_id"]]
        < positions[results["bad"]["gate_receipt_id"]]
        < positions[results["fixed"]["gate_receipt_id"]],
        "demo chronology mismatch",
    )
    plan_id, plan_hash = next(iter(plan_ids))
    bindings = [{"path": module["path"], "plan_receipt_id": plan_id, "plan_receipt_sha256": plan_hash}]
    enrollments = [
        record
        for record in records.values()
        if record.get("tool") == "gate.enroll"
        and record.get("policy_sha256") == manifest["policy"]["sha256"]
        and record.get("bindings") == bindings
        and record.get("result", {}).get("status") == "enrolled"
    ]
    repositories = [
        record
        for record in records.values()
        if record.get("tool") == "gate.repository"
        and record.get("policy_sha256") == manifest["policy"]["sha256"]
        and record.get("repository") == manifest["repository"]["full_name"]
        and record.get("repository_id") == manifest["repository"]["id"]
    ]
    require(len(enrollments) == len(repositories) == 1, "missing or ambiguous enrollment/repository binding")
    require(
        positions[plan_id]
        < positions[enrollments[0]["id"]]
        < positions[repositories[0]["id"]]
        < positions[results["baseline"]["gate_receipt_id"]],
        "enrollment chronology mismatch",
    )
    return {
        "valid": True,
        "verification": "internal_consistency_only",
        "notice": NOTICE,
        "github_checked": False,
        "receipt_count": len(records),
        "head_sha256": manifest["chain"]["head_sha256"],
        "policy_sha256": manifest["policy"]["sha256"],
        "stages": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="public repository root evidence-manifest.json")
    args = parser.parse_args()
    try:
        report = verify(args.manifest)
    except (EvidenceError, OSError, KeyError, TypeError, ValueError, OverflowError, RecursionError) as error:
        reason = str(error) if isinstance(error, EvidenceError) else "missing, unreadable, or malformed evidence"
        print(json.dumps({"valid": False, "verification": "internal_consistency_only", "reason": reason}))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
