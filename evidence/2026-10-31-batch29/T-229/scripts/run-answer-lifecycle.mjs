// T-229: runs answerLifecycleContracts on its own (test_t108_questions stops before it when hookFailureContracts fails).
// argv[2] = workbench directory, argv[3] = output JSON path.
const { answerLifecycleContracts } = await import(process.argv[2] + '/tests/t108_answer_lifecycle_contracts.mjs');
const { writeFileSync } = await import('node:fs');
const timer = setTimeout(() => { writeFileSync(process.argv[3], JSON.stringify({ status: 'HUNG' }) + '\n', { flag: 'wx' }); process.exit(3); }, 120000);
const cases = await answerLifecycleContracts(); clearTimeout(timer);
writeFileSync(process.argv[3], JSON.stringify({ cases }, null, 2) + '\n', { flag: 'wx' });
console.log(cases.map(c => c.name + ':' + c.status).join(' '));
