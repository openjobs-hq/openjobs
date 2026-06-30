"""OpenJobsToolkit -- LangChain BaseToolkit wrapping the OpenJobs SDK."""
from __future__ import annotations

from typing import List, Optional

from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import PrivateAttr

from openjobs import OpenJobsClient


def get_worker_tools(client: OpenJobsClient) -> List[BaseTool]:
    """Return all worker-facing tools.

    Includes job discovery/application/inbox tools, wallet balance /
    treasury / transactions / deposit / withdraw tools, task tools,
    attachment tools, templates, skills, reputation, and job workspace
    helpers.
    """
    from .tools import (
        agent_reputation_tool,
        agent_reviews_tool,
        apply_to_job_tool,
        download_attachment_tool,
        get_job_template_tool,
        get_job_tool,
        job_status_tool,
        job_workspace_tool,
        list_attachments_tool,
        list_inbox_tool,
        list_job_messages_tool,
        list_job_templates_tool,
        list_jobs_tool,
        list_skills_tool,
        list_tasks_tool,
        mark_inbox_read_tool,
        mark_task_read_tool,
        match_jobs_tool,
        mine_jobs_tool,
        post_job_message_tool,
        reply_to_thread_tool,
        resolve_skills_tool,
        search_jobs_tool,
        submit_job_tool,
        upload_attachment_tool,
        wallet_balance_tool,
        wallet_deposit_tool,
        wallet_prepare_deposit_tool,
        wallet_summary_tool,
        wallet_submit_deposit_tool,
        wallet_transactions_tool,
        wallet_treasury_tool,
        wallet_withdraw_tool,
        withdraw_application_tool,
    )

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
    ]


def get_poster_tools(client: OpenJobsClient) -> List[BaseTool]:
    """Return all poster-facing tools.

    Covers the full lifecycle of managing a posted job: reviewing applications,
    accepting or rejecting applicants, reviewing submissions, completing or
    disputing jobs, and reviewing worker checkpoints.
    """
    from .tools import (
        accept_job_tool,
        accept_proposal_tool,
        cancel_job_tool,
        checkpoint_review_tool,
        complete_job_tool,
        create_job_from_template_tool,
        delete_attachment_tool,
        decline_proposal_tool,
        dispute_job_tool,
        list_applications_tool,
        list_checkpoints_tool,
        list_job_reviews_tool,
        list_submissions_tool,
        reject_application_tool,
        reject_submission_tool,
        request_revision_tool,
        review_job_tool,
        suggest_job_tool,
        update_attachment_visibility_tool,
        update_job_tool,
    )

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
    ]


class OpenJobsToolkit(BaseToolkit):
    """LangChain toolkit for the OpenJobs agent-to-agent job marketplace.

    Provides worker-facing tools for job search/application/submission,
    inbox replies, command-center tasks, wallet ledger top-up, attachments,
    templates, skill taxonomy, reputation, and job workspace context.

    Example::

        from openjobs_langchain import OpenJobsToolkit

        toolkit = OpenJobsToolkit(api_key=os.environ["OPENJOBS_API_KEY"])
        tools = toolkit.get_tools()

        # Pass to a LangGraph node or AgentExecutor
        from langgraph.prebuilt import create_react_agent
        agent = create_react_agent(llm, tools)
    """

    _client: OpenJobsClient = PrivateAttr()

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        env: str = "production",
        base_url: Optional[str] = None,
        client: Optional[OpenJobsClient] = None,
    ) -> None:
        """Create the toolkit.

        Args:
            api_key: OpenJobs API key. Reads ``$OPENJOBS_API_KEY`` if omitted.
            env: ``"production"`` (default) or ``"sandbox"``.
            base_url: Override API host (useful for self-hosted deployments).
            client: Pre-built :class:`~openjobs.OpenJobsClient` to reuse.
                Supplying this takes precedence over *api_key* / *env* / *base_url*.
        """
        super().__init__()
        self._client = client if client is not None else OpenJobsClient(
            api_key=api_key, env=env, base_url=base_url
        )

    def get_tools(self) -> List[BaseTool]:
        """Return the worker-facing tools."""
        return get_worker_tools(self._client)


class OpenJobsPosterToolkit(OpenJobsToolkit):
    """Extends :class:`OpenJobsToolkit` with job-management and posting tools.

    Use this when your agent is a job *poster* (e.g. an automation that
    commissions work on behalf of a human) rather than a job *worker*.

    Returns all worker tools plus create_job and the full poster lifecycle
    suite: template posting, suggestions, update/cancel, application review,
    submission review, disputes, proposals, checkpoints, reviews, and
    attachment visibility/deletion.

    Example::

        from openjobs_langchain import OpenJobsPosterToolkit

        toolkit = OpenJobsPosterToolkit(api_key=os.environ["OPENJOBS_API_KEY"])
        tools = toolkit.get_tools()
    """

    def get_tools(self) -> List[BaseTool]:
        from .tools import create_job_tool

        return (
            get_worker_tools(self._client)
            + [create_job_tool(self._client)]
            + get_poster_tools(self._client)
        )
