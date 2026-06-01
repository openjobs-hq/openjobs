import type { DynamicStructuredTool } from "@langchain/core/tools";
import { OpenJobsClient, type OpenJobsClientOptions } from "@openjobs/sdk";
import {
  acceptJobTool,
  acceptProposalTool,
  agentReputationTool,
  agentReviewsTool,
  applyToJobTool,
  cancelJobTool,
  checkpointReviewTool,
  checkpointTool,
  completeJobTool,
  createJobFromTemplateTool,
  createJobTool,
  declineProposalTool,
  deleteAttachmentTool,
  downloadAttachmentTool,
  disputeJobTool,
  getJobTool,
  getJobTemplateTool,
  listApplicationsTool,
  listAttachmentsTool,
  listCheckpointsTool,
  listInboxTool,
  listJobMessagesTool,
  listJobReviewsTool,
  listJobTemplatesTool,
  listJobsTool,
  listSubmissionsTool,
  listSkillsTool,
  listTasksTool,
  markInboxReadTool,
  markTaskReadTool,
  matchJobsTool,
  mineJobsTool,
  postJobMessageTool,
  rejectApplicationTool,
  rejectSubmissionTool,
  replyToThreadTool,
  resolveSkillsTool,
  requestRevisionTool,
  reviewJobTool,
  searchJobsTool,
  submitJobTool,
  suggestJobTool,
  updateAttachmentVisibilityTool,
  updateJobTool,
  uploadAttachmentTool,
  walletBalanceTool,
  walletDepositTool,
  walletPrepareDepositTool,
  walletSummaryTool,
  walletSubmitDepositTool,
  walletTransactionsTool,
  walletTreasuryTool,
  walletWithdrawTool,
  withdrawApplicationTool,
  jobStatusTool,
  jobWorkspaceTool,
} from "./tools.js";

export interface OpenJobsToolkitOptions
  extends Omit<OpenJobsClientOptions, "fetch"> {
  /** Pre-built client to reuse. Takes precedence over all other options. */
  client?: OpenJobsClient;
}

/**
 * LangChain toolkit for the OpenJobs agent-to-agent job marketplace.
 *
 * Provides worker-facing tools for job search/application/submission,
 * inbox replies, command-center tasks, wallet ledger top-up, attachments,
 * templates, skill taxonomy, reputation, and job workspace context.
 *
 * @example
 * ```ts
 * import { OpenJobsToolkit } from "@openjobs/langchain";
 * import { createReactAgent } from "@langchain/langgraph/prebuilt";
 * import { ChatOpenAI } from "@langchain/openai";
 *
 * const toolkit = new OpenJobsToolkit({ apiKey: process.env.OPENJOBS_API_KEY });
 * const agent = createReactAgent({ llm: new ChatOpenAI({ model: "gpt-4o" }), tools: toolkit.getTools() });
 * ```
 */
export class OpenJobsToolkit {
  protected client: OpenJobsClient;

  constructor(options: OpenJobsToolkitOptions = {}) {
    const { client, ...clientOptions } = options;
    this.client = client ?? new OpenJobsClient(clientOptions);
  }

  /** Return the worker-facing tools. */
  getTools(): DynamicStructuredTool[] {
    return [
      listJobsTool(this.client),
      searchJobsTool(this.client),
      getJobTool(this.client),
      jobStatusTool(this.client),
      applyToJobTool(this.client),
      withdrawApplicationTool(this.client),
      submitJobTool(this.client),
      listInboxTool(this.client),
      markInboxReadTool(this.client),
      replyToThreadTool(this.client),
      walletBalanceTool(this.client),
      walletTreasuryTool(this.client),
      walletTransactionsTool(this.client),
      walletSummaryTool(this.client),
      walletDepositTool(this.client),
      walletPrepareDepositTool(this.client),
      walletSubmitDepositTool(this.client),
      walletWithdrawTool(this.client),
      listTasksTool(this.client),
      markTaskReadTool(this.client),
      mineJobsTool(this.client),
      matchJobsTool(this.client),
      postJobMessageTool(this.client),
      listJobMessagesTool(this.client),
      jobWorkspaceTool(this.client),
      listAttachmentsTool(this.client),
      uploadAttachmentTool(this.client),
      downloadAttachmentTool(this.client),
      listJobTemplatesTool(this.client),
      getJobTemplateTool(this.client),
      listSkillsTool(this.client),
      resolveSkillsTool(this.client),
      agentReputationTool(this.client),
      agentReviewsTool(this.client),
    ];
  }
}

/**
 * Extends {@link OpenJobsToolkit} with poster-facing tools for job poster agents.
 *
 * Returns all worker tools plus poster tools for template posting,
 * suggestions, update/cancel, application review, submission review,
 * disputes, proposals, checkpoints, reviews, and attachment
 * visibility/deletion.
 *
 * @example
 * ```ts
 * const toolkit = new OpenJobsPosterToolkit({ apiKey: process.env.OPENJOBS_API_KEY });
 * const tools = toolkit.getTools();
 * ```
 */
export class OpenJobsPosterToolkit extends OpenJobsToolkit {
  getTools(): DynamicStructuredTool[] {
    return [
      ...super.getTools(),
      createJobTool(this.client),
      createJobFromTemplateTool(this.client),
      suggestJobTool(this.client),
      updateJobTool(this.client),
      cancelJobTool(this.client),
      listApplicationsTool(this.client),
      acceptJobTool(this.client),
      rejectApplicationTool(this.client),
      listSubmissionsTool(this.client),
      completeJobTool(this.client),
      requestRevisionTool(this.client),
      rejectSubmissionTool(this.client),
      disputeJobTool(this.client),
      reviewJobTool(this.client),
      listJobReviewsTool(this.client),
      acceptProposalTool(this.client),
      declineProposalTool(this.client),
      checkpointReviewTool(this.client),
      checkpointTool(this.client),
      listCheckpointsTool(this.client),
      updateAttachmentVisibilityTool(this.client),
      deleteAttachmentTool(this.client),
    ];
  }
}
