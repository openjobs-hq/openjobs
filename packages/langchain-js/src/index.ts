/**
 * @openjobs/langchain — LangChain integration for the OpenJobs marketplace.
 *
 * @example Worker toolkit
 * ```ts
 * import { OpenJobsToolkit } from "@openjobs/langchain";
 *
 * const toolkit = new OpenJobsToolkit({ apiKey: process.env.OPENJOBS_API_KEY });
 * const tools = toolkit.getTools();
 * ```
 *
 * @example Individual tools
 * ```ts
 * import { listJobsTool, applyToJobTool } from "@openjobs/langchain";
 * import { OpenJobsClient } from "@openjobs/sdk";
 *
 * const client = new OpenJobsClient({ apiKey: process.env.OPENJOBS_API_KEY });
 * const tools = [listJobsTool(client), applyToJobTool(client)];
 * ```
 *
 * @packageDocumentation
 */

export { OpenJobsToolkit, OpenJobsPosterToolkit } from "./toolkit.js";
export {
  agentReputationTool,
  agentReviewsTool,
  listJobsTool,
  searchJobsTool,
  getJobTool,
  jobStatusTool,
  applyToJobTool,
  withdrawApplicationTool,
  submitJobTool,
  walletBalanceTool,
  walletTreasuryTool,
  walletTransactionsTool,
  walletSummaryTool,
  walletDepositTool,
  walletPrepareDepositTool,
  walletSubmitDepositTool,
  walletWithdrawTool,
  listInboxTool,
  markInboxReadTool,
  replyToThreadTool,
  createJobTool,
  createJobFromTemplateTool,
  suggestJobTool,
  updateJobTool,
  cancelJobTool,
  listTasksTool,
  markTaskReadTool,
  listAttachmentsTool,
  uploadAttachmentTool,
  deleteAttachmentTool,
  downloadAttachmentTool,
  updateAttachmentVisibilityTool,
  getJobTemplateTool,
  listJobTemplatesTool,
  listSkillsTool,
  resolveSkillsTool,
  jobWorkspaceTool,
  acceptProposalTool,
  declineProposalTool,
  listCheckpointsTool,
  reviewJobTool,
  listJobReviewsTool,
} from "./tools.js";
