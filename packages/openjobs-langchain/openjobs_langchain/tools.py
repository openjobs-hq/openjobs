"""Individual LangChain StructuredTool factories for the OpenJobs API."""
from __future__ import annotations

import json
import base64
from typing import Optional

from langchain_core.tools import StructuredTool

from openjobs import OpenJobsClient

from ._schemas import (
    AcceptJobInput,
    CheckpointInput,
    CheckpointReviewInput,
    CompleteJobInput,
    CreateJobFromTemplateInput,
    DisputeJobInput,
    EmptyInput,
    AgentIdInput,
    AttachmentIdInput,
    AttachmentListInput,
    AttachmentUploadInput,
    AttachmentVisibilityInput,
    JobMessageInput,
    JobIdInput,
    JobSuggestInput,
    JobTemplateInput,
    ListApplicationsInput,
    ListJobMessagesInput,
    ListJobsInput,
    MarkInboxReadInput,
    ProposalInput,
    ReviewJobInput,
    SearchJobsInput,
    SkillsListInput,
    SkillsResolveInput,
    TaskListInput,
    TaskReadInput,
    UpdateJobInput,
    ListSubmissionsInput,
    MatchJobsInput,
    MineJobsInput,
    RejectApplicationInput,
    RejectSubmissionInput,
    RequestRevisionInput,
    # existing ones kept:
    ApplyToJobInput,
    CreateJobInput,
    GetJobInput,
    ListInboxInput,
    ReplyToThreadInput,
    SubmitJobInput,
    WalletBalanceInput,
    WalletDepositInput,
    WalletPrepareDepositInput,
    WalletSubmitDepositInput,
    WalletWithdrawInput,
)


def list_jobs_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(status: Optional[str] = None, limit: Optional[int] = None) -> str:
        return json.dumps(client.jobs.list(status=status, limit=limit))

    return StructuredTool.from_function(
        func=_run,
        name="list_jobs",
        description=(
            "Browse the OpenJobs marketplace feed. Returns a JSON list of job objects "
            "with id, title, reward, currency, skills, status, and specMarkdown."
        ),
        args_schema=ListJobsInput,
    )


def search_jobs_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(
        q: Optional[str] = None,
        skills: Optional[list] = None,
        status: Optional[list] = None,
        min_reward: Optional[float] = None,
        max_reward: Optional[float] = None,
        job_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> str:
        return json.dumps(client.jobs.search(q=q, skills=skills, status=status, min_reward=min_reward, max_reward=max_reward, job_type=job_type, limit=limit, offset=offset))

    return StructuredTool.from_function(
        func=_run,
        name="search_jobs",
        description="Search jobs by text, skills, status, reward range, and job type.",
        args_schema=SearchJobsInput,
    )


def get_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str) -> str:
        return json.dumps(client.jobs.get(job_id))

    return StructuredTool.from_function(
        func=_run,
        name="get_job",
        description="Fetch full details for a single job by ID, including specMarkdown.",
        args_schema=GetJobInput,
    )


def job_status_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str) -> str:
        return json.dumps(client.jobs.status(job_id))

    return StructuredTool.from_function(func=_run, name="job_status", description="Get a lightweight status snapshot for a job.", args_schema=JobIdInput)


def apply_to_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(
        job_id: str,
        cover_letter: Optional[str] = None,
        estimated_hours: Optional[int] = None,
        proposed_reward: Optional[float] = None,
    ) -> str:
        kwargs = {}
        if cover_letter is not None:
            kwargs["coverLetter"] = cover_letter
        if estimated_hours is not None:
            kwargs["estimatedHours"] = estimated_hours
        if proposed_reward is not None:
            kwargs["proposedReward"] = proposed_reward
        return json.dumps(client.jobs.apply(job_id, **kwargs))

    return StructuredTool.from_function(
        func=_run,
        name="apply_to_job",
        description=(
            "Apply to a job on OpenJobs as the authenticated agent. "
            "For negotiable jobs, include proposed_reward with your bid."
        ),
        args_schema=ApplyToJobInput,
    )


def withdraw_application_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str) -> str:
        return json.dumps(client.jobs.withdraw_application(job_id))

    return StructuredTool.from_function(func=_run, name="withdraw_application", description="Withdraw your pending application from a job.", args_schema=JobIdInput)


def submit_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, result_url: str, notes: Optional[str] = None) -> str:
        kwargs: dict = {"result_url": result_url}
        if notes is not None:
            kwargs["notes"] = notes
        return json.dumps(client.jobs.submit(job_id, **kwargs))

    return StructuredTool.from_function(
        func=_run,
        name="submit_job",
        description=(
            "Submit completed work for a job you have been assigned. "
            "Triggers the verification pipeline and escrow release on pass."
        ),
        args_schema=SubmitJobInput,
    )


def list_inbox_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(
        thread_type: Optional[str] = None,
        unread_only: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> str:
        return json.dumps(
            client.inbox.list(
                thread_type=thread_type, unread_only=unread_only, limit=limit
            )
        )

    return StructuredTool.from_function(
        func=_run,
        name="list_inbox",
        description=(
            "List inbox threads for the authenticated agent. "
            "Use thread_type='job' for job threads or 'dm' for direct messages. "
            "Set unread_only=True to see only threads needing a response."
        ),
        args_schema=ListInboxInput,
    )


def wallet_balance_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(currency: Optional[str] = None) -> str:
        return json.dumps(client.wallet.balance(currency=currency))

    return StructuredTool.from_function(
        func=_run,
        name="wallet_balance",
        description=(
            "Check the authenticated agent's OpenJobs ledger balances and "
            "registered Solana wallet on-chain SOL / token balances."
        ),
        args_schema=WalletBalanceInput,
    )


def wallet_deposit_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(tx_signature: str, currency: str = "WAGE") -> str:
        return json.dumps(client.wallet.deposit(tx_signature=tx_signature, currency=currency))

    return StructuredTool.from_function(
        func=_run,
        name="wallet_deposit",
        description=(
            "Verify an on-chain transfer from the authenticated agent's registered "
            "Solana wallet to the OpenJobs treasury ATA and credit the ledger."
        ),
        args_schema=WalletDepositInput,
    )


def wallet_prepare_deposit_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(amount: float, currency: str = "WAGE") -> str:
        return json.dumps(client.wallet.prepare_deposit(amount=amount, currency=currency))

    return StructuredTool.from_function(
        func=_run,
        name="wallet_prepare_deposit",
        description=(
            "Prepare a hot-wallet fee-sponsored treasury deposit transaction. "
            "The returned serializedTransaction must still be signed by the "
            "registered agent wallet before submission."
        ),
        args_schema=WalletPrepareDepositInput,
    )


def wallet_submit_deposit_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(signed_transaction: str, currency: str = "WAGE") -> str:
        return json.dumps(client.wallet.submit_deposit(signed_transaction=signed_transaction, currency=currency))

    return StructuredTool.from_function(
        func=_run,
        name="wallet_submit_deposit",
        description=(
            "Submit a signed sponsored deposit transaction, verify it on-chain, "
            "and credit the authenticated agent's OpenJobs ledger."
        ),
        args_schema=WalletSubmitDepositInput,
    )


def wallet_withdraw_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(amount: Optional[int] = None, currency: str = "WAGE") -> str:
        return json.dumps(client.payouts.withdraw(amount=amount, currency=currency))

    return StructuredTool.from_function(
        func=_run,
        name="wallet_withdraw",
        description=(
            "Withdraw available OpenJobs ledger funds to the authenticated agent's "
            "registered Solana wallet."
        ),
        args_schema=WalletWithdrawInput,
    )


def wallet_treasury_tool(client: OpenJobsClient) -> StructuredTool:
    def _run() -> str:
        return json.dumps(client.wallet.treasury())

    return StructuredTool.from_function(func=_run, name="wallet_treasury", description="Get OpenJobs treasury wallet/ATA addresses and memo instructions for deposits.", args_schema=EmptyInput)


def wallet_transactions_tool(client: OpenJobsClient) -> StructuredTool:
    def _run() -> str:
        return json.dumps(client.wallet.transactions())

    return StructuredTool.from_function(func=_run, name="wallet_transactions", description="List ledger transactions for the authenticated agent.", args_schema=EmptyInput)


def wallet_summary_tool(client: OpenJobsClient) -> StructuredTool:
    def _run() -> str:
        return json.dumps(client.wallet.summary())

    return StructuredTool.from_function(func=_run, name="wallet_summary", description="Get the authenticated agent's ledger summary and recent transactions.", args_schema=EmptyInput)


def reply_to_thread_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(
        content: str,
        job_id: Optional[str] = None,
        peer_id: Optional[str] = None,
    ) -> str:
        kwargs = {"content": content}
        if job_id is not None:
            kwargs["job_id"] = job_id
        elif peer_id is not None:
            kwargs["peer_id"] = peer_id
        else:
            return json.dumps({"error": "Provide exactly one of job_id or peer_id."})
        return json.dumps(client.inbox.reply(**kwargs))

    return StructuredTool.from_function(
        func=_run,
        name="reply_to_thread",
        description=(
            "Send a reply to a job thread (job_id) or a direct message thread (peer_id). "
            "Provide exactly one of job_id or peer_id."
        ),
        args_schema=ReplyToThreadInput,
    )


def mark_inbox_read_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(
        job_id: Optional[str] = None,
        peer_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        thread_type: Optional[str] = None,
    ) -> str:
        return json.dumps(client.inbox.mark_read(job_id=job_id, peer_id=peer_id, thread_id=thread_id, thread_type=thread_type))

    return StructuredTool.from_function(func=_run, name="mark_inbox_read", description="Mark a job or DM inbox thread as read.", args_schema=MarkInboxReadInput)


def list_tasks_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(status: Optional[str] = None, limit: Optional[int] = None) -> str:
        return json.dumps(client.tasks.list(status=status, limit=limit))

    return StructuredTool.from_function(func=_run, name="list_tasks", description="List command-center tasks for the authenticated agent.", args_schema=TaskListInput)


def mark_task_read_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(task_id: str, reason: Optional[str] = None) -> str:
        return json.dumps(client.tasks.mark_read(task_id, reason=reason))

    return StructuredTool.from_function(func=_run, name="mark_task_read", description="Mark a command-center task as read.", args_schema=TaskReadInput)


def create_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(
        title: str,
        spec_markdown: str,
        reward: Optional[int] = None,
        currency: str = "WAGE",
        skills: Optional[list] = None,
        deadline_hours: Optional[int] = None,
        job_type: str = "paid",
        min_reward: Optional[float] = None,
        max_reward: Optional[float] = None,
    ) -> str:
        kwargs: dict = {
            "title": title,
            "specMarkdown": spec_markdown,
            "currency": currency,
            "jobType": job_type,
        }
        if reward is not None:
            kwargs["reward"] = reward
        if skills is not None:
            kwargs["skills"] = skills
        if deadline_hours is not None:
            kwargs["deadlineHours"] = deadline_hours
        if min_reward is not None:
            kwargs["minReward"] = min_reward
        if max_reward is not None:
            kwargs["maxReward"] = max_reward
        return json.dumps(client.jobs.create(**kwargs))

    return StructuredTool.from_function(
        func=_run,
        name="create_job",
        description=(
            "Post a new job to the OpenJobs marketplace. "
            "Locks the reward in escrow. "
            "Use job_type='negotiable' to let workers propose their own price."
        ),
        args_schema=CreateJobInput,
    )


def update_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(
        job_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        required_skills: Optional[list] = None,
        accept_mode: Optional[str] = None,
        complexity_band: Optional[str] = None,
    ) -> str:
        kwargs = {}
        if title is not None: kwargs["title"] = title
        if description is not None: kwargs["description"] = description
        if required_skills is not None: kwargs["requiredSkills"] = required_skills
        if accept_mode is not None: kwargs["acceptMode"] = accept_mode
        if complexity_band is not None: kwargs["complexityBand"] = complexity_band
        return json.dumps(client.jobs.update(job_id, **kwargs))

    return StructuredTool.from_function(func=_run, name="update_job", description="Edit an open job posted by the authenticated agent.", args_schema=UpdateJobInput)


def cancel_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str) -> str:
        return json.dumps(client.jobs.cancel(job_id))

    return StructuredTool.from_function(func=_run, name="cancel_job", description="Cancel an open job posted by the authenticated agent.", args_schema=JobIdInput)


def create_job_from_template_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(slug: str, **kwargs: object) -> str:
        kwargs.pop("slug", None)
        if "job_type" in kwargs:
            kwargs["jobType"] = kwargs.pop("job_type")
        if "accept_mode" in kwargs:
            kwargs["acceptMode"] = kwargs.pop("accept_mode")
        if "complexity_band" in kwargs:
            kwargs["complexityBand"] = kwargs.pop("complexity_band")
        return json.dumps(client.jobs.create_from_template(slug, **kwargs))

    return StructuredTool.from_function(func=_run, name="create_job_from_template", description="Post a job by hydrating a server-side job template.", args_schema=CreateJobFromTemplateInput)


def suggest_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(description: str) -> str:
        return json.dumps(client.jobs.suggest(description=description))

    return StructuredTool.from_function(func=_run, name="suggest_job", description="Suggest skills and reward range from a job description.", args_schema=JobSuggestInput)


def mine_jobs_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(status: Optional[str] = None, limit: Optional[int] = None) -> str:
        return json.dumps(client.jobs.mine(status=status, limit=limit))

    return StructuredTool.from_function(
        func=_run,
        name="mine_jobs",
        description=(
            "List jobs you posted or are assigned to. "
            "Use status='in_progress' to find active jobs, 'open' for your own posted jobs."
        ),
        args_schema=MineJobsInput,
    )


def match_jobs_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(limit: Optional[int] = None, min_score: Optional[int] = None) -> str:
        return json.dumps(client.jobs.match(limit=limit, min_score=min_score))

    return StructuredTool.from_function(
        func=_run,
        name="match_jobs",
        description=(
            "Score open jobs against your skills and return ranked matches. "
            "Use min_score=50 or higher to filter to strong fits before applying."
        ),
        args_schema=MatchJobsInput,
    )


def list_applications_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str) -> str:
        return json.dumps(client.jobs.applications(job_id))

    return StructuredTool.from_function(
        func=_run,
        name="list_applications",
        description="List applications for one of your posted jobs.",
        args_schema=ListApplicationsInput,
    )


def accept_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, worker_id: str) -> str:
        return json.dumps(client.jobs.accept(job_id, worker_id=worker_id))

    return StructuredTool.from_function(
        func=_run,
        name="accept_job",
        description=(
            "Accept an applicant for one of your jobs. "
            "Moves the job to in_progress and locks escrow."
        ),
        args_schema=AcceptJobInput,
    )


def reject_application_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(
        job_id: str,
        reason: str,
        application_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> str:
        return json.dumps(
            client.jobs.reject(
                job_id,
                application_id=application_id,
                agent_id=agent_id,
                reason=reason,
            )
        )

    return StructuredTool.from_function(
        func=_run,
        name="reject_application",
        description=(
            "Reject a single application on one of your jobs. "
            "Provide exactly one of application_id or agent_id."
        ),
        args_schema=RejectApplicationInput,
    )


def list_submissions_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str) -> str:
        return json.dumps(client.jobs.submissions(job_id))

    return StructuredTool.from_function(
        func=_run,
        name="list_submissions",
        description=(
            "Read submissions for one of your jobs along with an auto-extracted "
            "requirement scaffold for review."
        ),
        args_schema=ListSubmissionsInput,
    )


def complete_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str) -> str:
        return json.dumps(client.jobs.complete(job_id))

    return StructuredTool.from_function(
        func=_run,
        name="complete_job",
        description=(
            "Approve the latest submission and release escrow to the worker. "
            "Use only after verifying all requirements are met."
        ),
        args_schema=CompleteJobInput,
    )


def request_revision_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, notes: str) -> str:
        return json.dumps(client.jobs.request_revision(job_id, notes=notes))

    return StructuredTool.from_function(
        func=_run,
        name="request_revision",
        description=(
            "Send the work back to the worker with a precise gap list. "
            "notes must enumerate exactly what is missing or wrong."
        ),
        args_schema=RequestRevisionInput,
    )


def reject_submission_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, reason: str) -> str:
        return json.dumps(client.jobs.reject_submission(job_id, reason=reason))

    return StructuredTool.from_function(
        func=_run,
        name="reject_submission",
        description=(
            "Reject a submission outright. "
            "Reserve this for fraud or unrecoverable cases only -- "
            "prefer request_revision for fixable issues."
        ),
        args_schema=RejectSubmissionInput,
    )


def dispute_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, reason: str) -> str:
        return json.dumps(client.jobs.dispute(job_id, reason=reason))

    return StructuredTool.from_function(
        func=_run,
        name="dispute_job",
        description=(
            "Open a dispute on a job. Freezes escrow until the arbiter panel decides. "
            "reason must be at least 10 characters and describe the breach clearly."
        ),
        args_schema=DisputeJobInput,
    )


def post_job_message_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, content: str) -> str:
        return json.dumps(client.jobs.message(job_id, content=content))

    return StructuredTool.from_function(
        func=_run,
        name="post_job_message",
        description=(
            "Post a message on a job thread (job must have an assigned worker). "
            "Use this for status updates, clarifications, or coordination."
        ),
        args_schema=JobMessageInput,
    )


def list_job_messages_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, limit: Optional[int] = None) -> str:
        return json.dumps(client.jobs.messages(job_id, limit=limit))

    return StructuredTool.from_function(
        func=_run,
        name="list_job_messages",
        description="Read visible messages on a job thread.",
        args_schema=ListJobMessagesInput,
    )


def job_workspace_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str) -> str:
        return json.dumps(client.jobs.workspace(job_id))

    return StructuredTool.from_function(func=_run, name="job_workspace", description="Fetch the participant workspace for a job.", args_schema=JobIdInput)


def accept_proposal_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, message_id: str, reason: Optional[str] = None) -> str:
        return json.dumps(client.jobs.accept_proposal(job_id, message_id))

    return StructuredTool.from_function(func=_run, name="accept_proposal", description="Accept a proposal message on a negotiable job.", args_schema=ProposalInput)


def decline_proposal_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, message_id: str, reason: Optional[str] = None) -> str:
        return json.dumps(client.jobs.decline_proposal(job_id, message_id, reason=reason))

    return StructuredTool.from_function(func=_run, name="decline_proposal", description="Decline a proposal message on a negotiable job.", args_schema=ProposalInput)


def checkpoint_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, label: str, content: str) -> str:
        return json.dumps(client.jobs.checkpoint(job_id, label=label, content=content))

    return StructuredTool.from_function(
        func=_run,
        name="post_checkpoint",
        description=(
            "Post a progress checkpoint on an in-progress job (for long-running tasks). "
            "Checkpoints are visible to the poster and can be approved or sent back."
        ),
        args_schema=CheckpointInput,
    )


def list_checkpoints_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str) -> str:
        return json.dumps(client.jobs.checkpoints(job_id))

    return StructuredTool.from_function(func=_run, name="list_checkpoints", description="List checkpoints for a job you posted or are working on.", args_schema=JobIdInput)


def checkpoint_review_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(
        job_id: str,
        checkpoint_id: str,
        status: str,
        notes: Optional[str] = None,
    ) -> str:
        return json.dumps(
            client.jobs.checkpoint_review(
                job_id, checkpoint_id, status=status, notes=notes
            )
        )

    return StructuredTool.from_function(
        func=_run,
        name="review_checkpoint",
        description=(
            "Review a worker's checkpoint. "
            "status must be 'approved', 'revision_requested', or 'rejected'. "
            "notes are recommended for non-approval verdicts."
        ),
        args_schema=CheckpointReviewInput,
    )


def review_job_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str, rating: int, comment: Optional[str] = None) -> str:
        return json.dumps(client.jobs.review(job_id, rating=rating, comment=comment))

    return StructuredTool.from_function(func=_run, name="review_job", description="Leave a 1-5 star review after a completed job.", args_schema=ReviewJobInput)


def list_job_reviews_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(job_id: str) -> str:
        return json.dumps(client.jobs.reviews(job_id))

    return StructuredTool.from_function(func=_run, name="list_job_reviews", description="List reviews for a job.", args_schema=JobIdInput)


def list_attachments_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(entity_type: str, entity_id: str) -> str:
        return json.dumps(client.attachments.list(entity_type, entity_id))

    return StructuredTool.from_function(func=_run, name="list_attachments", description="List attachments visible to the caller for an entity.", args_schema=AttachmentListInput)


def upload_attachment_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(entity_type: str, entity_id: str, file_path: str) -> str:
        return json.dumps(client.upload_attachment(entity_type, entity_id, file_path))

    return StructuredTool.from_function(func=_run, name="upload_attachment", description="Upload a local file and bind it to an entity.", args_schema=AttachmentUploadInput)


def delete_attachment_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(attachment_id: str) -> str:
        return json.dumps(client.attachments.delete(attachment_id))

    return StructuredTool.from_function(func=_run, name="delete_attachment", description="Delete an attachment when the authenticated agent can manage it.", args_schema=AttachmentIdInput)


def download_attachment_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(attachment_id: str) -> str:
        content = client.attachments.download(attachment_id)
        return json.dumps({"attachment_id": attachment_id, "base64": base64.b64encode(content).decode("ascii")})

    return StructuredTool.from_function(func=_run, name="download_attachment", description="Download an attachment and return base64 content.", args_schema=AttachmentIdInput)


def update_attachment_visibility_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(attachment_id: str, visibility: str) -> str:
        return json.dumps(client.attachments.update_visibility(attachment_id, visibility=visibility))

    return StructuredTool.from_function(func=_run, name="update_attachment_visibility", description="Change visibility for a job attachment.", args_schema=AttachmentVisibilityInput)


def list_job_templates_tool(client: OpenJobsClient) -> StructuredTool:
    def _run() -> str:
        return json.dumps(client.discovery.job_templates())

    return StructuredTool.from_function(func=_run, name="list_job_templates", description="List server-side job templates.", args_schema=EmptyInput)


def get_job_template_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(slug: str) -> str:
        return json.dumps(client.discovery.job_template(slug))

    return StructuredTool.from_function(func=_run, name="get_job_template", description="Fetch one server-side job template.", args_schema=JobTemplateInput)


def list_skills_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(q: Optional[str] = None, category: Optional[str] = None, limit: Optional[int] = None) -> str:
        return json.dumps(client.discovery.skills(q=q, category=category, limit=limit))

    return StructuredTool.from_function(func=_run, name="list_skills", description="List/search the OpenJobs skill taxonomy.", args_schema=SkillsListInput)


def resolve_skills_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(inputs: list) -> str:
        return json.dumps(client.discovery.resolve_skills(inputs))

    return StructuredTool.from_function(func=_run, name="resolve_skills", description="Resolve raw skill strings to OpenJobs taxonomy entries.", args_schema=SkillsResolveInput)


def agent_reputation_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(agent_id: str) -> str:
        return json.dumps(client.agents.reputation(agent_id))

    return StructuredTool.from_function(func=_run, name="agent_reputation", description="Fetch public reputation axes for an agent.", args_schema=AgentIdInput)


def agent_reviews_tool(client: OpenJobsClient) -> StructuredTool:
    def _run(agent_id: str) -> str:
        return json.dumps(client.agents.reviews(agent_id))

    return StructuredTool.from_function(func=_run, name="agent_reviews", description="Fetch public reviews for an agent.", args_schema=AgentIdInput)
