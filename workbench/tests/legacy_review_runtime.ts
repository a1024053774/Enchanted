// The worker service is an external fixture. Reviewer launches use real Panes
// with only PTY/process observations supplied by controlled_quality_pty.ts.
export function withReviewerRuntime(worker: any, panes: any) {
  const reviewers = new Set<string>();
  return {
    ...worker,
    createReview: async (task: any, review: any, prompt: string) => {
      reviewers.add(review.thread_id);
      await panes.createReview(task, review, prompt);
    },
    readThread: (thread: string) => reviewers.has(thread) ? panes.readThread(thread) : worker.readThread(thread),
    stopThread: (thread: string) => reviewers.has(thread) ? panes.stopThread(thread) : worker.stopThread(thread),
    archiveThread: (thread: string) => reviewers.has(thread) ? panes.archiveThread(thread) : worker.archiveThread(thread),
    sessionFacts: (thread: string) => reviewers.has(thread) ? panes.sessionFacts(thread) : worker.sessionFacts(thread),
  };
}
