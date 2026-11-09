// 诊断副本的追加场景；不修改任务卡完成条件文件。
// 独立契约：非空的既有 leader 绑定不能被新的 pane/live leader 取代。
for (const role of ['worker', 'reviewer']) {
  scenario('review sentinel bound-leader mismatch ' + role, ['timeout', 'bound-leader-mismatch', 'UPS'], async f => {
    const identity = role === 'worker' ? f.task.current_attempt.runtime_identity : f.task.review.runtime_identity;
    identity.leader_pid = 4099;
    f.saveTask();
    f.nativeStart();
    await assert.rejects(f.signal('UserPromptSubmit', { prompt: f.dispatch.text }), (error: any) => {
      f.observed.refusal = error.code;
      return error.code === 'identity_conflict';
    }, 'bound leader mismatch must refuse recovery');
    assert.equal(f.pane.failed, f.failed, 'startup failure remains');
    assert.equal(f.pane.active, f.active, 'original active remains');
    assert.equal(f.pane.state, 'unknown');
    assert.equal(f.writes.length, 2, 'no recovery input replay');
  }, role);
}
