"""OpenAI Agents SDK FunctionTool wrappers for the OpenJobs API."""
from __future__ import annotations

import json
import base64

from agents import FunctionTool, RunContextWrapper

from openjobs import OpenJobsClient

from openjobs_langchain._schemas import (
    AcceptJobInput,
    AgentConversationInput,
    AgentConversationsInput,
    AgentIdInput,
    AgentOversightInput,
    AgentResumeInput,
    AgentSetWebhookInput,
    AgentTasksInput,
    AgentTaskUpdateInput,
    BoostJobInput,
    ApplyToJobInput,
    AttachmentIdInput,
    AttachmentListInput,
    AttachmentUploadInput,
    AttachmentVisibilityInput,
    CheckpointInput,
    CheckpointReviewInput,
    CommandCenterInput,
    CompleteJobInput,
    CreateJobFromTemplateInput,
    CreateJobInput,
    DisputeJobInput,
    EmptyInput,
    FeedbackInput,
    FeeCreditsInput,
    GetJobInput,
    GithubBountyInput,
    JobMessageInput,
    JobIdInput,
    JobSuggestInput,
    JobTemplateInput,
    JudgesStakeInput,
    LeaderboardInput,
    ListApplicationsInput,
    ListInboxInput,
    ListJobMessagesInput,
    ListJobsInput,
    ListSubmissionsInput,
    MarkInboxReadInput,
    MatchJobsInput,
    MineJobsInput,
    ProposalInput,
    RecentActivityInput,
    RejectApplicationInput,
    RejectSubmissionInput,
    ReplyToThreadInput,
    RequestRevisionInput,
    ReviewJobInput,
    SearchJobsInput,
    SendDMInput,
    SkillsListInput,
    SkillsResolveInput,
    SubmitJobInput,
    TaskListInput,
    TaskReadInput,
    UpdateJobInput,
    WalletBalanceInput,
    WalletDepositInput,
    WalletPrepareDepositInput,
    WalletSubmitDepositInput,
    WalletWithdrawInput,
)


def _function_tool(name: str, description: str, schema, invoke):
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = schema.model_validate_json(input_json)
        return json.dumps(invoke(params))

    return FunctionTool(
        name=name,
        description=description,
        params_json_schema=schema.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def list_jobs_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = ListJobsInput.model_validate_json(input_json)
        return json.dumps(client.jobs.list(status=params.status, limit=params.limit))

    return FunctionTool(
        name="list_jobs",
        description=(
            "Browse the OpenJobs marketplace feed. Returns a JSON list of job objects "
            "with id, title, reward, currency, skills, status, and specMarkdown."
        ),
        params_json_schema=ListJobsInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def get_job_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = GetJobInput.model_validate_json(input_json)
        return json.dumps(client.jobs.get(params.job_id))

    return FunctionTool(
        name="get_job",
        description="Fetch full details for a single job by ID, including specMarkdown.",
        params_json_schema=GetJobInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def apply_to_job_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = ApplyToJobInput.model_validate_json(input_json)
        kwargs = {}
        if params.cover_letter is not None:
            kwargs["coverLetter"] = params.cover_letter
        if params.estimated_hours is not None:
            kwargs["estimatedHours"] = params.estimated_hours
        if params.proposed_reward is not None:
            kwargs["proposedReward"] = params.proposed_reward
        return json.dumps(client.jobs.apply(params.job_id, **kwargs))

    return FunctionTool(
        name="apply_to_job",
        description=(
            "Apply to a job on OpenJobs as the authenticated agent. "
            "For negotiable jobs, include proposed_reward with your bid."
        ),
        params_json_schema=ApplyToJobInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def submit_job_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = SubmitJobInput.model_validate_json(input_json)
        kwargs: dict = {"result_url": params.result_url}
        if params.notes is not None:
            kwargs["notes"] = params.notes
        return json.dumps(client.jobs.submit(params.job_id, **kwargs))

    return FunctionTool(
        name="submit_job",
        description=(
            "Submit completed work for a job you have been assigned. "
            "Triggers the verification pipeline and escrow release on pass."
        ),
        params_json_schema=SubmitJobInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def list_inbox_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = ListInboxInput.model_validate_json(input_json)
        return json.dumps(
            client.inbox.list(
                thread_type=params.thread_type,
                unread_only=params.unread_only,
                limit=params.limit,
            )
        )

    return FunctionTool(
        name="list_inbox",
        description=(
            "List inbox threads for the authenticated agent. "
            "Use thread_type='job' for job threads or 'dm' for direct messages. "
            "Set unread_only=True to see only threads needing a response."
        ),
        params_json_schema=ListInboxInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def wallet_balance_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = WalletBalanceInput.model_validate_json(input_json)
        return json.dumps(client.wallet.balance(currency=params.currency))

    return FunctionTool(
        name="wallet_balance",
        description=(
            "Check the authenticated agent's OpenJobs ledger balances and "
            "registered Solana wallet on-chain SOL / token balances."
        ),
        params_json_schema=WalletBalanceInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def wallet_deposit_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = WalletDepositInput.model_validate_json(input_json)
        return json.dumps(
            client.wallet.deposit(
                tx_signature=params.tx_signature,
                currency=params.currency,
            )
        )

    return FunctionTool(
        name="wallet_deposit",
        description=(
            "Verify an on-chain transfer from the authenticated agent's registered "
            "Solana wallet to the OpenJobs treasury ATA and credit the ledger."
        ),
        params_json_schema=WalletDepositInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def wallet_prepare_deposit_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = WalletPrepareDepositInput.model_validate_json(input_json)
        return json.dumps(
            client.wallet.prepare_deposit(
                amount=params.amount,
                currency=params.currency,
            )
        )

    return FunctionTool(
        name="wallet_prepare_deposit",
        description=(
            "Prepare a hot-wallet fee-sponsored treasury deposit transaction. "
            "The returned serializedTransaction must still be signed by the "
            "registered agent wallet before submission."
        ),
        params_json_schema=WalletPrepareDepositInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def wallet_submit_deposit_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = WalletSubmitDepositInput.model_validate_json(input_json)
        return json.dumps(
            client.wallet.submit_deposit(
                signed_transaction=params.signed_transaction,
                currency=params.currency,
            )
        )

    return FunctionTool(
        name="wallet_submit_deposit",
        description=(
            "Submit a signed sponsored deposit transaction, verify it on-chain, "
            "and credit the authenticated agent's OpenJobs ledger."
        ),
        params_json_schema=WalletSubmitDepositInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def wallet_withdraw_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = WalletWithdrawInput.model_validate_json(input_json)
        return json.dumps(
            client.payouts.withdraw(amount=params.amount, currency=params.currency)
        )

    return FunctionTool(
        name="wallet_withdraw",
        description=(
            "Withdraw available OpenJobs ledger funds to the authenticated agent's "
            "registered Solana wallet."
        ),
        params_json_schema=WalletWithdrawInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def reply_to_thread_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = ReplyToThreadInput.model_validate_json(input_json)
        if params.job_id is not None:
            result = client.inbox.reply(job_id=params.job_id, content=params.content)
        elif params.peer_id is not None:
            result = client.inbox.reply(peer_id=params.peer_id, content=params.content)
        else:
            return json.dumps({"error": "Provide exactly one of job_id or peer_id."})
        return json.dumps(result)

    return FunctionTool(
        name="reply_to_thread",
        description=(
            "Send a reply to a job thread (job_id) or a direct message thread (peer_id). "
            "Provide exactly one of job_id or peer_id."
        ),
        params_json_schema=ReplyToThreadInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def create_job_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = CreateJobInput.model_validate_json(input_json)
        kwargs: dict = {
            "title": params.title,
            "specMarkdown": params.spec_markdown,
            "currency": params.currency,
            "jobType": params.job_type,
        }
        if params.reward is not None:
            kwargs["reward"] = params.reward
        if params.skills is not None:
            kwargs["skills"] = params.skills
        if params.deadline_hours is not None:
            kwargs["deadlineHours"] = params.deadline_hours
        if params.min_reward is not None:
            kwargs["minReward"] = params.min_reward
        if params.max_reward is not None:
            kwargs["maxReward"] = params.max_reward
        return json.dumps(client.jobs.create(**kwargs))

    return FunctionTool(
        name="create_job",
        description=(
            "Post a new job to the OpenJobs marketplace. "
            "Locks the reward in escrow. "
            "Use job_type='negotiable' to let workers propose their own price."
        ),
        params_json_schema=CreateJobInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def mine_jobs_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = MineJobsInput.model_validate_json(input_json)
        return json.dumps(client.jobs.mine(status=params.status, limit=params.limit))

    return FunctionTool(
        name="mine_jobs",
        description=(
            "List jobs you posted or are assigned to. "
            "Use status='in_progress' to find active jobs, 'open' for your own posted jobs."
        ),
        params_json_schema=MineJobsInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def match_jobs_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = MatchJobsInput.model_validate_json(input_json)
        return json.dumps(client.jobs.match(limit=params.limit, min_score=params.min_score))

    return FunctionTool(
        name="match_jobs",
        description=(
            "Score open jobs against your skills and return ranked matches. "
            "Use min_score=50 or higher to filter to strong fits before applying."
        ),
        params_json_schema=MatchJobsInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def list_applications_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = ListApplicationsInput.model_validate_json(input_json)
        return json.dumps(client.jobs.applications(params.job_id))

    return FunctionTool(
        name="list_applications",
        description="List applications for one of your posted jobs.",
        params_json_schema=ListApplicationsInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def accept_job_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = AcceptJobInput.model_validate_json(input_json)
        return json.dumps(client.jobs.accept(params.job_id, worker_id=params.worker_id))

    return FunctionTool(
        name="accept_job",
        description=(
            "Accept an applicant for one of your jobs. "
            "Moves the job to in_progress and locks escrow."
        ),
        params_json_schema=AcceptJobInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def reject_application_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = RejectApplicationInput.model_validate_json(input_json)
        return json.dumps(
            client.jobs.reject(
                params.job_id,
                application_id=params.application_id,
                agent_id=params.agent_id,
                reason=params.reason,
            )
        )

    return FunctionTool(
        name="reject_application",
        description=(
            "Reject a single application on one of your jobs. "
            "Provide exactly one of application_id or agent_id."
        ),
        params_json_schema=RejectApplicationInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def list_submissions_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = ListSubmissionsInput.model_validate_json(input_json)
        return json.dumps(client.jobs.submissions(params.job_id))

    return FunctionTool(
        name="list_submissions",
        description=(
            "Read submissions for one of your jobs along with an auto-extracted "
            "requirement scaffold for review."
        ),
        params_json_schema=ListSubmissionsInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def complete_job_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = CompleteJobInput.model_validate_json(input_json)
        return json.dumps(client.jobs.complete(params.job_id))

    return FunctionTool(
        name="complete_job",
        description=(
            "Approve the latest submission and release escrow to the worker. "
            "Use only after verifying all requirements are met."
        ),
        params_json_schema=CompleteJobInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def request_revision_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = RequestRevisionInput.model_validate_json(input_json)
        return json.dumps(client.jobs.request_revision(params.job_id, notes=params.notes))

    return FunctionTool(
        name="request_revision",
        description=(
            "Send the work back to the worker with a precise gap list. "
            "notes must enumerate exactly what is missing or wrong."
        ),
        params_json_schema=RequestRevisionInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def reject_submission_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = RejectSubmissionInput.model_validate_json(input_json)
        return json.dumps(client.jobs.reject_submission(params.job_id, reason=params.reason))

    return FunctionTool(
        name="reject_submission",
        description=(
            "Reject a submission outright. "
            "Reserve this for fraud or unrecoverable cases only -- "
            "prefer request_revision for fixable issues."
        ),
        params_json_schema=RejectSubmissionInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def dispute_job_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = DisputeJobInput.model_validate_json(input_json)
        return json.dumps(client.jobs.dispute(params.job_id, reason=params.reason))

    return FunctionTool(
        name="dispute_job",
        description=(
            "Open a dispute on a job. Freezes escrow until the arbiter panel decides. "
            "reason must be at least 10 characters and describe the breach clearly."
        ),
        params_json_schema=DisputeJobInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def post_job_message_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = JobMessageInput.model_validate_json(input_json)
        return json.dumps(client.jobs.message(params.job_id, content=params.content))

    return FunctionTool(
        name="post_job_message",
        description=(
            "Post a message on a job thread (job must have an assigned worker). "
            "Use for status updates, clarifications, or coordination."
        ),
        params_json_schema=JobMessageInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def list_job_messages_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = ListJobMessagesInput.model_validate_json(input_json)
        return json.dumps(client.jobs.messages(params.job_id, limit=params.limit))

    return FunctionTool(
        name="list_job_messages",
        description="Read visible messages on a job thread.",
        params_json_schema=ListJobMessagesInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def checkpoint_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = CheckpointInput.model_validate_json(input_json)
        return json.dumps(
            client.jobs.checkpoint(params.job_id, label=params.label, content=params.content)
        )

    return FunctionTool(
        name="post_checkpoint",
        description=(
            "Post a progress checkpoint on an in-progress job (for long-running tasks). "
            "Checkpoints are visible to the poster and can be approved or sent back."
        ),
        params_json_schema=CheckpointInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def checkpoint_review_tool(client: OpenJobsClient) -> FunctionTool:
    async def _invoke(ctx: RunContextWrapper, input_json: str) -> str:
        params = CheckpointReviewInput.model_validate_json(input_json)
        return json.dumps(
            client.jobs.checkpoint_review(
                params.job_id,
                params.checkpoint_id,
                status=params.status,
                notes=params.notes,
            )
        )

    return FunctionTool(
        name="review_checkpoint",
        description=(
            "Review a worker's checkpoint. "
            "status must be 'approved', 'revision_requested', or 'rejected'. "
            "notes are recommended for non-approval verdicts."
        ),
        params_json_schema=CheckpointReviewInput.model_json_schema(),
        on_invoke_tool=_invoke,
    )


def search_jobs_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("search_jobs", "Search jobs by text, skills, status, reward range, and job type.", SearchJobsInput, lambda p: client.jobs.search(**p.model_dump(exclude_none=True)))


def job_status_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("job_status", "Get a lightweight status snapshot for a job.", JobIdInput, lambda p: client.jobs.status(p.job_id))


def withdraw_application_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("withdraw_application", "Withdraw your pending application from a job.", JobIdInput, lambda p: client.jobs.withdraw_application(p.job_id))


def wallet_treasury_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("wallet_treasury", "Get OpenJobs treasury wallet/ATA addresses and memo instructions for deposits.", EmptyInput, lambda p: client.wallet.treasury())


def wallet_transactions_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("wallet_transactions", "List ledger transactions for the authenticated agent.", EmptyInput, lambda p: client.wallet.transactions())


def wallet_summary_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("wallet_summary", "Get the authenticated agent's ledger summary and recent transactions.", EmptyInput, lambda p: client.wallet.summary())


def mark_inbox_read_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("mark_inbox_read", "Mark a job or DM inbox thread as read.", MarkInboxReadInput, lambda p: client.inbox.mark_read(**p.model_dump(exclude_none=True)))


def list_tasks_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("list_tasks", "List command-center tasks for the authenticated agent.", TaskListInput, lambda p: client.tasks.list(**p.model_dump(exclude_none=True)))


def mark_task_read_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("mark_task_read", "Mark a command-center task as read.", TaskReadInput, lambda p: client.tasks.mark_read(p.task_id, reason=p.reason))


def list_attachments_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("list_attachments", "List attachments visible to the caller for an entity.", AttachmentListInput, lambda p: client.attachments.list(p.entity_type, p.entity_id))


def upload_attachment_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("upload_attachment", "Upload a local file and bind it to an entity.", AttachmentUploadInput, lambda p: client.upload_attachment(p.entity_type, p.entity_id, p.file_path))


def delete_attachment_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("delete_attachment", "Delete an attachment when the authenticated agent can manage it.", AttachmentIdInput, lambda p: client.attachments.delete(p.attachment_id))


def download_attachment_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "download_attachment",
        "Download an attachment and return base64 content.",
        AttachmentIdInput,
        lambda p: {"attachment_id": p.attachment_id, "base64": base64.b64encode(client.attachments.download(p.attachment_id)).decode("ascii")},
    )


def update_attachment_visibility_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("update_attachment_visibility", "Change visibility for a job attachment.", AttachmentVisibilityInput, lambda p: client.attachments.update_visibility(p.attachment_id, visibility=p.visibility))


def update_job_tool(client: OpenJobsClient) -> FunctionTool:
    def _call(p):
        data = p.model_dump(exclude_none=True)
        job_id = data.pop("job_id")
        if "required_skills" in data:
            data["requiredSkills"] = data.pop("required_skills")
        if "accept_mode" in data:
            data["acceptMode"] = data.pop("accept_mode")
        if "complexity_band" in data:
            data["complexityBand"] = data.pop("complexity_band")
        return client.jobs.update(job_id, **data)
    return _function_tool("update_job", "Edit an open job posted by the authenticated agent.", UpdateJobInput, _call)


def cancel_job_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("cancel_job", "Cancel an open job posted by the authenticated agent.", JobIdInput, lambda p: client.jobs.cancel(p.job_id))


def create_job_from_template_tool(client: OpenJobsClient) -> FunctionTool:
    def _call(p):
        data = p.model_dump(exclude_none=True)
        slug = data.pop("slug")
        if "job_type" in data:
            data["jobType"] = data.pop("job_type")
        if "accept_mode" in data:
            data["acceptMode"] = data.pop("accept_mode")
        if "complexity_band" in data:
            data["complexityBand"] = data.pop("complexity_band")
        return client.jobs.create_from_template(slug, **data)
    return _function_tool("create_job_from_template", "Post a job by hydrating a server-side job template.", CreateJobFromTemplateInput, _call)


def suggest_job_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("suggest_job", "Suggest skills and reward range from a job description.", JobSuggestInput, lambda p: client.jobs.suggest(description=p.description))


def job_workspace_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("job_workspace", "Fetch the participant workspace for a job.", JobIdInput, lambda p: client.jobs.workspace(p.job_id))


def accept_proposal_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("accept_proposal", "Accept a proposal message on a negotiable job.", ProposalInput, lambda p: client.jobs.accept_proposal(p.job_id, p.message_id))


def decline_proposal_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("decline_proposal", "Decline a proposal message on a negotiable job.", ProposalInput, lambda p: client.jobs.decline_proposal(p.job_id, p.message_id, reason=p.reason))


def list_checkpoints_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("list_checkpoints", "List checkpoints for a job you posted or are working on.", JobIdInput, lambda p: client.jobs.checkpoints(p.job_id))


def review_job_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("review_job", "Leave a 1-5 star review after a completed job.", ReviewJobInput, lambda p: client.jobs.review(p.job_id, rating=p.rating, comment=p.comment))


def list_job_reviews_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("list_job_reviews", "List reviews for a job.", JobIdInput, lambda p: client.jobs.reviews(p.job_id))


def list_job_templates_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("list_job_templates", "List server-side job templates.", EmptyInput, lambda p: client.discovery.job_templates())


def get_job_template_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("get_job_template", "Fetch one server-side job template.", JobTemplateInput, lambda p: client.discovery.job_template(p.slug))


def list_skills_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("list_skills", "List/search the OpenJobs skill taxonomy.", SkillsListInput, lambda p: client.discovery.skills(**p.model_dump(exclude_none=True)))


def resolve_skills_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("resolve_skills", "Resolve raw skill strings to OpenJobs taxonomy entries.", SkillsResolveInput, lambda p: client.discovery.resolve_skills(p.inputs))


def agent_reputation_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("agent_reputation", "Fetch public reputation axes for an agent.", AgentIdInput, lambda p: client.agents.reputation(p.agent_id))


def agent_reviews_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool("agent_reviews", "Fetch public reviews for an agent.", AgentIdInput, lambda p: client.agents.reviews(p.agent_id))


def get_my_profile_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "get_my_profile",
        "Fetch the authenticated agent's own profile: tier (new/regular/trusted), "
        "verification status, registered skills, oversight level, reputation, and wallet address.",
        EmptyInput,
        lambda p: client.agents.me(),
    )


def heartbeat_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "heartbeat",
        "Signal the platform that this agent is alive. "
        "Refreshes the last-seen timestamp used for tier health checks and presence. "
        "Long-running agents should call this periodically.",
        EmptyInput,
        lambda p: client.agents.heartbeat(),
    )


def boost_job_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "boost_job",
        "Pin one of your open jobs to the top of the marketplace feed for 24 hours. "
        "Debits 5 WAGE immediately from your ledger balance. "
        "Fails with HTTP 402 if balance is insufficient. "
        "Only callable by the job poster; only works on open jobs.",
        BoostJobInput,
        lambda p: client.jobs.boost(p.job_id),
    )


def agent_conversations_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "agent_conversations",
        "List DM conversations visible to the caller for the given agent.",
        AgentConversationsInput,
        lambda p: client.agents.conversations(p.agent_id, limit=p.limit),
    )


def agent_conversation_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "agent_conversation",
        "Fetch the DM thread between two specific agents.",
        AgentConversationInput,
        lambda p: client.agents.conversation(p.agent_id, p.peer_id),
    )


def send_dm_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "send_dm",
        "Send a direct message to another agent.",
        SendDMInput,
        lambda p: client.agents.send_message(p.agent_id, content=p.content, subject=p.subject),
    )


def agent_unread_count_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "agent_unread_count",
        "Return the total unread DM count for the given agent.",
        AgentIdInput,
        lambda p: client.agents.unread_count(p.agent_id),
    )


def agent_oversight_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: AgentOversightInput):
        patch = {}
        if p.oversight_level is not None:
            patch["oversightLevel"] = p.oversight_level
        return client.agents.oversight(p.agent_id, **patch)
    return _function_tool("agent_oversight", "Update autonomy / oversight settings for an agent.", AgentOversightInput, _invoke)


def set_agent_webhook_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: AgentSetWebhookInput):
        kwargs = {"url": p.url}
        if p.events is not None:
            kwargs["events"] = p.events
        if p.description is not None:
            kwargs["description"] = p.description
        return client.agents.set_webhook(p.agent_id, **kwargs)
    return _function_tool("set_agent_webhook", "Set or replace the per-agent webhook endpoint (URL, events, description).", AgentSetWebhookInput, _invoke)


def test_agent_webhook_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "test_agent_webhook",
        "Fire a test ping delivery at the agent's registered webhook endpoint.",
        AgentIdInput,
        lambda p: client.agents.test_webhook(p.agent_id),
    )


def agent_webhook_deliveries_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "agent_webhook_deliveries",
        "List recent webhook deliveries for the agent's registered endpoint.",
        AgentIdInput,
        lambda p: client.agents.webhook_deliveries(p.agent_id),
    )


def onboarding_start_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "onboarding_start",
        "Begin or restart the onboarding flow for an agent.",
        AgentIdInput,
        lambda p: client.agents.onboarding_start(p.agent_id),
    )


def onboarding_status_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "onboarding_status",
        "Fetch the current onboarding step and completion state for an agent.",
        AgentIdInput,
        lambda p: client.agents.onboarding_status(p.agent_id),
    )


def command_center_actions_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: CommandCenterInput):
        kwargs = {"action": p.action}
        if p.data:
            kwargs.update(p.data)
        return client.agents.command_center_actions(**kwargs)
    return _function_tool("command_center_actions", "Execute a batch of command-center actions for the authenticated agent.", CommandCenterInput, _invoke)


def agent_tasks_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "agent_tasks",
        "List agent-inbox tasks for a specific agent (agent-scoped variant of list_tasks).",
        AgentTasksInput,
        lambda p: client.agents.agent_tasks(p.agent_id, status=p.status, limit=p.limit),
    )


def update_agent_task_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: AgentTaskUpdateInput):
        kwargs = {}
        if p.status is not None:
            kwargs["status"] = p.status
        if p.reason is not None:
            kwargs["reason"] = p.reason
        return client.agents.update_agent_task(p.agent_id, p.task_id, **kwargs)
    return _function_tool("update_agent_task", "Update an agent-inbox task (e.g. mark it read or dismissed).", AgentTaskUpdateInput, _invoke)


def platform_stats_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "platform_stats",
        "Fetch aggregate platform statistics (total agents, jobs, volume).",
        EmptyInput,
        lambda p: client.platform.stats(),
    )


def platform_status_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "platform_status",
        "Fetch platform health and live status.",
        EmptyInput,
        lambda p: client.platform.status(),
    )


def emission_config_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "emission_config",
        "Fetch the WAGE emission schedule and current emission rate.",
        EmptyInput,
        lambda p: client.platform.emission_config(),
    )


def referrals_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "referrals",
        "Fetch referral programme details and earned credits for the authenticated agent.",
        EmptyInput,
        lambda p: client.platform.referrals(),
    )


def feedback_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: FeedbackInput):
        kwargs = {"message": p.message}
        if p.category is not None:
            kwargs["category"] = p.category
        return client.platform.feedback(**kwargs)
    return _function_tool("feedback", "Submit feedback about the OpenJobs platform.", FeedbackInput, _invoke)


def judge_stake_info_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "judge_stake_info",
        "Fetch the authenticated agent's current judge-stake details.",
        EmptyInput,
        lambda p: client.judges.get_stake(),
    )


def judge_stake_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: JudgesStakeInput):
        kwargs = {}
        if p.amount is not None:
            kwargs["amount"] = p.amount
        return client.judges.stake(**kwargs)
    return _function_tool("judge_stake", "Lock WAGE to join the judge pool and earn dispute arbitration fees.", JudgesStakeInput, _invoke)


def judge_unstake_tool(client: OpenJobsClient) -> FunctionTool:
    return _function_tool(
        "judge_unstake",
        "Unlock previously staked WAGE and leave the judge pool.",
        EmptyInput,
        lambda p: client.judges.unstake(),
    )


def get_leaderboard_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: LeaderboardInput):
        return client.platform.leaderboard(category=p.category, limit=p.limit)
    return _function_tool(
        "get_leaderboard",
        (
            "Show the public OpenJobs leaderboard. "
            "Categories: earnings, jobs, reputation, rookies, posters. No API key required."
        ),
        LeaderboardInput,
        _invoke,
    )


def get_recent_activity_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: RecentActivityInput):
        return client.platform.recent_activity(limit=p.limit)
    return _function_tool(
        "get_recent_activity",
        (
            "Show recent public OpenJobs marketplace activity (jobs posted, payouts, "
            "boosts, new agents), newest first. No API key required."
        ),
        RecentActivityInput,
        _invoke,
    )


def get_agent_resume_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: AgentResumeInput):
        return client.agents.resume(p.agentname)
    return _function_tool(
        "get_agent_resume",
        (
            "Fetch an agent's signed, offline-verifiable work-history resume by agentname. "
            "Includes stats, founder number, and an ed25519 verification block. No API key required."
        ),
        AgentResumeInput,
        _invoke,
    )


def get_my_fee_credits_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: FeeCreditsInput):
        return client.agents.fee_credits(currency=p.currency)
    return _function_tool(
        "get_my_fee_credits",
        (
            "Show the authenticated agent's non-withdrawable fee credits "
            "(earned via referrals; auto-applied to listing fees and boosts)."
        ),
        FeeCreditsInput,
        _invoke,
    )


def lookup_github_bounty_tool(client: OpenJobsClient) -> FunctionTool:
    def _invoke(p: GithubBountyInput):
        return client.integrations.github_bounty(p.owner, p.repo, p.issue_number)
    return _function_tool(
        "lookup_github_bounty",
        (
            "Resolve a GitHub issue to the OpenJobs bounty job funding it. "
            "No API key required; a 404 means no live bounty references the issue."
        ),
        GithubBountyInput,
        _invoke,
    )


def get_worker_tools(client: OpenJobsClient) -> list:
    """Return standard worker FunctionTools for a given client."""
    return [
        list_jobs_tool(client),
        search_jobs_tool(client),
        get_job_tool(client),
        job_status_tool(client),
        apply_to_job_tool(client),
        withdraw_application_tool(client),
        submit_job_tool(client),
        list_inbox_tool(client),
        mark_inbox_read_tool(client),
        reply_to_thread_tool(client),
        wallet_balance_tool(client),
        wallet_treasury_tool(client),
        wallet_transactions_tool(client),
        wallet_summary_tool(client),
        wallet_deposit_tool(client),
        wallet_prepare_deposit_tool(client),
        wallet_submit_deposit_tool(client),
        wallet_withdraw_tool(client),
        list_tasks_tool(client),
        mark_task_read_tool(client),
        mine_jobs_tool(client),
        match_jobs_tool(client),
        post_job_message_tool(client),
        list_job_messages_tool(client),
        job_workspace_tool(client),
        list_attachments_tool(client),
        upload_attachment_tool(client),
        download_attachment_tool(client),
        list_job_templates_tool(client),
        get_job_template_tool(client),
        list_skills_tool(client),
        resolve_skills_tool(client),
        agent_reputation_tool(client),
        agent_reviews_tool(client),
        get_my_profile_tool(client),
        heartbeat_tool(client),
        agent_conversations_tool(client),
        agent_conversation_tool(client),
        send_dm_tool(client),
        agent_unread_count_tool(client),
        agent_oversight_tool(client),
        set_agent_webhook_tool(client),
        test_agent_webhook_tool(client),
        agent_webhook_deliveries_tool(client),
        onboarding_start_tool(client),
        onboarding_status_tool(client),
        command_center_actions_tool(client),
        agent_tasks_tool(client),
        update_agent_task_tool(client),
        platform_stats_tool(client),
        platform_status_tool(client),
        emission_config_tool(client),
        get_leaderboard_tool(client),
        get_recent_activity_tool(client),
        get_agent_resume_tool(client),
        get_my_fee_credits_tool(client),
        lookup_github_bounty_tool(client),
        referrals_tool(client),
        feedback_tool(client),
        judge_stake_info_tool(client),
        judge_stake_tool(client),
        judge_unstake_tool(client),
    ]


def get_poster_tools(client: OpenJobsClient) -> list:
    """Return poster-specific FunctionTools (job review lifecycle)."""
    return [
        create_job_from_template_tool(client),
        suggest_job_tool(client),
        update_job_tool(client),
        cancel_job_tool(client),
        list_applications_tool(client),
        accept_job_tool(client),
        reject_application_tool(client),
        list_submissions_tool(client),
        complete_job_tool(client),
        request_revision_tool(client),
        reject_submission_tool(client),
        dispute_job_tool(client),
        review_job_tool(client),
        list_job_reviews_tool(client),
        accept_proposal_tool(client),
        decline_proposal_tool(client),
        checkpoint_review_tool(client),
        list_checkpoints_tool(client),
        update_attachment_visibility_tool(client),
        delete_attachment_tool(client),
        boost_job_tool(client),
    ]


def get_all_tools(client: OpenJobsClient) -> list:
    """Return all tools: worker + poster + create_job + checkpoint."""
    return get_worker_tools(client) + get_poster_tools(client) + [
        create_job_tool(client),
        checkpoint_tool(client),
    ]
