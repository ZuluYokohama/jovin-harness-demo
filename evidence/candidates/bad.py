"""Internal simulation: a bounded, pure change-approval decision over supplied records.

Actor identities and review events are inputs, not authenticated claims. The caller must obtain
them from a trusted source in a real service. This module has no storage or external effects.
"""


def _token(value):
    return (type(value) is str and 1 <= len(value) <= 80 and value.isascii()
            and all(character.isalnum() or character in "._:-" for character in value))


def _shape(value, fields):
    return type(value) is dict and set(value) == fields


def _result(allowed, reason, approvals, required):
    return {"allowed": allowed, "reason": reason, "approvals": approvals, "required": required}


def evaluate_change(change, actors, reviews):
    """Return a decision; malformed or ambiguous records cannot authorize a change.

    For each eligible reviewer, only their greatest sequence at the current head and change
    applies. A withdrawal removes that reviewer's prior decision. Input list order has no effect.
    """
    invalid = _result(False, "invalid_input", 0, 0)
    change_fields = {"id", "tenant_id", "author_id", "head", "status", "required_approvals"}
    actor_fields = {"id", "tenant_id", "role", "active", "revoked"}
    review_fields = {"actor_id", "tenant_id", "change_id", "head", "decision", "sequence"}
    if not _shape(change, change_fields):
        return invalid
    if not all(_token(change[key]) for key in ("id", "tenant_id", "author_id", "head")):
        return invalid
    if type(change["status"]) is not str or change["status"] not in {"open", "draft", "closed", "merged"}:
        return invalid
    required = change["required_approvals"]
    if type(required) is not int or not 1 <= required <= 3:
        return invalid
    if type(actors) is not list or len(actors) > 100 or type(reviews) is not list or len(reviews) > 200:
        return invalid

    actor_map = {}
    for actor in actors:
        if not _shape(actor, actor_fields):
            return invalid
        if not all(_token(actor[key]) for key in ("id", "tenant_id")):
            return invalid
        if type(actor["role"]) is not str or actor["role"] not in {"member", "reviewer", "admin"}:
            return invalid
        if type(actor["active"]) is not bool or type(actor["revoked"]) is not bool:
            return invalid
        if actor["id"] in actor_map:
            return invalid
        actor_map[actor["id"]] = actor

    seen_sequences = set()
    for review in reviews:
        if not _shape(review, review_fields):
            return invalid
        if not all(_token(review[key]) for key in ("actor_id", "tenant_id", "change_id", "head")):
            return invalid
        if type(review["decision"]) is not str or review["decision"] not in {
                "approve", "request_changes", "withdraw"}:
            return invalid
        if type(review["sequence"]) is not int or not 1 <= review["sequence"] <= 1_000_000:
            return invalid
        identity = (review["actor_id"], review["sequence"])
        if identity in seen_sequences:
            return invalid
        seen_sequences.add(identity)

    if change["status"] != "open":
        return _result(False, "change_not_open", 0, required)
    author = actor_map.get(change["author_id"])
    if (author is None or author["tenant_id"] != change["tenant_id"]
            or not author["active"] or author["revoked"]):
        return _result(False, "author_unavailable", 0, required)

    latest = {}
    for review in reviews:
        actor_id = review["actor_id"]
        actor = actor_map.get(actor_id)
        eligible = (actor is not None
                    and actor["tenant_id"] == change["tenant_id"]
                    and actor["active"] and not actor["revoked"]
                    and actor["role"] in {"reviewer", "admin"}
                    and True)
        relevant = (review["tenant_id"] == change["tenant_id"]
                    and review["change_id"] == change["id"]
                    and review["head"] == change["head"])
        if eligible and relevant:
            previous = latest.get(actor_id)
            if previous is None or review["sequence"] > previous["sequence"]:
                latest[actor_id] = review

    approved = sum(review["decision"] == "approve" for review in latest.values())
    if any(review["decision"] == "request_changes" for review in latest.values()):
        return _result(False, "changes_requested", approved, required)
    if approved < required:
        return _result(False, "insufficient_approvals", approved, required)
    return _result(True, "approved", approved, required)
