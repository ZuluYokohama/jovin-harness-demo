"""Acceptance examples for the internal simulation; execute only in the harness sandbox."""

from solution import evaluate_change


def _change(**updates):
    value = {"id": "change-1", "tenant_id": "tenant-a", "author_id": "author", "head": "rev-2",
             "status": "open", "required_approvals": 2}
    value.update(updates)
    return value


def _actor(identity, **updates):
    value = {"id": identity, "tenant_id": "tenant-a", "role": "reviewer", "active": True, "revoked": False}
    value.update(updates)
    return value


def _actors():
    return [_actor("author", role="admin"), _actor("alice"), _actor("bob", role="admin"), _actor("carol")]


def _review(identity, **updates):
    value = {"actor_id": identity, "tenant_id": "tenant-a", "change_id": "change-1", "head": "rev-2",
             "decision": "approve", "sequence": 1}
    value.update(updates)
    return value


def test_current_authorized_quorum_allows():
    assert evaluate_change(_change(), _actors(), [_review("alice"), _review("bob")]) == {
        "allowed": True, "reason": "approved", "approvals": 2, "required": 2}


def test_tenant_boundaries_reject_forged_membership_and_events():
    actors = _actors() + [_actor("outsider", tenant_id="tenant-b")]
    for wrong_review in (_review("outsider"), _review("bob", tenant_id="tenant-b")):
        assert evaluate_change(_change(), actors, [_review("alice"), wrong_review]) == {
            "allowed": False, "reason": "insufficient_approvals", "approvals": 1, "required": 2}
    actors[0] = _actor("author", tenant_id="tenant-b", role="admin")
    assert evaluate_change(_change(), actors, [_review("alice"), _review("bob")]) == {
        "allowed": False, "reason": "author_unavailable", "approvals": 0, "required": 2}


def test_inactive_revoked_and_member_actors_cannot_approve():
    for update in ({"active": False}, {"revoked": True}, {"role": "member"}):
        actors = _actors()
        actors[2] = _actor("bob", **update)
        assert evaluate_change(_change(), actors, [_review("alice"), _review("bob")]) == {
            "allowed": False, "reason": "insufficient_approvals", "approvals": 1, "required": 2}
    assert evaluate_change(_change(), _actors(), [_review("alice"), _review("missing")]) == {
        "allowed": False, "reason": "insufficient_approvals", "approvals": 1, "required": 2}


def test_author_self_approval_is_denied_even_for_admin():
    assert evaluate_change(_change(), _actors(), [_review("author"), _review("alice")]) == {
        "allowed": False, "reason": "insufficient_approvals", "approvals": 1, "required": 2}


def test_quorum_counts_distinct_reviewers_at_each_threshold():
    repeated = [_review("alice"), _review("alice", sequence=2)]
    assert evaluate_change(_change(), _actors(), repeated) == {
        "allowed": False, "reason": "insufficient_approvals", "approvals": 1, "required": 2}
    assert evaluate_change(_change(required_approvals=1), _actors(), repeated) == {
        "allowed": True, "reason": "approved", "approvals": 1, "required": 1}
    pair = [_review("alice"), _review("bob")]
    assert evaluate_change(_change(required_approvals=3), _actors(), pair) == {
        "allowed": False, "reason": "insufficient_approvals", "approvals": 2, "required": 3}
    assert evaluate_change(_change(required_approvals=3), _actors(), pair + [_review("carol")]) == {
        "allowed": True, "reason": "approved", "approvals": 3, "required": 3}


def test_stale_and_unrelated_reviews_do_not_authorize_or_veto():
    for wrong_review in (_review("bob", head="rev-1"), _review("bob", change_id="other-change")):
        assert evaluate_change(_change(), _actors(), [_review("alice"), wrong_review]) == {
            "allowed": False, "reason": "insufficient_approvals", "approvals": 1, "required": 2}
    reviews = [_review("alice"), _review("bob"),
               _review("alice", head="rev-1", decision="request_changes", sequence=9)]
    assert evaluate_change(_change(), _actors(), reviews) == {
        "allowed": True, "reason": "approved", "approvals": 2, "required": 2}


def test_current_request_changes_blocks_an_otherwise_satisfied_quorum():
    reviews = [_review("alice"), _review("bob"), _review("carol", decision="request_changes")]
    assert evaluate_change(_change(), _actors(), reviews) == {
        "allowed": False, "reason": "changes_requested", "approvals": 2, "required": 2}


def test_latest_current_decision_can_withdraw_or_replace_a_review():
    base = [_review("alice"), _review("bob")]
    assert evaluate_change(_change(), _actors(), base + [_review("alice", sequence=2, decision="withdraw")]) == {
        "allowed": False, "reason": "insufficient_approvals", "approvals": 1, "required": 2}
    for earlier in ("request_changes", "withdraw"):
        reviews = [_review("alice", decision=earlier), _review("alice", sequence=2), _review("bob")]
        assert evaluate_change(_change(), _actors(), reviews) == {
            "allowed": True, "reason": "approved", "approvals": 2, "required": 2}


def test_request_must_be_open_and_author_currently_available():
    for status in ("draft", "closed", "merged"):
        assert evaluate_change(_change(status=status), _actors(), [_review("alice"), _review("bob")]) == {
            "allowed": False, "reason": "change_not_open", "approvals": 0, "required": 2}
    for actors in (_actors()[1:], [_actor("author", active=False), *_actors()[1:]],
                   [_actor("author", revoked=True), *_actors()[1:]]):
        assert evaluate_change(_change(), actors, [_review("alice"), _review("bob")]) == {
            "allowed": False, "reason": "author_unavailable", "approvals": 0, "required": 2}


def test_unknown_statuses_and_malformed_records_fail_closed():
    good_reviews = [_review("alice"), _review("bob")]
    cases = [(_change(status="approved_elsewhere"), _actors(), good_reviews),
             (_change(status=[]), _actors(), good_reviews),
             (_change(extra=True), _actors(), good_reviews),
             (_change(), _actors(), [_review("alice", decision="unknown")]),
             (_change(), _actors(), [_review("alice", sequence=True)]),
             (_change(), _actors(), [_review("alice", sequence=0)]),
             (_change(), _actors(), [_review("alice"), _review("alice", decision="withdraw")]),
             (_change(), _actors() + [_actor("alice", tenant_id="tenant-b")], good_reviews),
             (_change(), [_actor("author", role="superuser")], good_reviews),
             (_change(), _actors(), None)]
    for quorum in (0, 4, True, "2"):
        cases.append((_change(required_approvals=quorum), _actors(), good_reviews))
    missing_field = _review("alice")
    del missing_field["head"]
    cases.append((_change(), _actors(), [missing_field]))
    for change, actors, reviews in cases:
        assert evaluate_change(change, actors, reviews) == {
            "allowed": False, "reason": "invalid_input", "approvals": 0, "required": 0}


def test_sequence_numbers_control_decisions_independently_of_list_order():
    reviews = [_review("alice", sequence=4), _review("alice", decision="request_changes", sequence=2),
               _review("bob")]
    expected = {"allowed": True, "reason": "approved", "approvals": 2, "required": 2}
    assert evaluate_change(_change(), _actors(), reviews) == expected
    assert evaluate_change(_change(), list(reversed(_actors())), list(reversed(reviews))) == expected
