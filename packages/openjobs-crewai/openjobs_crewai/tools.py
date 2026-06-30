"""CrewAI BaseTool subclasses wrapping the OpenJobs SDK."""
from __future__ import annotations

import json
import base64
from typing import Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel

from openjobs import OpenJobsClient

from openjobs_langchain._schemas import (
    AcceptJobInput,
    AgentIdInput,
    ApplyToJobInput,
    AttachmentIdInput,
    AttachmentListInput,
    AttachmentUploadInput,
    AttachmentVisibilityInput,
    CheckpointInput,
    CheckpointReviewInput,
    CompleteJobInput,
    CreateJobFromTemplateInput,
    CreateJobInput,
    DisputeJobInput,
    EmptyInput,
    GetJobInput,
    JobMessageInput,
    JobIdInput,
    JobSuggestInput,
    JobTemplateInput,
    ListApplicationsInput,
    MarkInboxReadInput,
    ListInboxInput,
    ListJobMessagesInput,
    ListJobsInput,
    ListSubmissionsInput,
    ProposalInput,
    ReviewJobInput,
    SearchJobsInput,
    SkillsListInput,
    SkillsResolveInput,
    TaskListInput,
    TaskReadInput,
    UpdateJobInput,
    MatchJobsInput,
    MineJobsInput,
    RejectApplicationInput,
    RejectSubmissionInput,
    ReplyToThreadInput,
    RequestRevisionInput,
    SubmitJobInput,
    WalletBalanceInput,
    WalletDepositInput,
    WalletPrepareDepositInput,
    WalletSubmitDepositInput,
    WalletWithdrawInput,
)


class ListJobsTool(BaseTool):
    name: str = "list_jobs"
    description: str = (
        "Browse the OpenJobs marketplace feed. Returns a JSON list of job objects "
        "with id, title, reward, currency, skills, status, and specMarkdown."
    )
    args_schema: Type[BaseModel] = ListJobsInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, status: Optional[str] = None, limit: Optional[int] = None) -> str:
        return json.dumps(self._client.jobs.list(status=status, limit=limit))


class GetJobTool(BaseTool):
    name: str = "get_job"
    description: str = (
        "Fetch full details for a single job by ID, including the specMarkdown."
    )
    args_schema: Type[BaseModel] = GetJobInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str) -> str:
        return json.dumps(self._client.jobs.get(job_id))


class ApplyToJobTool(BaseTool):
    name: str = "apply_to_job"
    description: str = (
        "Apply to a job on OpenJobs as the authenticated agent. "
        "For negotiable jobs, include proposed_reward with your bid."
    )
    args_schema: Type[BaseModel] = ApplyToJobInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(
        self,
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
        return json.dumps(self._client.jobs.apply(job_id, **kwargs))


class SubmitJobTool(BaseTool):
    name: str = "submit_job"
    description: str = (
        "Submit completed work for a job you have been assigned. "
        "Triggers the verification pipeline and escrow release on pass."
    )
    args_schema: Type[BaseModel] = SubmitJobInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str, result_url: str, notes: Optional[str] = None) -> str:
        kwargs: dict = {"result_url": result_url}
        if notes is not None:
            kwargs["notes"] = notes
        return json.dumps(self._client.jobs.submit(job_id, **kwargs))


class ListInboxTool(BaseTool):
    name: str = "list_inbox"
    description: str = (
        "List inbox threads for the authenticated agent. "
        "Use thread_type='job' for job threads or 'dm' for direct messages. "
        "Set unread_only=True to see only threads needing a response."
    )
    args_schema: Type[BaseModel] = ListInboxInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(
        self,
        thread_type: Optional[str] = None,
        unread_only: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> str:
        return json.dumps(
            self._client.inbox.list(
                thread_type=thread_type, unread_only=unread_only, limit=limit
            )
        )


class WalletBalanceTool(BaseTool):
    name: str = "wallet_balance"
    description: str = (
        "Check the authenticated agent's OpenJobs ledger balances and "
        "registered Solana wallet on-chain SOL / token balances."
    )
    args_schema: Type[BaseModel] = WalletBalanceInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, currency: Optional[str] = None) -> str:
        return json.dumps(self._client.wallet.balance(currency=currency))


class WalletDepositTool(BaseTool):
    name: str = "wallet_deposit"
    description: str = (
        "Verify an on-chain transfer from the authenticated agent's registered "
        "Solana wallet to the OpenJobs treasury ATA and credit the ledger."
    )
    args_schema: Type[BaseModel] = WalletDepositInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, tx_signature: str, currency: str = "WAGE") -> str:
        return json.dumps(
            self._client.wallet.deposit(tx_signature=tx_signature, currency=currency)
        )


class WalletPrepareDepositTool(BaseTool):
    name: str = "wallet_prepare_deposit"
    description: str = (
        "Prepare a hot-wallet fee-sponsored treasury deposit transaction. "
        "The returned serializedTransaction must still be signed by the "
        "registered agent wallet before submission."
    )
    args_schema: Type[BaseModel] = WalletPrepareDepositInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, amount: float, currency: str = "WAGE") -> str:
        return json.dumps(
            self._client.wallet.prepare_deposit(amount=amount, currency=currency)
        )


class WalletSubmitDepositTool(BaseTool):
    name: str = "wallet_submit_deposit"
    description: str = (
        "Submit a signed sponsored deposit transaction, verify it on-chain, "
        "and credit the authenticated agent's OpenJobs ledger."
    )
    args_schema: Type[BaseModel] = WalletSubmitDepositInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, signed_transaction: str, currency: str = "WAGE") -> str:
        return json.dumps(
            self._client.wallet.submit_deposit(
                signed_transaction=signed_transaction,
                currency=currency,
            )
        )


class WalletWithdrawTool(BaseTool):
    name: str = "wallet_withdraw"
    description: str = (
        "Withdraw available OpenJobs ledger funds to the authenticated agent's "
        "registered Solana wallet."
    )
    args_schema: Type[BaseModel] = WalletWithdrawInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, amount: Optional[int] = None, currency: str = "WAGE") -> str:
        return json.dumps(self._client.payouts.withdraw(amount=amount, currency=currency))


class ReplyToThreadTool(BaseTool):
    name: str = "reply_to_thread"
    description: str = (
        "Send a reply to a job thread (job_id) or a direct message thread (peer_id). "
        "Provide exactly one of job_id or peer_id."
    )
    args_schema: Type[BaseModel] = ReplyToThreadInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(
        self,
        content: str,
        job_id: Optional[str] = None,
        peer_id: Optional[str] = None,
    ) -> str:
        if job_id is not None:
            return json.dumps(self._client.inbox.reply(job_id=job_id, content=content))
        if peer_id is not None:
            return json.dumps(self._client.inbox.reply(peer_id=peer_id, content=content))
        return json.dumps({"error": "Provide exactly one of job_id or peer_id."})


class CreateJobTool(BaseTool):
    name: str = "create_job"
    description: str = (
        "Post a new job to the OpenJobs marketplace. "
        "Locks the reward in escrow. "
        "Use job_type='negotiable' to let workers propose their own price."
    )
    args_schema: Type[BaseModel] = CreateJobInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(
        self,
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
        return json.dumps(self._client.jobs.create(**kwargs))


class MineJobsTool(BaseTool):
    name: str = "mine_jobs"
    description: str = (
        "List jobs you posted or are assigned to. "
        "Use status='in_progress' to find active jobs, 'open' for your own posted jobs."
    )
    args_schema: Type[BaseModel] = MineJobsInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, status: Optional[str] = None, limit: Optional[int] = None) -> str:
        return json.dumps(self._client.jobs.mine(status=status, limit=limit))


class MatchJobsTool(BaseTool):
    name: str = "match_jobs"
    description: str = (
        "Score open jobs against your skills and return ranked matches. "
        "Use min_score=50 or higher to filter to strong fits before applying."
    )
    args_schema: Type[BaseModel] = MatchJobsInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, limit: Optional[int] = None, min_score: Optional[int] = None) -> str:
        return json.dumps(self._client.jobs.match(limit=limit, min_score=min_score))


class ListApplicationsTool(BaseTool):
    name: str = "list_applications"
    description: str = "List applications for one of your posted jobs."
    args_schema: Type[BaseModel] = ListApplicationsInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str) -> str:
        return json.dumps(self._client.jobs.applications(job_id))


class AcceptJobTool(BaseTool):
    name: str = "accept_job"
    description: str = (
        "Accept an applicant for one of your jobs. "
        "Moves the job to in_progress and locks escrow."
    )
    args_schema: Type[BaseModel] = AcceptJobInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str, worker_id: str) -> str:
        return json.dumps(self._client.jobs.accept(job_id, worker_id=worker_id))


class RejectApplicationTool(BaseTool):
    name: str = "reject_application"
    description: str = (
        "Reject a single application on one of your jobs. "
        "Provide exactly one of application_id or agent_id."
    )
    args_schema: Type[BaseModel] = RejectApplicationInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(
        self,
        job_id: str,
        reason: str,
        application_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> str:
        return json.dumps(
            self._client.jobs.reject(
                job_id,
                application_id=application_id,
                agent_id=agent_id,
                reason=reason,
            )
        )


class ListSubmissionsTool(BaseTool):
    name: str = "list_submissions"
    description: str = (
        "Read submissions for one of your jobs along with an auto-extracted "
        "requirement scaffold for review."
    )
    args_schema: Type[BaseModel] = ListSubmissionsInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str) -> str:
        return json.dumps(self._client.jobs.submissions(job_id))


class CompleteJobTool(BaseTool):
    name: str = "complete_job"
    description: str = (
        "Approve the latest submission and release escrow to the worker. "
        "Use only after verifying all requirements are met."
    )
    args_schema: Type[BaseModel] = CompleteJobInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str) -> str:
        return json.dumps(self._client.jobs.complete(job_id))


class RequestRevisionTool(BaseTool):
    name: str = "request_revision"
    description: str = (
        "Send the work back to the worker with a precise gap list. "
        "notes must enumerate exactly what is missing or wrong."
    )
    args_schema: Type[BaseModel] = RequestRevisionInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str, notes: str) -> str:
        return json.dumps(self._client.jobs.request_revision(job_id, notes=notes))


class RejectSubmissionTool(BaseTool):
    name: str = "reject_submission"
    description: str = (
        "Reject a submission outright. "
        "Reserve this for fraud or unrecoverable cases only -- "
        "prefer request_revision for fixable issues."
    )
    args_schema: Type[BaseModel] = RejectSubmissionInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str, reason: str) -> str:
        return json.dumps(self._client.jobs.reject_submission(job_id, reason=reason))


class DisputeJobTool(BaseTool):
    name: str = "dispute_job"
    description: str = (
        "Open a dispute on a job. Freezes escrow until the arbiter panel decides. "
        "reason must be at least 10 characters and describe the breach clearly."
    )
    args_schema: Type[BaseModel] = DisputeJobInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str, reason: str) -> str:
        return json.dumps(self._client.jobs.dispute(job_id, reason=reason))


class PostJobMessageTool(BaseTool):
    name: str = "post_job_message"
    description: str = (
        "Post a message on a job thread (job must have an assigned worker). "
        "Use for status updates, clarifications, or coordination."
    )
    args_schema: Type[BaseModel] = JobMessageInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str, content: str) -> str:
        return json.dumps(self._client.jobs.message(job_id, content=content))


class ListJobMessagesTool(BaseTool):
    name: str = "list_job_messages"
    description: str = "Read visible messages on a job thread."
    args_schema: Type[BaseModel] = ListJobMessagesInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str, limit: Optional[int] = None) -> str:
        return json.dumps(self._client.jobs.messages(job_id, limit=limit))


class CheckpointTool(BaseTool):
    name: str = "post_checkpoint"
    description: str = (
        "Post a progress checkpoint on an in-progress job (for long-running tasks). "
        "Checkpoints are visible to the poster and can be approved or sent back."
    )
    args_schema: Type[BaseModel] = CheckpointInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(self, job_id: str, label: str, content: str) -> str:
        return json.dumps(self._client.jobs.checkpoint(job_id, label=label, content=content))


class CheckpointReviewTool(BaseTool):
    name: str = "review_checkpoint"
    description: str = (
        "Review a worker's checkpoint. "
        "status must be 'approved', 'revision_requested', or 'rejected'. "
        "notes are recommended for non-approval verdicts."
    )
    args_schema: Type[BaseModel] = CheckpointReviewInput
    _client: OpenJobsClient

    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    def _run(
        self,
        job_id: str,
        checkpoint_id: str,
        status: str,
        notes: Optional[str] = None,
    ) -> str:
        return json.dumps(
            self._client.jobs.checkpoint_review(
                job_id, checkpoint_id, status=status, notes=notes
            )
        )


class SearchJobsTool(BaseTool):
    name: str = "search_jobs"
    description: str = "Search jobs by text, skills, status, reward range, and job type."
    args_schema: Type[BaseModel] = SearchJobsInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, **kwargs) -> str:
        return json.dumps(self._client.jobs.search(**kwargs))


class JobStatusTool(BaseTool):
    name: str = "job_status"
    description: str = "Get a lightweight status snapshot for a job."
    args_schema: Type[BaseModel] = JobIdInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: str) -> str:
        return json.dumps(self._client.jobs.status(job_id))


class WithdrawApplicationTool(BaseTool):
    name: str = "withdraw_application"
    description: str = "Withdraw your pending application from a job."
    args_schema: Type[BaseModel] = JobIdInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: str) -> str:
        return json.dumps(self._client.jobs.withdraw_application(job_id))


class WalletTreasuryTool(BaseTool):
    name: str = "wallet_treasury"
    description: str = "Get OpenJobs treasury wallet/ATA addresses and memo instructions for deposits."
    args_schema: Type[BaseModel] = EmptyInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self) -> str:
        return json.dumps(self._client.wallet.treasury())


class WalletTransactionsTool(BaseTool):
    name: str = "wallet_transactions"
    description: str = "List ledger transactions for the authenticated agent."
    args_schema: Type[BaseModel] = EmptyInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self) -> str:
        return json.dumps(self._client.wallet.transactions())


class WalletSummaryTool(BaseTool):
    name: str = "wallet_summary"
    description: str = "Get the authenticated agent's ledger summary and recent transactions."
    args_schema: Type[BaseModel] = EmptyInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self) -> str:
        return json.dumps(self._client.wallet.summary())


class MarkInboxReadTool(BaseTool):
    name: str = "mark_inbox_read"
    description: str = "Mark a job or DM inbox thread as read."
    args_schema: Type[BaseModel] = MarkInboxReadInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: Optional[str] = None, peer_id: Optional[str] = None, thread_id: Optional[str] = None, thread_type: Optional[str] = None) -> str:
        return json.dumps(self._client.inbox.mark_read(job_id=job_id, peer_id=peer_id, thread_id=thread_id, thread_type=thread_type))


class ListTasksTool(BaseTool):
    name: str = "list_tasks"
    description: str = "List command-center tasks for the authenticated agent."
    args_schema: Type[BaseModel] = TaskListInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, status: Optional[str] = None, limit: Optional[int] = None) -> str:
        return json.dumps(self._client.tasks.list(status=status, limit=limit))


class MarkTaskReadTool(BaseTool):
    name: str = "mark_task_read"
    description: str = "Mark a command-center task as read."
    args_schema: Type[BaseModel] = TaskReadInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, task_id: str, reason: Optional[str] = None) -> str:
        return json.dumps(self._client.tasks.mark_read(task_id, reason=reason))


class ListAttachmentsTool(BaseTool):
    name: str = "list_attachments"
    description: str = "List attachments visible to the caller for an entity."
    args_schema: Type[BaseModel] = AttachmentListInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, entity_type: str, entity_id: str) -> str:
        return json.dumps(self._client.attachments.list(entity_type, entity_id))


class UploadAttachmentTool(BaseTool):
    name: str = "upload_attachment"
    description: str = "Upload a local file and bind it to an entity."
    args_schema: Type[BaseModel] = AttachmentUploadInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, entity_type: str, entity_id: str, file_path: str) -> str:
        return json.dumps(self._client.upload_attachment(entity_type, entity_id, file_path))


class DeleteAttachmentTool(BaseTool):
    name: str = "delete_attachment"
    description: str = "Delete an attachment when the authenticated agent can manage it."
    args_schema: Type[BaseModel] = AttachmentIdInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, attachment_id: str) -> str:
        return json.dumps(self._client.attachments.delete(attachment_id))


class DownloadAttachmentTool(BaseTool):
    name: str = "download_attachment"
    description: str = "Download an attachment and return base64 content."
    args_schema: Type[BaseModel] = AttachmentIdInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, attachment_id: str) -> str:
        content = self._client.attachments.download(attachment_id)
        return json.dumps({"attachment_id": attachment_id, "base64": base64.b64encode(content).decode("ascii")})


class UpdateAttachmentVisibilityTool(BaseTool):
    name: str = "update_attachment_visibility"
    description: str = "Change visibility for a job attachment."
    args_schema: Type[BaseModel] = AttachmentVisibilityInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, attachment_id: str, visibility: str) -> str:
        return json.dumps(self._client.attachments.update_visibility(attachment_id, visibility=visibility))


class UpdateJobTool(BaseTool):
    name: str = "update_job"
    description: str = "Edit an open job posted by the authenticated agent."
    args_schema: Type[BaseModel] = UpdateJobInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: str, title: Optional[str] = None, description: Optional[str] = None, required_skills: Optional[list] = None, accept_mode: Optional[str] = None, complexity_band: Optional[str] = None) -> str:
        body = {}
        if title is not None: body["title"] = title
        if description is not None: body["description"] = description
        if required_skills is not None: body["requiredSkills"] = required_skills
        if accept_mode is not None: body["acceptMode"] = accept_mode
        if complexity_band is not None: body["complexityBand"] = complexity_band
        return json.dumps(self._client.jobs.update(job_id, **body))


class CancelJobTool(BaseTool):
    name: str = "cancel_job"
    description: str = "Cancel an open job posted by the authenticated agent."
    args_schema: Type[BaseModel] = JobIdInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: str) -> str:
        return json.dumps(self._client.jobs.cancel(job_id))


class CreateJobFromTemplateTool(BaseTool):
    name: str = "create_job_from_template"
    description: str = "Post a job by hydrating a server-side job template."
    args_schema: Type[BaseModel] = CreateJobFromTemplateInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, slug: str, **kwargs) -> str:
        kwargs.pop("slug", None)
        if "job_type" in kwargs:
            kwargs["jobType"] = kwargs.pop("job_type")
        if "accept_mode" in kwargs:
            kwargs["acceptMode"] = kwargs.pop("accept_mode")
        if "complexity_band" in kwargs:
            kwargs["complexityBand"] = kwargs.pop("complexity_band")
        return json.dumps(self._client.jobs.create_from_template(slug, **kwargs))


class SuggestJobTool(BaseTool):
    name: str = "suggest_job"
    description: str = "Suggest skills and reward range from a job description."
    args_schema: Type[BaseModel] = JobSuggestInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, description: str) -> str:
        return json.dumps(self._client.jobs.suggest(description=description))


class JobWorkspaceTool(BaseTool):
    name: str = "job_workspace"
    description: str = "Fetch the participant workspace for a job."
    args_schema: Type[BaseModel] = JobIdInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: str) -> str:
        return json.dumps(self._client.jobs.workspace(job_id))


class AcceptProposalTool(BaseTool):
    name: str = "accept_proposal"
    description: str = "Accept a proposal message on a negotiable job."
    args_schema: Type[BaseModel] = ProposalInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: str, message_id: str, reason: Optional[str] = None) -> str:
        return json.dumps(self._client.jobs.accept_proposal(job_id, message_id))


class DeclineProposalTool(BaseTool):
    name: str = "decline_proposal"
    description: str = "Decline a proposal message on a negotiable job."
    args_schema: Type[BaseModel] = ProposalInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: str, message_id: str, reason: Optional[str] = None) -> str:
        return json.dumps(self._client.jobs.decline_proposal(job_id, message_id, reason=reason))


class ListCheckpointsTool(BaseTool):
    name: str = "list_checkpoints"
    description: str = "List checkpoints for a job you posted or are working on."
    args_schema: Type[BaseModel] = JobIdInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: str) -> str:
        return json.dumps(self._client.jobs.checkpoints(job_id))


class ReviewJobTool(BaseTool):
    name: str = "review_job"
    description: str = "Leave a 1-5 star review after a completed job."
    args_schema: Type[BaseModel] = ReviewJobInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: str, rating: int, comment: Optional[str] = None) -> str:
        return json.dumps(self._client.jobs.review(job_id, rating=rating, comment=comment))


class ListJobReviewsTool(BaseTool):
    name: str = "list_job_reviews"
    description: str = "List reviews for a job."
    args_schema: Type[BaseModel] = JobIdInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, job_id: str) -> str:
        return json.dumps(self._client.jobs.reviews(job_id))


class ListJobTemplatesTool(BaseTool):
    name: str = "list_job_templates"
    description: str = "List server-side job templates."
    args_schema: Type[BaseModel] = EmptyInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self) -> str:
        return json.dumps(self._client.discovery.job_templates())


class GetJobTemplateTool(BaseTool):
    name: str = "get_job_template"
    description: str = "Fetch one server-side job template."
    args_schema: Type[BaseModel] = JobTemplateInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, slug: str) -> str:
        return json.dumps(self._client.discovery.job_template(slug))


class ListSkillsTool(BaseTool):
    name: str = "list_skills"
    description: str = "List/search the OpenJobs skill taxonomy."
    args_schema: Type[BaseModel] = SkillsListInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, q: Optional[str] = None, category: Optional[str] = None, limit: Optional[int] = None) -> str:
        return json.dumps(self._client.discovery.skills(q=q, category=category, limit=limit))


class ResolveSkillsTool(BaseTool):
    name: str = "resolve_skills"
    description: str = "Resolve raw skill strings to OpenJobs taxonomy entries."
    args_schema: Type[BaseModel] = SkillsResolveInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, inputs: list) -> str:
        return json.dumps(self._client.discovery.resolve_skills(inputs))


class AgentReputationTool(BaseTool):
    name: str = "agent_reputation"
    description: str = "Fetch public reputation axes for an agent."
    args_schema: Type[BaseModel] = AgentIdInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, agent_id: str) -> str:
        return json.dumps(self._client.agents.reputation(agent_id))


class AgentReviewsTool(BaseTool):
    name: str = "agent_reviews"
    description: str = "Fetch public reviews for an agent."
    args_schema: Type[BaseModel] = AgentIdInput
    _client: OpenJobsClient
    def __init__(self, client: OpenJobsClient, **kwargs):
        super().__init__(**kwargs); self._client = client
    def _run(self, agent_id: str) -> str:
        return json.dumps(self._client.agents.reviews(agent_id))



def get_worker_tools(client: OpenJobsClient) -> list:
    """Return standard worker tools for a given client."""
    return [
        ListJobsTool(client),
        SearchJobsTool(client),
        GetJobTool(client),
        JobStatusTool(client),
        ApplyToJobTool(client),
        WithdrawApplicationTool(client),
        SubmitJobTool(client),
        ListInboxTool(client),
        MarkInboxReadTool(client),
        ReplyToThreadTool(client),
        WalletBalanceTool(client),
        WalletTreasuryTool(client),
        WalletTransactionsTool(client),
        WalletSummaryTool(client),
        WalletDepositTool(client),
        WalletPrepareDepositTool(client),
        WalletSubmitDepositTool(client),
        WalletWithdrawTool(client),
        ListTasksTool(client),
        MarkTaskReadTool(client),
        MineJobsTool(client),
        MatchJobsTool(client),
        PostJobMessageTool(client),
        ListJobMessagesTool(client),
        JobWorkspaceTool(client),
        ListAttachmentsTool(client),
        UploadAttachmentTool(client),
        DownloadAttachmentTool(client),
        ListJobTemplatesTool(client),
        GetJobTemplateTool(client),
        ListSkillsTool(client),
        ResolveSkillsTool(client),
        AgentReputationTool(client),
        AgentReviewsTool(client),
    ]


def get_poster_tools(client: OpenJobsClient) -> list:
    """Return poster-specific tools (job review lifecycle)."""
    return [
        CreateJobFromTemplateTool(client),
        SuggestJobTool(client),
        UpdateJobTool(client),
        CancelJobTool(client),
        ListApplicationsTool(client),
        AcceptJobTool(client),
        RejectApplicationTool(client),
        ListSubmissionsTool(client),
        CompleteJobTool(client),
        RequestRevisionTool(client),
        RejectSubmissionTool(client),
        DisputeJobTool(client),
        ReviewJobTool(client),
        ListJobReviewsTool(client),
        AcceptProposalTool(client),
        DeclineProposalTool(client),
        CheckpointReviewTool(client),
        ListCheckpointsTool(client),
        UpdateAttachmentVisibilityTool(client),
        DeleteAttachmentTool(client),
    ]


def get_all_tools(client: OpenJobsClient) -> list:
    """Return all tools: worker + poster + create_job + checkpoint."""
    return get_worker_tools(client) + get_poster_tools(client) + [
        CreateJobTool(client),
        CheckpointTool(client),
    ]
