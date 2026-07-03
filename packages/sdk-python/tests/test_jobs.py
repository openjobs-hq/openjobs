"""Unit tests for JobsApi — covers all ~33 public methods."""
from __future__ import annotations

import json

from .conftest import make_client


def mk(body=None):
    c, t = make_client(body=body or {})
    return c, t


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_default():
    c, t = mk({"jobs": []})
    result = c.jobs.list()
    assert result["jobs"] == []
    assert t.last.method == "GET"
    assert "/api/v1/jobs" in str(t.last.url)


def test_list_status_filter():
    c, t = mk()
    c.jobs.list(status="open")
    assert "status=open" in str(t.last.url)


def test_list_limit():
    c, t = mk()
    c.jobs.list(limit=50)
    assert "limit=50" in str(t.last.url)


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

def test_search():
    c, t = mk({"jobs": []})
    c.jobs.search(q="data analysis")
    assert "jobs/search" in str(t.last.url)
    assert "data" in str(t.last.url)


def test_search_with_skills():
    c, t = mk()
    c.jobs.search(skills=["python", "ml"])
    url = str(t.last.url)
    assert "python" in url


def test_search_with_budget():
    c, t = mk()
    c.jobs.search(min_reward=10, max_reward=500)
    url = str(t.last.url)
    assert "minReward=10" in url or "min_reward=10" in url


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

def test_get():
    c, t = mk({"id": "job_1", "title": "Parse HTML"})
    result = c.jobs.get("job_1")
    assert result["id"] == "job_1"
    assert "jobs/job_1" in str(t.last.url)


def test_get_status():
    c, t = mk({"status": "open"})
    c.jobs.status("job_1")
    assert "jobs/job_1/status" in str(t.last.url)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create():
    c, t = mk({"id": "job_new"})
    result = c.jobs.create(
        title="Scrape site",
        description="Scrape 1000 pages",
        reward=50,
        required_skills=["scraping"],
    )
    assert result["id"] == "job_new"
    assert t.last.method == "POST"
    body = json.loads(t.last.content)
    assert body["title"] == "Scrape site"


def test_create_fields_in_body():
    # create(**fields) forwards kwargs to the JSON body directly
    c, t = mk()
    c.jobs.create(title="x", description="y", reward=5, required_skills=["python"])
    body = json.loads(t.last.content)
    assert body["title"] == "x"
    assert body["reward"] == 5
    assert body["required_skills"] == ["python"]


# ---------------------------------------------------------------------------
# create_from_template
# ---------------------------------------------------------------------------

def test_create_from_template():
    c, t = mk({"id": "job_tmpl"})
    c.jobs.create_from_template("seo-audit", title="Audit my site")
    assert t.last.method == "POST"
    assert "jobs/from-template/seo-audit" in str(t.last.url)


# ---------------------------------------------------------------------------
# suggest
# ---------------------------------------------------------------------------

def test_suggest():
    c, t = mk({"title": "Analyze data"})
    c.jobs.suggest(description="I need help with analysis")
    assert t.last.method == "POST"
    assert "jobs/suggest" in str(t.last.url)
    body = json.loads(t.last.content)
    assert "analysis" in body["description"]


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update():
    c, t = mk({"id": "job_1"})
    c.jobs.update("job_1", title="New Title")
    assert t.last.method == "PATCH"
    assert "jobs/job_1" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["title"] == "New Title"


# ---------------------------------------------------------------------------
# cancel
# ---------------------------------------------------------------------------

def test_cancel():
    c, t = mk({"ok": True})
    c.jobs.cancel("job_1")
    assert t.last.method == "DELETE"
    assert "jobs/job_1" in str(t.last.url)


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------

def test_apply():
    c, t = mk({"applicationId": "app_1"})
    result = c.jobs.apply("job_1", cover_letter="Pick me")
    assert result["applicationId"] == "app_1"
    assert t.last.method == "POST"
    assert "jobs/job_1/apply" in str(t.last.url)
    body = json.loads(t.last.content)
    # Python SDK passes **fields directly; snake_case keys are sent as-is
    assert body.get("cover_letter") == "Pick me"


def test_apply_with_attachments():
    c, t = mk()
    c.jobs.apply("job_1", cover_letter="Hi", attachment_ids=["att_1"])
    body = json.loads(t.last.content)
    # Python SDK forwards **fields as-is (snake_case)
    assert "att_1" in body.get("attachment_ids", [])


# ---------------------------------------------------------------------------
# withdraw_application
# ---------------------------------------------------------------------------

def test_withdraw_application():
    c, t = mk()
    c.jobs.withdraw_application("job_1")
    assert t.last.method == "DELETE"
    assert "jobs/job_1/apply" in str(t.last.url)


# ---------------------------------------------------------------------------
# submit
# ---------------------------------------------------------------------------

def test_submit():
    c, t = mk({"submissionId": "sub_1"})
    result = c.jobs.submit("job_1", deliverable="https://example.com/result")
    assert result["submissionId"] == "sub_1"
    assert t.last.method == "POST"
    assert "jobs/job_1/submit" in str(t.last.url)


def test_submit_with_attachments():
    c, t = mk()
    c.jobs.submit("job_1", deliverable="url", attachment_ids=["att_2"])
    body = json.loads(t.last.content)
    # Python SDK forwards **fields as-is (snake_case)
    assert "att_2" in body.get("attachment_ids", [])


# ---------------------------------------------------------------------------
# mine / match
# ---------------------------------------------------------------------------

def test_mine():
    c, t = mk({"jobs": []})
    c.jobs.mine(status="active")
    assert "jobs/mine" in str(t.last.url)
    assert "status=active" in str(t.last.url)


def test_match():
    c, t = mk({"jobs": [], "scores": []})
    c.jobs.match(limit=10, min_score=80)
    assert "jobs/match" in str(t.last.url)
    url = str(t.last.url)
    assert "limit=10" in url


# ---------------------------------------------------------------------------
# applications / accept / reject
# ---------------------------------------------------------------------------

def test_applications():
    c, t = mk({"applications": []})
    c.jobs.applications("job_1")
    assert "jobs/job_1/applications" in str(t.last.url)


def test_accept():
    c, t = mk({"ok": True})
    c.jobs.accept("job_1", worker_id="agent_2")
    assert t.last.method == "PATCH"
    assert "jobs/job_1/accept" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body.get("workerId") == "agent_2"


def test_accept_with_attachments():
    c, t = mk()
    c.jobs.accept("job_1", worker_id="agent_2", attachment_ids=["att_1"])
    body = json.loads(t.last.content)
    assert "att_1" in body.get("attachmentIds", [])


def test_reject_application():
    c, t = mk()
    c.jobs.reject("job_1", reason="Not a fit", application_id="app_1")
    assert t.last.method == "POST"
    assert "jobs/job_1/reject" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["reason"] == "Not a fit"


# ---------------------------------------------------------------------------
# submissions / complete / request_revision / reject_submission
# ---------------------------------------------------------------------------

def test_submissions():
    c, t = mk({"submissions": []})
    c.jobs.submissions("job_1")
    assert "jobs/job_1/submissions" in str(t.last.url)


def test_complete():
    c, t = mk({"ok": True})
    c.jobs.complete("job_1")
    assert t.last.method == "PATCH"
    assert "jobs/job_1/complete" in str(t.last.url)


def test_complete_with_attachments():
    c, t = mk()
    c.jobs.complete("job_1", attachment_ids=["att_review"])
    body = json.loads(t.last.content)
    assert "att_review" in body.get("attachmentIds", [])


def test_request_revision():
    c, t = mk()
    c.jobs.request_revision("job_1", notes="Please fix the format")
    assert t.last.method == "POST"
    assert "jobs/job_1/request-revision" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["notes"] == "Please fix the format"


def test_reject_submission():
    c, t = mk()
    c.jobs.reject_submission("job_1", reason="Incomplete")
    assert t.last.method == "POST"
    assert "jobs/job_1/reject-submission" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["reason"] == "Incomplete"


# ---------------------------------------------------------------------------
# dispute
# ---------------------------------------------------------------------------

def test_dispute():
    c, t = mk({"id": "dispute_1"})
    c.jobs.dispute("job_1", reason="Deliverable does not match spec at all.")
    assert t.last.method == "POST"
    assert "/api/v1/jobs/job_1/dispute" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["reason"] == "Deliverable does not match spec at all."


def test_dispute_with_attachments():
    c, t = mk({"id": "dispute_2"})
    c.jobs.dispute("job_1", reason="Work was not delivered as agreed.", attachment_ids=["att_1", "att_2"])
    body = json.loads(t.last.content)
    assert body["attachmentIds"] == ["att_1", "att_2"]


def test_dispute_short_reason_raises_api_error():
    from openjobs import OpenJobsApiError
    import pytest
    c, _ = make_client(
        status_code=422,
        body={"error": "reason must be at least 10 characters"},
    )
    with pytest.raises(OpenJobsApiError) as exc_info:
        c.jobs.dispute("job_1", reason="short")
    assert exc_info.value.status == 422


# ---------------------------------------------------------------------------
# messages
# ---------------------------------------------------------------------------

def test_message_post():
    c, t = mk({"id": "msg_1"})
    c.jobs.message("job_1", content="Hi there")
    assert t.last.method == "POST"
    assert "jobs/job_1/messages" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["content"] == "Hi there"


def test_messages_list():
    c, t = mk({"messages": []})
    c.jobs.messages("job_1", limit=20)
    assert t.last.method == "GET"
    assert "jobs/job_1/messages" in str(t.last.url)


# ---------------------------------------------------------------------------
# workspace
# ---------------------------------------------------------------------------

def test_workspace():
    c, t = mk({"workspace": {}})
    c.jobs.workspace("job_1")
    assert "jobs/job_1/workspace" in str(t.last.url)


# ---------------------------------------------------------------------------
# proposals
# ---------------------------------------------------------------------------

def test_accept_proposal():
    c, t = mk({"ok": True})
    c.jobs.accept_proposal("job_1", "msg_1")
    assert t.last.method == "POST"
    assert "proposals/msg_1/accept" in str(t.last.url)


def test_decline_proposal():
    c, t = mk()
    c.jobs.decline_proposal("job_1", "msg_1", reason="Not right fit")
    assert t.last.method == "POST"
    assert "proposals/msg_1/decline" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body.get("reason") == "Not right fit"


# ---------------------------------------------------------------------------
# checkpoints
# ---------------------------------------------------------------------------

def test_checkpoint_create():
    c, t = mk({"id": "cp_1"})
    c.jobs.checkpoint("job_1", label="Draft done", content="Initial draft complete")
    assert t.last.method == "POST"
    assert "checkpoints" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["label"] == "Draft done"


def test_checkpoints_list():
    c, t = mk({"checkpoints": []})
    c.jobs.checkpoints("job_1")
    assert t.last.method == "GET"
    assert "checkpoints" in str(t.last.url)


def test_checkpoint_review():
    c, t = mk({"ok": True})
    c.jobs.checkpoint_review("job_1", "cp_1", status="approved")
    assert t.last.method == "PATCH"
    assert "checkpoints/cp_1" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["status"] == "approved"


# ---------------------------------------------------------------------------
# review / reviews / boost
# ---------------------------------------------------------------------------

def test_review():
    c, t = mk({"id": "rv_1"})
    c.jobs.review("job_1", rating=5, comment="Great work!")
    assert t.last.method == "POST"
    assert "jobs/job_1/reviews" in str(t.last.url)
    body = json.loads(t.last.content)
    assert body["rating"] == 5


def test_reviews():
    c, t = mk({"reviews": []})
    c.jobs.reviews("job_1")
    assert t.last.method == "GET"
    assert "jobs/job_1/reviews" in str(t.last.url)


def test_boost():
    c, t = mk({"ok": True})
    c.jobs.boost("job_1")
    assert t.last.method == "POST"
    assert "jobs/job_1/boost" in str(t.last.url)
