import { DynamicStructuredTool } from "@langchain/core/tools";
import { z } from "zod";
import type { OpenJobsClient } from "@openjobs/sdk";

const listJobsSchema = z.object({
  status: z.string().optional().describe(
    "Filter by status: 'open', 'in_progress', or 'completed'. Omit for all."
  ),
  limit: z.number().int().positive().optional().describe(
    "Max number of jobs to return."
  ),
});

const getJobSchema = z.object({
  jobId: z.string().describe("The job ID to fetch."),
});

const applyToJobSchema = z.object({
  jobId: z.string().describe("The job ID to apply to."),
  coverLetter: z.string().optional().describe("Application message / cover letter."),
  estimatedHours: z.number().int().positive().optional().describe(
    "Your estimated hours to complete the job."
  ),
  proposedReward: z.number().positive().optional().describe(
    "Your bid for negotiable jobs (required when job_type is 'negotiable')."
  ),
});

const submitJobSchema = z.object({
  jobId: z.string().describe("The job ID to submit completed work for."),
  resultUrl: z.string().url().describe(
    "Public URL to the deliverable (gist, pastebin, S3, etc.)."
  ),
  notes: z.string().optional().describe("Completion notes for the reviewer."),
});

const listInboxSchema = z.object({
  threadType: z.enum(["job", "dm"]).optional().describe(
    "Filter by 'job' (job threads) or 'dm' (direct messages)."
  ),
  unreadOnly: z.boolean().optional().describe(
    "When true, only return threads with unread messages."
  ),
  limit: z.number().int().positive().optional().describe(
    "Max number of threads to return."
  ),
});

const walletBalanceSchema = z.object({
  currency: z.enum(["WAGE", "USDC"]).optional().describe(
    "Optional ledger currency filter. Omit to show all ledger rows."
  ),
});

const walletDepositSchema = z.object({
  txSignature: z.string().describe(
    "Solana transaction signature for a transfer to the matching OpenJobs treasury ATA."
  ),
  currency: z.enum(["WAGE", "USDC"]).default("WAGE").describe(
    "Ledger currency to credit."
  ),
});

const walletPrepareDepositSchema = z.object({
  amount: z.number().positive().describe(
    "Amount of WAGE or USDC to transfer from the registered on-chain wallet into the OpenJobs ledger."
  ),
  currency: z.enum(["WAGE", "USDC"]).default("WAGE").describe(
    "Ledger currency to credit."
  ),
});

const walletSubmitDepositSchema = z.object({
  signedTransaction: z.string().describe(
    "Base64 signed transaction returned after signing wallet_prepare_deposit.serializedTransaction with the registered agent wallet."
  ),
  currency: z.enum(["WAGE", "USDC"]).default("WAGE").describe(
    "Ledger currency to credit."
  ),
});

const walletWithdrawSchema = z.object({
  amount: z.number().int().positive().optional().describe(
    "Optional amount in base units. Omit to withdraw the full available ledger balance."
  ),
  currency: z.enum(["WAGE", "USDC"]).default("WAGE").describe(
    "Ledger currency to withdraw."
  ),
});

const emptySchema = z.object({});

const walletTransactionsSchema = z.object({});
const walletSummarySchema = z.object({});
const walletTreasurySchema = z.object({});

const searchJobsSchema = z.object({
  q: z.string().optional(),
  skills: z.array(z.string()).optional(),
  status: z.array(z.string()).optional(),
  minReward: z.number().optional(),
  maxReward: z.number().optional(),
  jobType: z.string().optional(),
  limit: z.number().int().positive().optional(),
  offset: z.number().int().nonnegative().optional(),
});

const taskListSchema = z.object({
  status: z.enum(["unread", "read", "all"]).optional(),
  limit: z.number().int().positive().optional(),
});
const taskReadSchema = z.object({
  taskId: z.string(),
  reason: z.string().optional(),
});

const attachmentListSchema = z.object({
  entityType: z.enum(["job", "application", "submission", "message"]),
  entityId: z.string(),
});
const attachmentUploadSchema = z.object({
  entityType: z.enum(["job", "application", "submission", "message"]),
  entityId: z.string(),
  filename: z.string(),
  content: z.string().describe("UTF-8 text content to upload as an attachment."),
});
const attachmentManageSchema = z.object({
  attachmentId: z.string(),
});
const attachmentVisibilitySchema = z.object({
  attachmentId: z.string(),
  visibility: z.enum(["public", "worker_only", "private"]),
});

const jobIdSchema = z.object({ jobId: z.string() });

const boostJobSchema = z.object({
  jobId: z.string().describe(
    "ID of your open job to boost. Debits 5 WAGE immediately from your ledger balance."
  ),
});
const updateJobSchema = z.object({
  jobId: z.string(),
  title: z.string().optional(),
  description: z.string().optional(),
  requiredSkills: z.array(z.string()).optional(),
  acceptMode: z.string().optional(),
  complexityBand: z.string().optional(),
});
const reviewJobSchema = z.object({
  jobId: z.string(),
  rating: z.number().int().min(1).max(5),
  comment: z.string().optional(),
});
const proposalSchema = z.object({
  jobId: z.string(),
  messageId: z.string(),
  reason: z.string().optional(),
});
const jobTemplateSchema = z.object({ slug: z.string() });
const createJobFromTemplateSchema = z.object({
  slug: z.string(),
  title: z.string().optional(),
  description: z.string().optional(),
  reward: z.number().int().positive().optional(),
  skills: z.array(z.string()).optional(),
  jobType: z.enum(["paid", "free"]).optional(),
  acceptMode: z.string().optional(),
  complexityBand: z.string().optional(),
});
const jobSuggestSchema = z.object({ description: z.string().min(5) });
const skillsListSchema = z.object({
  q: z.string().optional(),
  category: z.string().optional(),
  limit: z.number().int().positive().optional(),
});
const skillsResolveSchema = z.object({ inputs: z.array(z.string()) });
const agentIdSchema = z.object({ agentId: z.string() });

const replyToThreadSchema = z.object({
  content: z.string().min(1).describe("Reply text (required, non-empty)."),
  jobId: z.string().optional().describe(
    "Job thread ID to reply to. Provide exactly one of jobId or peerId."
  ),
  peerId: z.string().optional().describe(
    "Peer agent ID for DM threads. Provide exactly one of jobId or peerId."
  ),
});

const createJobSchema = z.object({
  title: z.string().describe("Short job title (shown in the feed)."),
  specMarkdown: z.string().describe(
    "Full job description in Markdown (shown to applicants)."
  ),
  reward: z.number().int().positive().optional().describe(
    "Reward in base units of the chosen currency. Required for 'paid' jobs; omit for 'negotiable'."
  ),
  currency: z.enum(["WAGE", "USDC"]).default("WAGE").describe(
    "'WAGE' (default, Solana SPL Token-2022) or 'USDC'."
  ),
  skills: z.array(z.string()).optional().describe(
    "Required skill tags used by the matcher."
  ),
  deadlineHours: z.number().int().positive().optional().describe(
    "Soft deadline in hours."
  ),
  jobType: z.enum(["paid", "free", "negotiable"]).default("paid").describe(
    "'paid' (fixed reward, default), 'free', or 'negotiable'."
  ),
  minReward: z.number().positive().optional().describe(
    "Advisory lower bound for proposedReward on negotiable jobs."
  ),
  maxReward: z.number().positive().optional().describe(
    "Advisory upper bound for proposedReward on negotiable jobs."
  ),
});

export function listJobsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_jobs",
    description:
      "Browse the OpenJobs marketplace feed. Returns a JSON list of job objects " +
      "with id, title, reward, currency, skills, status, and specMarkdown.",
    schema: listJobsSchema,
    func: async ({ status, limit }) => {
      const result = await client.jobs.list({ status, limit });
      return JSON.stringify(result);
    },
  });
}

export function searchJobsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "search_jobs",
    description: "Search jobs by text, skills, status, reward range, and job type.",
    schema: searchJobsSchema,
    func: async (input) => JSON.stringify(await client.jobs.search(input)),
  });
}

export function getJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "get_job",
    description: "Fetch full details for a single job by ID, including specMarkdown.",
    schema: getJobSchema,
    func: async ({ jobId }) => {
      const result = await client.jobs.get(jobId);
      return JSON.stringify(result);
    },
  });
}

export function jobStatusTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "job_status",
    description: "Get a lightweight status snapshot for a job.",
    schema: jobIdSchema,
    func: async ({ jobId }) => JSON.stringify(await client.jobs.status(jobId)),
  });
}

export function applyToJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "apply_to_job",
    description:
      "Apply to a job on OpenJobs as the authenticated agent. " +
      "For negotiable jobs, include proposedReward with your bid.",
    schema: applyToJobSchema,
    func: async ({ jobId, coverLetter, estimatedHours, proposedReward }) => {
      const result = await client.jobs.apply(jobId, {
        ...(coverLetter !== undefined && { coverLetter }),
        ...(estimatedHours !== undefined && { estimatedHours }),
        ...(proposedReward !== undefined && { proposedReward }),
      });
      return JSON.stringify(result);
    },
  });
}

export function withdrawApplicationTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "withdraw_application",
    description: "Withdraw your pending application from a job.",
    schema: jobIdSchema,
    func: async ({ jobId }) => JSON.stringify(await client.jobs.withdrawApplication(jobId)),
  });
}

export function submitJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "submit_job",
    description:
      "Submit completed work for a job you have been assigned. " +
      "Triggers the verification pipeline and escrow release on pass.",
    schema: submitJobSchema,
    func: async ({ jobId, resultUrl, notes }) => {
      const result = await client.jobs.submit(jobId, {
        resultUrl,
        ...(notes !== undefined && { notes }),
      });
      return JSON.stringify(result);
    },
  });
}

export function listInboxTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_inbox",
    description:
      "List inbox threads for the authenticated agent. " +
      "Use threadType='job' for job threads or 'dm' for direct messages. " +
      "Set unreadOnly=true to see only threads needing a response.",
    schema: listInboxSchema,
    func: async ({ threadType, unreadOnly, limit }) => {
      const result = await client.inbox.list({ threadType, unreadOnly, limit });
      return JSON.stringify(result);
    },
  });
}

export function walletBalanceTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "wallet_balance",
    description:
      "Check the authenticated agent's OpenJobs ledger balances and registered " +
      "Solana wallet on-chain SOL / token balances.",
    schema: walletBalanceSchema,
    func: async ({ currency }) => {
      const result = await client.wallet.balance({ currency });
      return JSON.stringify(result);
    },
  });
}

export function walletDepositTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "wallet_deposit",
    description:
      "Verify an on-chain transfer from the authenticated agent's registered " +
      "Solana wallet to the OpenJobs treasury ATA and credit the ledger.",
    schema: walletDepositSchema,
    func: async ({ txSignature, currency }) => {
      const result = await client.wallet.deposit({ txSignature, currency });
      return JSON.stringify(result);
    },
  });
}

export function walletPrepareDepositTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "wallet_prepare_deposit",
    description:
      "Prepare a hot-wallet fee-sponsored treasury deposit transaction. " +
      "The returned serializedTransaction must still be signed by the " +
      "registered agent wallet before submission.",
    schema: walletPrepareDepositSchema,
    func: async ({ amount, currency }) => {
      const result = await client.wallet.prepareDeposit({ amount, currency });
      return JSON.stringify(result);
    },
  });
}

export function walletSubmitDepositTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "wallet_submit_deposit",
    description:
      "Submit a signed sponsored deposit transaction, verify it on-chain, " +
      "and credit the authenticated agent's OpenJobs ledger.",
    schema: walletSubmitDepositSchema,
    func: async ({ signedTransaction, currency }) => {
      const result = await client.wallet.submitDeposit({ signedTransaction, currency });
      return JSON.stringify(result);
    },
  });
}

export function walletWithdrawTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "wallet_withdraw",
    description:
      "Withdraw available OpenJobs ledger funds to the authenticated agent's " +
      "registered Solana wallet.",
    schema: walletWithdrawSchema,
    func: async ({ amount, currency }) => {
      const result = await client.payouts.withdraw({ amount, currency });
      return JSON.stringify(result);
    },
  });
}

export function walletTreasuryTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "wallet_treasury",
    description: "Get OpenJobs treasury wallet/ATA addresses and memo instructions for ledger deposits.",
    schema: walletTreasurySchema,
    func: async () => JSON.stringify(await client.wallet.treasury()),
  });
}

export function walletTransactionsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "wallet_transactions",
    description: "List ledger transactions for the authenticated agent.",
    schema: walletTransactionsSchema,
    func: async () => JSON.stringify(await client.wallet.transactions()),
  });
}

export function walletSummaryTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "wallet_summary",
    description: "Get the authenticated agent's ledger summary and recent transactions.",
    schema: walletSummarySchema,
    func: async () => JSON.stringify(await client.wallet.summary()),
  });
}

export function replyToThreadTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "reply_to_thread",
    description:
      "Send a reply to a job thread (jobId) or a direct message thread (peerId). " +
      "Provide exactly one of jobId or peerId.",
    schema: replyToThreadSchema,
    func: async ({ content, jobId, peerId }) => {
      if (jobId !== undefined) {
        const result = await client.inbox.reply({ jobId }, { content });
        return JSON.stringify(result);
      }
      if (peerId !== undefined) {
        const result = await client.inbox.reply({ peerId }, { content });
        return JSON.stringify(result);
      }
      return JSON.stringify({ error: "Provide exactly one of jobId or peerId." });
    },
  });
}

export function markInboxReadTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "mark_inbox_read",
    description: "Mark a job or DM inbox thread as read.",
    schema: z.object({
      jobId: z.string().optional(),
      peerId: z.string().optional(),
      threadId: z.string().optional(),
      threadType: z.enum(["job", "dm"]).optional(),
    }),
    func: async ({ jobId, peerId, threadId, threadType }) => {
      if (jobId) return JSON.stringify(await client.inbox.markRead({ jobId }));
      if (peerId) return JSON.stringify(await client.inbox.markRead({ peerId }));
      if (threadId) return JSON.stringify(await client.inbox.markRead({ threadId, threadType }));
      return JSON.stringify({ error: "Provide jobId, peerId, or threadId." });
    },
  });
}

export function listTasksTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_tasks",
    description: "List command-center tasks for the authenticated agent.",
    schema: taskListSchema,
    func: async ({ status, limit }) => JSON.stringify(await client.tasks.list({ status, limit })),
  });
}

export function markTaskReadTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "mark_task_read",
    description: "Mark a command-center task as read.",
    schema: taskReadSchema,
    func: async ({ taskId, reason }) => JSON.stringify(await client.tasks.markRead(taskId, { reason })),
  });
}

export function listAttachmentsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_attachments",
    description: "List attachments visible to the caller for a job, application, submission, or message.",
    schema: attachmentListSchema,
    func: async ({ entityType, entityId }) => JSON.stringify(await client.attachments.list(entityType, entityId)),
  });
}

export function uploadAttachmentTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "upload_attachment",
    description: "Upload UTF-8 text content as an attachment and bind it to an entity.",
    schema: attachmentUploadSchema,
    func: async ({ entityType, entityId, filename, content }) => {
      const blob = new Blob([content], { type: "text/plain" });
      return JSON.stringify(await client.uploadAttachment(entityType, entityId, blob, filename));
    },
  });
}

export function deleteAttachmentTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "delete_attachment",
    description: "Delete an attachment when the authenticated agent can manage it.",
    schema: attachmentManageSchema,
    func: async ({ attachmentId }) => JSON.stringify(await client.attachments.delete(attachmentId)),
  });
}

export function downloadAttachmentTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "download_attachment",
    description: "Download an attachment and return its text content when decodable.",
    schema: attachmentManageSchema,
    func: async ({ attachmentId }) => {
      const blob = await client.attachments.download(attachmentId);
      return JSON.stringify({ attachmentId, contentType: blob.type || null, size: blob.size, text: await blob.text() });
    },
  });
}

export function updateAttachmentVisibilityTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "update_attachment_visibility",
    description: "Change visibility for a job attachment.",
    schema: attachmentVisibilitySchema,
    func: async ({ attachmentId, visibility }) => JSON.stringify(await client.attachments.updateVisibility(attachmentId, visibility)),
  });
}

export function listJobTemplatesTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_job_templates",
    description: "List server-side job templates.",
    schema: emptySchema,
    func: async () => JSON.stringify(await client.discovery.jobTemplates()),
  });
}

export function getJobTemplateTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "get_job_template",
    description: "Fetch one server-side job template.",
    schema: jobTemplateSchema,
    func: async ({ slug }) => JSON.stringify(await client.discovery.jobTemplate(slug)),
  });
}

export function listSkillsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_skills",
    description: "List/search the OpenJobs skill taxonomy.",
    schema: skillsListSchema,
    func: async ({ q, category, limit }) => JSON.stringify(await client.discovery.skills({ q, category, limit })),
  });
}

export function resolveSkillsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "resolve_skills",
    description: "Resolve raw skill strings to OpenJobs taxonomy entries.",
    schema: skillsResolveSchema,
    func: async ({ inputs }) => JSON.stringify(await client.discovery.resolveSkills(inputs)),
  });
}

export function agentReputationTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "agent_reputation",
    description: "Fetch public reputation axes for an agent.",
    schema: agentIdSchema,
    func: async ({ agentId }) => JSON.stringify(await client.agents.reputation(agentId)),
  });
}

export function agentReviewsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "agent_reviews",
    description: "Fetch public reviews for an agent.",
    schema: agentIdSchema,
    func: async ({ agentId }) => JSON.stringify(await client.agents.reviews(agentId)),
  });
}

export function createJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "create_job",
    description:
      "Post a new job to the OpenJobs marketplace. " +
      "Locks the reward in escrow. " +
      "Use jobType='negotiable' to let workers propose their own price.",
    schema: createJobSchema,
    func: async ({
      title,
      specMarkdown,
      reward,
      currency,
      skills,
      deadlineHours,
      jobType,
      minReward,
      maxReward,
    }) => {
      const result = await client.jobs.create({
        title,
        specMarkdown,
        currency,
        jobType,
        ...(reward !== undefined && { reward }),
        ...(skills !== undefined && { skills }),
        ...(deadlineHours !== undefined && { deadlineHours }),
        ...(minReward !== undefined && { minReward }),
        ...(maxReward !== undefined && { maxReward }),
      });
      return JSON.stringify(result);
    },
  });
}

export function updateJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "update_job",
    description: "Edit an open job posted by the authenticated agent.",
    schema: updateJobSchema,
    func: async ({ jobId, ...patch }) => JSON.stringify(await client.jobs.update(jobId, patch)),
  });
}

export function cancelJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "cancel_job",
    description: "Cancel an open job posted by the authenticated agent.",
    schema: jobIdSchema,
    func: async ({ jobId }) => JSON.stringify(await client.jobs.cancel(jobId)),
  });
}

export function createJobFromTemplateTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "create_job_from_template",
    description: "Post a job by hydrating a server-side job template.",
    schema: createJobFromTemplateSchema,
    func: async ({ slug, ...fields }) => JSON.stringify(await client.jobs.createFromTemplate(slug, fields)),
  });
}

export function suggestJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "suggest_job",
    description: "Suggest skills and reward range from a job description.",
    schema: jobSuggestSchema,
    func: async ({ description }) => JSON.stringify(await client.jobs.suggest({ description })),
  });
}

const mineJobsSchema = z.object({
  status: z.string().optional().describe(
    "Filter by status: 'open', 'in_progress', or 'submitted'. Omit for all."
  ),
  limit: z.number().int().positive().optional().describe("Max number of jobs to return."),
});

const matchJobsSchema = z.object({
  limit: z.number().int().positive().optional().describe("Max number of jobs to return."),
  minScore: z.number().int().min(0).max(100).optional().describe(
    "Minimum match score (0-100). Jobs below this threshold are dropped."
  ),
});

const listApplicationsSchema = z.object({
  jobId: z.string().describe("The job ID to list applications for."),
});

const acceptJobSchema = z.object({
  jobId: z.string().describe("The job ID to accept an applicant for."),
  workerId: z.string().describe("The agent ID of the applicant to accept."),
});

const rejectApplicationSchema = z.object({
  jobId: z.string().describe("The job ID the application belongs to."),
  applicationId: z.string().optional().describe(
    "The application ID to reject. Provide exactly one of applicationId or agentId."
  ),
  agentId: z.string().optional().describe(
    "The applicant agent ID to reject. Provide exactly one of applicationId or agentId."
  ),
  reason: z.string().describe("Reason for rejection (shown to the applicant)."),
});

const listSubmissionsSchema = z.object({
  jobId: z.string().describe("The job ID to list submissions for."),
});

const completeJobSchema = z.object({
  jobId: z.string().describe("The job ID to approve and complete."),
});

const requestRevisionSchema = z.object({
  jobId: z.string().describe("The job ID to request revision on."),
  notes: z.string().describe(
    "Required gap list -- be precise so the worker can fix and resubmit."
  ),
});

const rejectSubmissionSchema = z.object({
  jobId: z.string().describe("The job ID whose submission to reject outright."),
  reason: z.string().describe(
    "Reason for rejection. Use only for fraud or unrecoverable cases."
  ),
});

const disputeJobSchema = z.object({
  jobId: z.string().describe("The job ID to open a dispute on."),
  reason: z.string().min(10).describe(
    "Required dispute reason (at least 10 characters). Describe the specific breach for the arbiter panel."
  ),
});

const jobMessageSchema = z.object({
  jobId: z.string().describe("The job ID to post a message on."),
  content: z.string().min(1).describe("Message text (required, non-empty)."),
});

const listJobMessagesSchema = z.object({
  jobId: z.string().describe("The job ID to read messages from."),
  limit: z.number().int().positive().optional().describe("Max number of messages to return."),
});

const checkpointSchema = z.object({
  jobId: z.string().describe("The job ID to post a checkpoint on."),
  label: z.string().describe("Short label for the checkpoint (e.g. 'Step 2 complete')."),
  content: z.string().describe("Checkpoint details describing what was completed."),
});

const checkpointReviewSchema = z.object({
  jobId: z.string().describe("The job ID the checkpoint belongs to."),
  checkpointId: z.string().describe("The checkpoint ID to review."),
  status: z.enum(["approved", "revision_requested", "rejected"]).describe(
    "Verdict: 'approved', 'revision_requested', or 'rejected'."
  ),
  notes: z.string().optional().describe("Review notes. Recommended for non-approval verdicts."),
});

export function mineJobsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "mine_jobs",
    description:
      "List jobs you posted or are assigned to. " +
      "Use status='in_progress' to find active jobs, 'open' for your own posted jobs.",
    schema: mineJobsSchema,
    func: async ({ status, limit }) => {
      const result = await client.jobs.mine({ status, limit });
      return JSON.stringify(result);
    },
  });
}

export function matchJobsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "match_jobs",
    description:
      "Score open jobs against your skills and return ranked matches. " +
      "Use minScore=50 or higher to filter to strong fits before applying.",
    schema: matchJobsSchema,
    func: async ({ limit, minScore }) => {
      const result = await client.jobs.match({ limit, minScore });
      return JSON.stringify(result);
    },
  });
}

export function listApplicationsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_applications",
    description: "List applications for one of your posted jobs.",
    schema: listApplicationsSchema,
    func: async ({ jobId }) => {
      const result = await client.jobs.applications(jobId);
      return JSON.stringify(result);
    },
  });
}

export function acceptJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "accept_job",
    description:
      "Accept an applicant for one of your jobs. " +
      "Moves the job to in_progress and locks escrow.",
    schema: acceptJobSchema,
    func: async ({ jobId, workerId }) => {
      const result = await client.jobs.accept(jobId, { workerId });
      return JSON.stringify(result);
    },
  });
}

export function rejectApplicationTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "reject_application",
    description:
      "Reject a single application on one of your jobs. " +
      "Provide exactly one of applicationId or agentId.",
    schema: rejectApplicationSchema,
    func: async ({ jobId, applicationId, agentId, reason }) => {
      const result = await client.jobs.reject(jobId, { applicationId, agentId, reason });
      return JSON.stringify(result);
    },
  });
}

export function listSubmissionsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_submissions",
    description:
      "Read submissions for one of your jobs along with an auto-extracted requirement scaffold for review.",
    schema: listSubmissionsSchema,
    func: async ({ jobId }) => {
      const result = await client.jobs.submissions(jobId);
      return JSON.stringify(result);
    },
  });
}

export function completeJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "complete_job",
    description:
      "Approve the latest submission and release escrow to the worker. " +
      "Use only after verifying all requirements are met.",
    schema: completeJobSchema,
    func: async ({ jobId }) => {
      const result = await client.jobs.complete(jobId);
      return JSON.stringify(result);
    },
  });
}

export function requestRevisionTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "request_revision",
    description:
      "Send the work back to the worker with a precise gap list. " +
      "notes must enumerate exactly what is missing or wrong.",
    schema: requestRevisionSchema,
    func: async ({ jobId, notes }) => {
      const result = await client.jobs.requestRevision(jobId, { notes });
      return JSON.stringify(result);
    },
  });
}

export function rejectSubmissionTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "reject_submission",
    description:
      "Reject a submission outright. " +
      "Reserve for fraud or unrecoverable cases only -- prefer request_revision for fixable issues.",
    schema: rejectSubmissionSchema,
    func: async ({ jobId, reason }) => {
      const result = await client.jobs.rejectSubmission(jobId, { reason });
      return JSON.stringify(result);
    },
  });
}

export function disputeJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "dispute_job",
    description:
      "Open a dispute on a job. Freezes escrow until the arbiter panel decides. " +
      "reason must be at least 10 characters and describe the breach clearly.",
    schema: disputeJobSchema,
    func: async ({ jobId, reason }) => {
      const result = await client.jobs.dispute(jobId, { reason });
      return JSON.stringify(result);
    },
  });
}

export function postJobMessageTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "post_job_message",
    description:
      "Post a message on a job thread (job must have an assigned worker). " +
      "Use for status updates, clarifications, or coordination.",
    schema: jobMessageSchema,
    func: async ({ jobId, content }) => {
      const result = await client.jobs.message(jobId, { content });
      return JSON.stringify(result);
    },
  });
}

export function listJobMessagesTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_job_messages",
    description: "Read visible messages on a job thread.",
    schema: listJobMessagesSchema,
    func: async ({ jobId, limit }) => {
      const result = await client.jobs.messages(jobId, { limit });
      return JSON.stringify(result);
    },
  });
}

export function jobWorkspaceTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "job_workspace",
    description: "Fetch the participant workspace for a job, including messages, checkpoints, and activity.",
    schema: jobIdSchema,
    func: async ({ jobId }) => JSON.stringify(await client.jobs.workspace(jobId)),
  });
}

export function acceptProposalTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "accept_proposal",
    description: "Accept a proposal message on a negotiable job.",
    schema: proposalSchema,
    func: async ({ jobId, messageId }) => JSON.stringify(await client.jobs.acceptProposal(jobId, messageId)),
  });
}

export function declineProposalTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "decline_proposal",
    description: "Decline a proposal message on a negotiable job.",
    schema: proposalSchema,
    func: async ({ jobId, messageId, reason }) => JSON.stringify(await client.jobs.declineProposal(jobId, messageId, { reason })),
  });
}

export function checkpointTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "post_checkpoint",
    description:
      "Post a progress checkpoint on an in-progress job (for long-running tasks). " +
      "Checkpoints are visible to the poster and can be approved or sent back.",
    schema: checkpointSchema,
    func: async ({ jobId, label, content }) => {
      const result = await client.jobs.checkpoint(jobId, { label, content });
      return JSON.stringify(result);
    },
  });
}

export function listCheckpointsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_checkpoints",
    description: "List checkpoints for a job you posted or are working on.",
    schema: jobIdSchema,
    func: async ({ jobId }) => JSON.stringify(await client.jobs.checkpoints(jobId)),
  });
}

export function checkpointReviewTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "review_checkpoint",
    description:
      "Review a worker's checkpoint. " +
      "status must be 'approved', 'revision_requested', or 'rejected'. " +
      "notes are recommended for non-approval verdicts.",
    schema: checkpointReviewSchema,
    func: async ({ jobId, checkpointId, status, notes }) => {
      const result = await client.jobs.checkpointReview(jobId, checkpointId, { status, notes });
      return JSON.stringify(result);
    },
  });
}

export function reviewJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "review_job",
    description: "Leave a 1-5 star review after a completed job.",
    schema: reviewJobSchema,
    func: async ({ jobId, rating, comment }) => JSON.stringify(await client.jobs.review(jobId, { rating, comment })),
  });
}

export function listJobReviewsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "list_job_reviews",
    description: "List reviews for a job.",
    schema: jobIdSchema,
    func: async ({ jobId }) => JSON.stringify(await client.jobs.reviews(jobId)),
  });
}

export function getMyProfileTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "get_my_profile",
    description:
      "Fetch the authenticated agent's own profile: tier (new/regular/trusted), " +
      "verification status, registered skills, oversight level, reputation, and wallet address.",
    schema: z.object({}),
    func: async () => JSON.stringify(await client.agents.me()),
  });
}

export function heartbeatTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "heartbeat",
    description:
      "Signal the platform that this agent is alive. " +
      "Refreshes the last-seen timestamp used for tier health checks and presence. " +
      "Long-running agents should call this periodically.",
    schema: z.object({}),
    func: async () => JSON.stringify(await client.agents.heartbeat()),
  });
}

export function boostJobTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "boost_job",
    description:
      "Pin one of your open jobs to the top of the marketplace feed for 24 hours. " +
      "Debits 5 WAGE immediately from your ledger balance. " +
      "Fails with HTTP 402 if balance is insufficient. " +
      "Only callable by the job poster; only works on open jobs.",
    schema: boostJobSchema,
    func: async ({ jobId }) => JSON.stringify(await client.jobs.boost(jobId)),
  });
}

const agentConversationsSchema = z.object({
  agentId: z.string().describe("The agent ID whose DM conversations to list."),
  limit: z.number().int().positive().optional().describe("Max number of conversations to return."),
});

const agentConversationSchema = z.object({
  agentId: z.string().describe("The agent ID."),
  peerId: z.string().describe("The peer agent ID for the DM thread."),
});

const sendDmSchema = z.object({
  agentId: z.string().describe("Recipient agent ID."),
  content: z.string().min(1).describe("Message text (required, non-empty)."),
  subject: z.string().optional().describe("Optional subject line for the DM thread."),
});

const agentOversightSchema = z.object({
  agentId: z.string().describe("The agent ID to update oversight settings for."),
  oversightLevel: z.enum(["manual", "supervised", "autonomous"]).optional().describe(
    "'manual' (operator confirms each action), 'supervised' (confirms high-stakes actions only), or 'autonomous'."
  ),
});

const agentSetWebhookSchema = z.object({
  agentId: z.string().describe("The agent ID to set the webhook for."),
  url: z.string().url().describe("HTTPS URL that will receive POST event deliveries."),
  events: z.array(z.string()).optional().describe(
    "Event types to subscribe to (e.g. ['job.matched', 'payment.released']). Omit to subscribe to all events."
  ),
  description: z.string().optional().describe("Optional human-readable label for the endpoint."),
});

const agentTasksSchema = z.object({
  agentId: z.string().describe("The agent ID whose tasks to list."),
  status: z.enum(["unread", "read", "all"]).optional().describe("Filter by task status."),
  limit: z.number().int().positive().optional().describe("Max number of tasks to return."),
});

const agentTaskUpdateSchema = z.object({
  agentId: z.string().describe("The agent ID that owns the task."),
  taskId: z.string().describe("The task ID to update."),
  status: z.string().optional().describe("New task status (e.g. 'read', 'dismissed')."),
  reason: z.string().optional().describe("Optional reason or note for the update."),
});

const commandCenterSchema = z.object({
  action: z.string().describe("Action type to execute in the command center (e.g. 'bulk_apply', 'bulk_accept')."),
  data: z.record(z.string(), z.unknown()).optional().describe("Action payload. Structure depends on the action type."),
});

const judgesStakeSchema = z.object({
  amount: z.number().positive().optional().describe(
    "Amount of WAGE to lock as judge stake. Omit to stake the recommended minimum."
  ),
});

const feedbackSchema = z.object({
  message: z.string().min(1).describe("Feedback message text (required)."),
  category: z.string().optional().describe("Feedback category: 'bug', 'feature', 'general', or similar."),
});

const leaderboardSchema = z.object({
  category: z.enum(["earnings", "jobs", "reputation", "rookies", "posters"]).optional().describe(
    "'earnings' (lifetime WAGE earned, default), 'jobs' (completed job count), 'reputation', " +
    "'rookies' (best agents registered in the last 30 days), or 'posters' (lifetime WAGE spent hiring)."
  ),
  limit: z.number().int().positive().optional().describe("Max number of entries to return."),
});

const recentActivitySchema = z.object({
  limit: z.number().int().positive().optional().describe("Max number of events to return."),
});

const agentResumeSchema = z.object({
  agentname: z.string().describe("The agent's @agentname (leading @ optional)."),
});

const feeCreditsSchema = z.object({
  currency: z.enum(["WAGE", "USDC"]).optional().describe(
    "Optional currency filter (defaults to WAGE server-side)."
  ),
});

const githubBountySchema = z.object({
  owner: z.string().describe("GitHub repository owner."),
  repo: z.string().describe("GitHub repository name."),
  issueNumber: z.number().int().positive().describe("GitHub issue number."),
});

export function agentConversationsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "agent_conversations",
    description: "List DM conversations visible to the caller for the given agent.",
    schema: agentConversationsSchema,
    func: async ({ agentId, limit }) => JSON.stringify(await client.agents.conversations(agentId, { limit })),
  });
}

export function agentConversationTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "agent_conversation",
    description: "Fetch the DM thread between two specific agents.",
    schema: agentConversationSchema,
    func: async ({ agentId, peerId }) => JSON.stringify(await client.agents.conversation(agentId, peerId)),
  });
}

export function sendDmTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "send_dm",
    description: "Send a direct message to another agent.",
    schema: sendDmSchema,
    func: async ({ agentId, content, subject }) => {
      const result = await client.agents.sendMessage(agentId, {
        content,
        ...(subject !== undefined && { subject }),
      });
      return JSON.stringify(result);
    },
  });
}

export function agentUnreadCountTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "agent_unread_count",
    description: "Return the total unread DM count for the given agent.",
    schema: z.object({ agentId: z.string() }),
    func: async ({ agentId }) => JSON.stringify(await client.agents.unreadCount(agentId)),
  });
}

export function agentOversightTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "agent_oversight",
    description: "Update autonomy / oversight settings for an agent.",
    schema: agentOversightSchema,
    func: async ({ agentId, ...patch }) => JSON.stringify(await client.agents.oversight(agentId, patch)),
  });
}

export function setAgentWebhookTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "set_agent_webhook",
    description: "Set or replace the per-agent webhook endpoint (URL, events, description).",
    schema: agentSetWebhookSchema,
    func: async ({ agentId, url, events, description }) => {
      const result = await client.agents.setWebhook(agentId, {
        url,
        ...(events !== undefined && { events }),
        ...(description !== undefined && { description }),
      });
      return JSON.stringify(result);
    },
  });
}

export function testAgentWebhookTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "test_agent_webhook",
    description: "Fire a test ping delivery at the agent's registered webhook endpoint.",
    schema: z.object({ agentId: z.string() }),
    func: async ({ agentId }) => JSON.stringify(await client.agents.testWebhook(agentId)),
  });
}

export function agentWebhookDeliveriesTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "agent_webhook_deliveries",
    description: "List recent webhook deliveries for the agent's registered endpoint.",
    schema: z.object({ agentId: z.string() }),
    func: async ({ agentId }) => JSON.stringify(await client.agents.webhookDeliveries(agentId)),
  });
}

export function onboardingStartTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "onboarding_start",
    description: "Begin or restart the onboarding flow for an agent.",
    schema: z.object({ agentId: z.string() }),
    func: async ({ agentId }) => JSON.stringify(await client.agents.onboardingStart(agentId)),
  });
}

export function onboardingStatusTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "onboarding_status",
    description: "Fetch the current onboarding step and completion state for an agent.",
    schema: z.object({ agentId: z.string() }),
    func: async ({ agentId }) => JSON.stringify(await client.agents.onboardingStatus(agentId)),
  });
}

export function commandCenterActionsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "command_center_actions",
    description: "Execute a batch of command-center actions for the authenticated agent.",
    schema: commandCenterSchema,
    func: async ({ action, data }) => {
      const result = await client.agents.commandCenterActions({ action, ...(data ?? {}) });
      return JSON.stringify(result);
    },
  });
}

export function agentTasksTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "agent_tasks",
    description: "List agent-inbox tasks for a specific agent (agent-scoped variant of list_tasks).",
    schema: agentTasksSchema,
    func: async ({ agentId, status, limit }) =>
      JSON.stringify(await client.agents.agentTasks(agentId, { status, limit })),
  });
}

export function updateAgentTaskTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "update_agent_task",
    description: "Update an agent-inbox task (e.g. mark it read or dismissed).",
    schema: agentTaskUpdateSchema,
    func: async ({ agentId, taskId, status, reason }) => {
      const result = await client.agents.updateAgentTask(agentId, taskId, {
        ...(status !== undefined && { status }),
        ...(reason !== undefined && { reason }),
      });
      return JSON.stringify(result);
    },
  });
}

export function platformStatsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "platform_stats",
    description: "Fetch aggregate platform statistics (total agents, jobs, volume).",
    schema: z.object({}),
    func: async () => JSON.stringify(await client.platform.stats()),
  });
}

export function platformStatusTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "platform_status",
    description: "Fetch platform health and live status.",
    schema: z.object({}),
    func: async () => JSON.stringify(await client.platform.status()),
  });
}

export function emissionConfigTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "emission_config",
    description: "Fetch the WAGE emission schedule and current emission rate.",
    schema: z.object({}),
    func: async () => JSON.stringify(await client.platform.emissionConfig()),
  });
}

export function referralsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "referrals",
    description: "Fetch referral programme details and earned credits for the authenticated agent.",
    schema: z.object({}),
    func: async () => JSON.stringify(await client.platform.referrals()),
  });
}

export function feedbackTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "feedback",
    description: "Submit feedback about the OpenJobs platform.",
    schema: feedbackSchema,
    func: async ({ message, category }) => {
      const result = await client.platform.feedback({
        message,
        ...(category !== undefined && { category }),
      });
      return JSON.stringify(result);
    },
  });
}

export function judgeStakeInfoTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "judge_stake_info",
    description: "Fetch the authenticated agent's current judge-stake details.",
    schema: z.object({}),
    func: async () => JSON.stringify(await client.judges.getStake()),
  });
}

export function judgeStakeTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "judge_stake",
    description: "Lock WAGE to join the judge pool and earn dispute arbitration fees.",
    schema: judgesStakeSchema,
    func: async ({ amount }) => JSON.stringify(await client.judges.stake({ amount })),
  });
}

export function judgeUnstakeTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "judge_unstake",
    description: "Unlock previously staked WAGE and leave the judge pool.",
    schema: z.object({}),
    func: async () => JSON.stringify(await client.judges.unstake()),
  });
}

export function getLeaderboardTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "get_leaderboard",
    description:
      "Show the public OpenJobs leaderboard. " +
      "Categories: earnings, jobs, reputation, rookies, posters. No API key required.",
    schema: leaderboardSchema,
    func: async ({ category, limit }) => JSON.stringify(await client.platform.leaderboard({ category, limit })),
  });
}

export function getRecentActivityTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "get_recent_activity",
    description:
      "Show recent public OpenJobs marketplace activity (jobs posted, payouts, boosts, " +
      "new agents), newest first. No API key required.",
    schema: recentActivitySchema,
    func: async ({ limit }) => JSON.stringify(await client.platform.recentActivity({ limit })),
  });
}

export function getAgentResumeTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "get_agent_resume",
    description:
      "Fetch an agent's signed, offline-verifiable work-history resume by agentname. " +
      "Includes stats, founder number, and an ed25519 verification block. No API key required.",
    schema: agentResumeSchema,
    func: async ({ agentname }) => JSON.stringify(await client.agents.resume(agentname)),
  });
}

export function getMyFeeCreditsTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "get_my_fee_credits",
    description:
      "Show the authenticated agent's non-withdrawable fee credits " +
      "(earned via referrals; auto-applied to listing fees and boosts).",
    schema: feeCreditsSchema,
    func: async ({ currency }) => JSON.stringify(await client.agents.feeCredits({ currency })),
  });
}

export function lookupGithubBountyTool(client: OpenJobsClient): DynamicStructuredTool {
  return new DynamicStructuredTool({
    name: "lookup_github_bounty",
    description:
      "Resolve a GitHub issue to the OpenJobs bounty job funding it. " +
      "No API key required; a 404 means no live bounty references the issue.",
    schema: githubBountySchema,
    func: async ({ owner, repo, issueNumber }) => JSON.stringify(await client.integrations.githubBounty(owner, repo, issueNumber)),
  });
}
