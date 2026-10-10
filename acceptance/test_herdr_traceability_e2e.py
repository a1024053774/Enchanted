#!/usr/bin/env python3
"""T-073 public CLI/Git contract; fake Herdr is explicit, no model calls.

Replay: python3 -B acceptance/test_herdr_traceability_e2e.py --artifacts NEW_DIR
--scripts-root selects a frozen candidate/mutant; expected values are independent.
"""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import uuid

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
ARTIFACTS = None
COMMANDS = []


class Contract(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="t073-contract-", dir="/tmp")).resolve()
        self.artifacts = ARTIFACTS / self._testMethodName
        self.artifacts.mkdir()
        self.env = {k:v for k,v in os.environ.items() if not k.startswith(("A2A_", "GIT_CONFIG_"))}
        self.env.update(HERDR_ENV="1", GIT_AUTHOR_NAME="contract", GIT_AUTHOR_EMAIL="contract@example.invalid",
                        GIT_COMMITTER_NAME="contract", GIT_COMMITTER_EMAIL="contract@example.invalid",
                        PYTHONDONTWRITEBYTECODE="1")
        self.git("init", "-q", "-b", "master")
        roles = self.root / ".project-map/roles"
        roles.mkdir(parents=True)
        (roles / "worker.md").write_text("独立 fixture worker 角色卡\n", encoding="utf-8")
        (self.root / "seed.txt").write_text("independent seed\n", encoding="utf-8")
        self.git("add", ".project-map", "seed.txt")
        self.git("commit", "-qm", "seed")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        self.fakebin = self.root / "explicit-fake-herdr"
        self.fakebin.mkdir()
        fake = self.fakebin / "herdr"
        fake.write_text("#!"+sys.executable+"\n"+'''
import json,os,sys
from pathlib import Path
args=sys.argv[1:]
with Path(os.environ['FAKE_CALLS']).open('a') as f:f.write(json.dumps(args)+'\\n')
if args[:2]==['pane','split']:
 print(json.dumps({'result':{'pane':{'pane_id':'fake:pane'}}}))
elif args[:2]==['pane','run']:
 Path(os.environ['FAKE_EXPORT']).write_text(args[3])
 # Actual Herdr 0.9.3 pane run succeeds with an empty stdout.
elif args[:2]==['agent','start']:
 if os.environ.get('FAKE_FAIL_START'):
  print('explicit fake startup failure',file=sys.stderr);sys.exit(12)
 print(json.dumps({'result':{'type':'agent_started','argv':['codex',*args[args.index('--')+1:]]}}))
else:sys.exit(2)
''', encoding="utf-8")
        fake.chmod(0o755)
        self.env.update(PATH=str(self.fakebin)+os.pathsep+self.env["PATH"],
                        FAKE_CALLS=str(self.root/"fake-calls.jsonl"), FAKE_EXPORT=str(self.root/"fake-export.txt"))
        self.task = "T-sentinel-" + uuid.uuid4().hex[:10] + "-1"
        self.attempt, self.session = "attempt-"+uuid.uuid4().hex, "session-"+uuid.uuid4().hex

    def tearDown(self):
        with tarfile.open(self.artifacts / "fixture.tar.gz", "w:gz") as archive:
            archive.add(self.root, arcname="fixture")
        (self.artifacts / "location.txt").write_text(str(self.root)+"\n",encoding="utf-8")

    def run_command(self, argv, env=None, expected=0):
        r = subprocess.run(argv, cwd=self.root, env=env or self.env, text=True, capture_output=True, timeout=20)
        COMMANDS.append(dict(case=self._testMethodName, argv=[str(a) for a in argv], cwd=str(self.root),
                             exit_code=r.returncode, stdout=r.stdout, stderr=r.stderr))
        if expected is None:
            self.assertNotEqual(r.returncode, 0, r.stdout+r.stderr)
        else:
            self.assertEqual(r.returncode, expected, r.stdout+r.stderr)
        return r

    def git(self, *args, env=None, expected=0):
        return self.run_command(["git", *args], env=env, expected=expected)

    def launch(self, attempt=None, env=None, expected=0):
        self.assertTrue((SCRIPTS / "launch-worker").is_file(), "EXPECTED_RED launch entry missing")
        r = self.run_command([str(SCRIPTS / "launch-worker"), "--root", str(self.root), "--cwd", str(self.root),
                              "--agent", "fixture-worker", "--project", "sentinel-project", "--task", self.task,
                              "--attempt", attempt or self.attempt, "--session", self.session], env=env, expected=expected)
        if expected:
            return r
        return json.loads(r.stdout)["launch_id"]

    def managed_env(self):
        import shlex
        exports = shlex.split((self.root/"fake-export.txt").read_text())[1:]
        env = dict(self.env, CODEX_THREAD_ID="native-"+uuid.uuid4().hex)
        env.update(v.split("=",1) for v in exports)
        return env

    def rows(self, name):
        return [json.loads(line) for line in (self.root/"records"/name).read_text(encoding="utf-8").splitlines()]

    def assert_trailers(self, env, launch_id):
        message = self.git("log", "-1", "--format=%B").stdout
        (self.artifacts / ("message-"+uuid.uuid4().hex+".txt")).write_text(message,encoding="utf-8")
        actual = [line for line in message.splitlines() if line.startswith("A2A-")]
        self.assertEqual(len(actual), 9, message)
        expected = {"A2A-Task":self.task,"A2A-Attempt":self.attempt,"A2A-Session":self.session,
                    "A2A-Role":"worker","A2A-Tool":"codex-cli 0.162.1","A2A-Model":"gpt-6.1-sol",
                    "A2A-Effort":"xhigh","A2A-Native-Session":env["CODEX_THREAD_ID"],"A2A-Launch":launch_id}
        self.assertEqual(dict(line.split(": ",1) for line in actual),expected)
        bound = self.rows("launches.jsonl")[-1]
        self.assertEqual(bound["native_session"],env["CODEX_THREAD_ID"])
        self.assertEqual(bound["project_commit"],self.base)
        self.assertEqual(bound["argv"], ["codex","-m","gpt-6.1-sol","-c",'model_reasoning_effort="xhigh"',
                                           "-c",'service_tier="fast"',"-c","check_for_update_on_startup=false",
                                           "--sandbox","workspace-write","--ask-for-approval","on-request"])

    def hook(self, name, body):
        path = self.root / ".git/hooks" / name
        path.write_text("#!/bin/sh\n"+body,encoding="utf-8")
        path.chmod(0o755)

    def test_commit_no_verify_and_plain_counterexample(self):
        launch = self.launch()
        env = self.managed_env()
        self.hook("prepare-commit-msg", "echo original >> hook-trace.txt\n")
        self.hook("pre-commit", "echo pre-commit >> pre-trace.txt\n")
        self.git("commit","--allow-empty","-m","独立输入 café "+uuid.uuid4().hex,env=env)
        self.assert_trailers(env,launch)
        self.git("commit","--no-verify","--allow-empty","-m","second",env=env)
        self.assert_trailers(env,launch)
        self.assertEqual((self.root/"hook-trace.txt").read_text().splitlines(),["original","original"])
        self.assertEqual((self.root/"pre-trace.txt").read_text().splitlines(),["pre-commit"])
        self.git("commit","--allow-empty","-m","plain")
        self.assertNotIn("A2A-",self.git("log","-1","--format=%B").stdout)

    def test_original_failure_missing_env_and_damaged_launch(self):
        self.launch()
        env = self.managed_env()
        self.hook("prepare-commit-msg", "echo failure >> hook-trace.txt\nexit 19\n")
        self.git("commit","--allow-empty","-m","must fail",env=env,expected=None)
        self.assertEqual(self.git("rev-parse","HEAD").stdout.strip(),self.base)
        self.assertEqual((self.root/"hook-trace.txt").read_text().splitlines(),["failure"])
        (self.root/".git/hooks/prepare-commit-msg").unlink()
        missing=dict(env);del missing["A2A_SESSION"]
        self.git("commit","--allow-empty","-m","missing env",env=missing,expected=None)
        wrong=dict(env,A2A_TASK="unassigned-task")
        self.git("commit","--allow-empty","-m","wrong task",env=wrong,expected=None)
        logfile=self.root/"records/launches.jsonl"
        with logfile.open("ab") as f:f.write(b'{"partial":')
        before=logfile.read_bytes()
        self.git("commit","--allow-empty","-m","broken log",env=env,expected=None)
        self.assertEqual(logfile.read_bytes(),before)

    def test_duplicate_trailers_keep_body_and_project_trailer(self):
        launch=self.launch();env=self.managed_env()
        body="独立重复尾注输入 "+uuid.uuid4().hex
        signed="Signed-off-by: External Sentinel <sentinel@example.invalid>"
        message=body+"\n\nA2A-Task: obsolete-one\nA2A-Task: obsolete-two\nA2A-Model: obsolete-model\n"+signed+"\n"
        self.git("commit","--allow-empty","-m",message,env=env)
        self.assert_trailers(env,launch)
        actual=self.git("log","-1","--format=%B").stdout
        self.assertIn(body,actual);self.assertIn(signed,actual)
        self.assertNotIn("obsolete-one",actual);self.assertNotIn("obsolete-two",actual)

    def test_amend_rebase_merge_and_native_replacement(self):
        launch=self.launch();env=self.managed_env()
        self.git("commit","--allow-empty","-m","first",env=env)
        self.git("commit","--amend","--no-edit","--allow-empty",env=env)
        self.assert_trailers(env,launch)
        self.git("checkout","-qb","side",self.base,env=env)
        (self.root/"side.txt").write_text("side\n",encoding="utf-8")
        self.git("add","side.txt",env=env);self.git("commit","-qm","side",env=env)
        self.git("rebase","master",env=env)
        self.assert_trailers(env,launch)
        self.git("checkout","master",env=env)
        (self.root/"main.txt").write_text("main\n",encoding="utf-8")
        self.git("add","main.txt",env=env);self.git("commit","-qm","main",env=env)
        self.git("merge","--no-ff","side","-m","merge",env=env)
        self.assert_trailers(env,launch)
        self.git("commit","--allow-empty","-m","replacement",env=dict(env,CODEX_THREAD_ID="wrong-native"),expected=None)

    def facts(self):
        p=self.root/"facts.json"
        p.write_text(json.dumps(dict(task_type="构建与基础设施",complexity="M",delivery_rounds=2,
                                    elapsed_seconds=93,human_interventions=1,
                                    rejections={"identity_version":0,"path_boundary":0,"completion":1,"red_state":0,
                                                "rule_checks":0,"independent_review":0,"commit_trailers":0}),ensure_ascii=False),encoding="utf-8")
        return p

    def score(self, launch, extra=(), expected=0):
        return self.run_command([str(SCRIPTS/"score"),"--root",str(self.root),"--launch",launch,
                                "--facts",str(self.facts()),"--result","通过","--boundary-discipline","3",
                                "--boundary-reason","遵守边界","--engineering-taste","2",
                                "--engineering-reason","可用，需要小幅整理",*extra],expected=expected)

    def test_score_required_abandon_upgrade_and_user(self):
        launch=self.launch()
        self.score(launch,expected=None) # notes is mandatory even when empty.
        self.assertFalse((self.root/"records/scores.jsonl").exists())
        row=json.loads(self.score(launch,("--notes","复核完成")).stdout)
        self.assertEqual(row["facts"]["elapsed_seconds"],93)
        self.assertEqual(row["facts"]["delivery_rounds"],2)
        self.assertEqual(row["task"],self.task)
        before=(self.root/"records/scores.jsonl").read_bytes()
        self.score(launch,("--notes","duplicate"),expected=None)
        self.assertEqual((self.root/"records/scores.jsonl").read_bytes(),before)
        user=self.run_command([str(SCRIPTS/"score"),"--root",str(self.root),"--source","user","--score-of",row["score_id"],
                               "--boundary-discipline","1","--boundary-reason","用户边界评价",
                               "--engineering-taste","3","--engineering-reason","用户工程评价","--notes",""])
        self.assertEqual(self.rows("scores.jsonl")[0],row)
        self.assertEqual(json.loads(user.stdout)["source"],"user")
        abandoned=self.launch(attempt="abandon-sentinel")
        a=self.run_command([str(SCRIPTS/"score"),"--root",str(self.root),"--launch",abandoned,"--result","放弃","--reason","外部条件变化"])
        self.assertEqual(json.loads(a.stdout)["data"],{"result":"放弃","reason":"外部条件变化"})
        self.assertNotIn("facts",json.loads(a.stdout))
        upgraded=self.launch(attempt="upgrade-sentinel")
        self.run_command([str(SCRIPTS/"score"),"--root",str(self.root),"--launch",upgraded,"--facts",str(self.facts()),
                          "--result","升级","--boundary-discipline","2","--boundary-reason","边界可接受",
                          "--engineering-taste","1","--engineering-reason","需更强执行器","--notes",""])
        self.assertEqual([r["data"].get("result") for r in self.rows("scores.jsonl")],["通过",None,"放弃","升级"])

    def test_score_concurrency_corruption_and_start_failure(self):
        launches=[self.launch(attempt="concurrent-"+str(i)) for i in range(5)]
        facts=self.facts()
        def score_one(launch):
            return self.run_command([str(SCRIPTS/"score"),"--root",str(self.root),"--launch",launch,"--facts",str(facts),
                                     "--result","通过","--boundary-discipline","3","--boundary-reason","reason",
                                     "--engineering-taste","3","--engineering-reason","reason","--notes",""])
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(score_one,launches))
        self.assertEqual(len(self.rows("scores.jsonl")),5)
        log=self.root/"records/scores.jsonl"
        with log.open("ab") as f:f.write(b'{"partial":')
        before=log.read_bytes();self.score(launches[0],("--notes",""),expected=None)
        self.assertEqual(log.read_bytes(),before)
        failed_env=dict(self.env,FAKE_FAIL_START="1")
        self.launch(attempt="failure",env=failed_env,expected=12)
        self.assertEqual(self.rows("launches.jsonl")[-1]["phase"],"failed")
        calls=[json.loads(line) for line in (self.root/"fake-calls.jsonl").read_text().splitlines()]
        self.assertEqual(sum(a[:2]==["agent","start"] for a in calls),6)
        self.assertFalse(any("close" in a for a in calls))

    def test_score_missing_or_unknown_check_rejected(self):
        launch=self.launch()
        facts=self.facts()
        good=json.loads(facts.read_text(encoding="utf-8"))
        for rejected in ({"not_a_gate_check":0}, {key:value for key,value in good["rejections"].items() if key!="independent_review"}):
            bad=dict(good,rejections=rejected)
            facts.write_text(json.dumps(bad,ensure_ascii=False),encoding="utf-8")
            self.run_command([str(SCRIPTS/"score"),"--root",str(self.root),"--launch",launch,"--facts",str(facts),
                              "--result","通过","--boundary-discipline","3","--boundary-reason","reason",
                              "--engineering-taste","3","--engineering-reason","reason","--notes",""],expected=None)
            self.assertFalse((self.root/"records/scores.jsonl").exists())


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--artifacts",type=Path,required=True)
    p.add_argument("--scripts-root",type=Path,default=SCRIPTS)
    p.add_argument("--case")
    args=p.parse_args()
    ARTIFACTS=args.artifacts.resolve();ARTIFACTS.mkdir()
    SCRIPTS=args.scripts_root.resolve()
    suite=unittest.defaultTestLoader.loadTestsFromName(args.case,Contract) if args.case else unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    (ARTIFACTS/"commands.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False)+"\n" for r in COMMANDS),encoding="utf-8")
    (ARTIFACTS/"summary.json").write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                                                      scripts_root=str(SCRIPTS)),indent=2)+"\n",encoding="utf-8")
    sys.exit(0 if result.wasSuccessful() else 1)
