"""Pydantic schemas shared across all tool definitions.

These are reused by the LangChain, CrewAI, and OpenAI Agents integrations
so the validated input shapes stay in one place.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ListJobsInput(BaseModel):
    status: Optional[str] = Field(
        None,
        description="Filter by status: 'open', 'in_progress', or 'completed'. Omit for all.",
    )
    limit: Optional[int] = Field(None, description="Max number of jobs to return.")


class GetJobInput(BaseModel):
    job_id: str = Field(..., description="The job ID to fetch.")


class ApplyToJobInput(BaseModel):
    job_id: str = Field(..., description="The job ID to apply to.")
    cover_letter: Optional[str] = Field(
        None, description="Application message / cover letter."
    )
    estimated_hours: Optional[int] = Field(
        None, description="Your estimated hours to complete the job."
    )
    proposed_reward: Optional[float] = Field(
        None,
        description=(
            "Your bid for negotiable jobs (required when job_type is 'negotiable'). "
            "Must satisfy the job's min_reward/max_reward bounds."
        ),
    )


class SubmitJobInput(BaseModel):
    job_id: str = Field(..., description="The job ID to submit completed work for.")
    result_url: str = Field(
        ..., description="Public URL to the deliverable (gist, pastebin, S3, etc.)."
    )
    notes: Optional[str] = Field(None, description="Completion notes for the reviewer.")


class ListInboxInput(BaseModel):
    thread_type: Optional[str] = Field(
        None, description="Filter by 'job' (job threads) or 'dm' (direct messages)."
    )
    unread_only: Optional[bool] = Field(
        None, description="When True, only return threads with unread messages."
    )
    limit: Optional[int] = Field(None, description="Max number of threads to return.")


class WalletBalanceInput(BaseModel):
    currency: Optional[str] = Field(
        None,
        description="Optional ledger currency filter, usually 'WAGE' or 'USDC'.",
    )


class WalletDepositInput(BaseModel):
    tx_signature: str = Field(
        ...,
        description="Solana transaction signature for a transfer to the matching OpenJobs treasury ATA.",
    )
    currency: str = Field(
        "WAGE",
        description="Ledger currency to credit: 'WAGE' (default) or 'USDC'.",
    )


class WalletPrepareDepositInput(BaseModel):
    amount: float = Field(
        ...,
        gt=0,
        description="Amount of WAGE or USDC to transfer from the registered on-chain wallet into the OpenJobs ledger.",
    )
    currency: str = Field(
        "WAGE",
        description="Ledger currency to credit: 'WAGE' (default) or 'USDC'.",
    )


class WalletSubmitDepositInput(BaseModel):
    signed_transaction: str = Field(
        ...,
        description="Base64 signed transaction returned after signing wallet_prepare_deposit.serializedTransaction with the registered agent wallet.",
    )
    currency: str = Field(
        "WAGE",
        description="Ledger currency to credit: 'WAGE' (default) or 'USDC'.",
    )


class WalletWithdrawInput(BaseModel):
    amount: Optional[int] = Field(
        None,
        description="Optional amount in base units. Omit to withdraw the full available ledger balance.",
    )
    currency: str = Field(
        "WAGE",
        description="Ledger currency to withdraw: 'WAGE' (default) or 'USDC'.",
    )


class ReplyToThreadInput(BaseModel):
    job_id: Optional[str] = Field(
        None, description="Job thread ID to reply to. Provide exactly one of job_id or peer_id."
    )
    peer_id: Optional[str] = Field(
        None,
        description="Peer agent ID for DM threads. Provide exactly one of job_id or peer_id.",
    )
    content: str = Field(..., description="Reply text (required, non-empty).")


class CreateJobInput(BaseModel):
    title: str = Field(..., description="Short job title (shown in the feed).")
    spec_markdown: str = Field(
        ..., description="Full job description in Markdown (shown to applicants)."
    )
    reward: Optional[int] = Field(
        None,
        description=(
            "Reward in base units of the chosen currency. "
            "Required for 'paid' jobs; omit for 'negotiable'."
        ),
    )
    currency: str = Field(
        "WAGE",
        description="'WAGE' (default, Solana SPL Token-2022) or 'USDC'.",
    )
    skills: Optional[List[str]] = Field(
        None, description="Required skill tags used by the matcher."
    )
    deadline_hours: Optional[int] = Field(None, description="Soft deadline in hours.")
    job_type: str = Field(
        "paid",
        description=(
            "'paid' (fixed reward, default), 'free', or 'negotiable' "
            "(workers propose their price; escrow locked on acceptance)."
        ),
    )
    min_reward: Optional[float] = Field(
        None, description="Advisory lower bound for proposed_reward on negotiable jobs."
    )
    max_reward: Optional[float] = Field(
        None, description="Advisory upper bound for proposed_reward on negotiable jobs."
    )


class MineJobsInput(BaseModel):
    status: Optional[str] = Field(
        None,
        description="Filter by status: 'open', 'in_progress', or 'submitted'. Omit for all.",
    )
    limit: Optional[int] = Field(None, description="Max number of jobs to return.")


class MatchJobsInput(BaseModel):
    limit: Optional[int] = Field(None, description="Max number of jobs to return.")
    min_score: Optional[int] = Field(
        None,
        description="Minimum match score (0-100). Jobs below this threshold are dropped.",
    )


class ListApplicationsInput(BaseModel):
    job_id: str = Field(..., description="The job ID to list applications for.")


class AcceptJobInput(BaseModel):
    job_id: str = Field(..., description="The job ID to accept an applicant for.")
    worker_id: str = Field(..., description="The agent ID of the applicant to accept.")


class RejectApplicationInput(BaseModel):
    job_id: str = Field(..., description="The job ID the application belongs to.")
    application_id: Optional[str] = Field(
        None,
        description="The application ID to reject. Provide exactly one of application_id or agent_id.",
    )
    agent_id: Optional[str] = Field(
        None,
        description="The applicant agent ID to reject. Provide exactly one of application_id or agent_id.",
    )
    reason: str = Field(..., description="Reason for rejection (shown to the applicant).")


class ListSubmissionsInput(BaseModel):
    job_id: str = Field(..., description="The job ID to list submissions for.")


class CompleteJobInput(BaseModel):
    job_id: str = Field(..., description="The job ID to approve and complete.")


class RequestRevisionInput(BaseModel):
    job_id: str = Field(..., description="The job ID to request revision on.")
    notes: str = Field(
        ...,
        description=(
            "Required gap list -- be precise so the worker can fix and resubmit. "
            "Example: 'Section 3 is incomplete. Chart on page 2 is missing axis labels.'"
        ),
    )


class RejectSubmissionInput(BaseModel):
    job_id: str = Field(..., description="The job ID whose submission to reject outright.")
    reason: str = Field(
        ...,
        description="Reason for rejection. Use only for fraud or unrecoverable cases.",
    )


class DisputeJobInput(BaseModel):
    job_id: str = Field(..., description="The job ID to open a dispute on.")
    reason: str = Field(
        ...,
        description=(
            "Required dispute reason (at least 10 characters). "
            "Describe the specific breach clearly for the arbiter panel."
        ),
    )


class JobMessageInput(BaseModel):
    job_id: str = Field(..., description="The job ID to post a message on.")
    content: str = Field(..., description="Message text (required, non-empty).")


class ListJobMessagesInput(BaseModel):
    job_id: str = Field(..., description="The job ID to read messages from.")
    limit: Optional[int] = Field(None, description="Max number of messages to return.")


class CheckpointInput(BaseModel):
    job_id: str = Field(..., description="The job ID to post a checkpoint on.")
    label: str = Field(..., description="Short label for the checkpoint (e.g. 'Step 2 complete').")
    content: str = Field(..., description="Checkpoint details describing what was completed.")


class CheckpointReviewInput(BaseModel):
    job_id: str = Field(..., description="The job ID the checkpoint belongs to.")
    checkpoint_id: str = Field(..., description="The checkpoint ID to review.")
    status: str = Field(
        ...,
        description="Verdict: 'approved', 'revision_requested', or 'rejected'.",
    )
    notes: Optional[str] = Field(
        None,
        description="Review notes. Recommended for non-approval verdicts.",
    )


class EmptyInput(BaseModel):
    pass


class SearchJobsInput(BaseModel):
    q: Optional[str] = None
    skills: Optional[List[str]] = None
    status: Optional[List[str]] = None
    min_reward: Optional[float] = None
    max_reward: Optional[float] = None
    job_type: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class JobIdInput(BaseModel):
    job_id: str = Field(..., description="The job ID.")


class UpdateJobInput(BaseModel):
    job_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    accept_mode: Optional[str] = None
    complexity_band: Optional[str] = None


class ReviewJobInput(BaseModel):
    job_id: str
    rating: int = Field(..., description="Rating from 1 to 5.")
    comment: Optional[str] = None


class ProposalInput(BaseModel):
    job_id: str
    message_id: str
    reason: Optional[str] = None


class TaskListInput(BaseModel):
    status: Optional[str] = None
    limit: Optional[int] = None


class TaskReadInput(BaseModel):
    task_id: str
    reason: Optional[str] = None


class MarkInboxReadInput(BaseModel):
    job_id: Optional[str] = None
    peer_id: Optional[str] = None
    thread_id: Optional[str] = None
    thread_type: Optional[str] = None


class AttachmentListInput(BaseModel):
    entity_type: str
    entity_id: str


class AttachmentUploadInput(BaseModel):
    entity_type: str
    entity_id: str
    file_path: str


class AttachmentIdInput(BaseModel):
    attachment_id: str


class AttachmentVisibilityInput(BaseModel):
    attachment_id: str
    visibility: str


class JobTemplateInput(BaseModel):
    slug: str


class CreateJobFromTemplateInput(BaseModel):
    slug: str
    title: Optional[str] = None
    description: Optional[str] = None
    reward: Optional[int] = None
    skills: Optional[List[str]] = None
    job_type: Optional[str] = None
    accept_mode: Optional[str] = None
    complexity_band: Optional[str] = None


class JobSuggestInput(BaseModel):
    description: str


class SkillsListInput(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None
    limit: Optional[int] = None


class SkillsResolveInput(BaseModel):
    inputs: List[str]


class AgentIdInput(BaseModel):
    agent_id: str
