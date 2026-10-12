import importlib.machinery, importlib.util, io, json, os, shutil, sys, tempfile, unittest, multiprocessing as mp
from contextlib import redirect_stdout, redirect_stderr
from datetime import timedelta
BIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "breakroom")

def load(home):
    os.environ["BREAKROOM_HOME"] = home
    loader = importlib.machinery.SourceFileLoader("breakroom_mod", BIN)
    spec = importlib.util.spec_from_loader("breakroom_mod", loader); m = importlib.util.module_from_spec(spec); loader.exec_module(m); return m

def _worker(args):
    home, i = args; m = load(home)
    with redirect_stdout(io.StringIO()):
        for j in range(20): m.main(["--as", f"bot{i}", "log", "--to", "all", "--kind", "status", f"w{i}-{j}"])
        m.main(["--as", f"bot{i}", "claim", f"unique job number {i} zebra{i*7919}", "--product", "p", "--force"])

class T(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(); self.m = load(self.home)
        json.dump({"bots": [{"id": "aaa-111111", "name": "Alpha (SF)", "tag": "(SF)", "owns": "builds", "does_not_own": ""},
                            {"id": "bbb-222222", "name": "Beta", "tag": "none", "owns": "pricing", "does_not_own": ""}]}, f := open(os.path.join(self.home, "registry.json"), "w")); f.close()
    def tearDown(self): shutil.rmtree(self.home)
    def run_cli(self, *argv):
        o, e = io.StringIO(), io.StringIO()
        with redirect_stdout(o), redirect_stderr(e): code = self.m.main(list(argv))
        return code, o.getvalue(), e.getvalue()

    def test_claim_check_dedupe(self):
        self.assertEqual(self.run_cli("--as", "Alpha", "claim", "Build landing page for Drippy", "--product", "drippy")[0], 0)
        code, out, _ = self.run_cli("check", "build drippy landing page")
        self.assertEqual(code, 3); self.assertIn("T-0001", out)
        self.assertEqual(self.run_cli("check", "file quarterly taxes")[0], 0)
        code, _, err = self.run_cli("--as", "Beta", "claim", "Build the landing page for Drippy", "--product", "drippy")
        self.assertEqual(code, 3); self.assertIn("refusing", err)
        self.assertEqual(self.run_cli("--as", "Beta", "claim", "Build the landing page for Drippy", "--product", "drippy", "--force")[0], 0)
        self.assertEqual(len(self.m.cards()), 2)
        self.assertEqual(self.m.cards()["T-0001"]["owner_agent_id"], "aaa-111111")  # name resolved via registry

    def test_stale_takeover(self):
        self.run_cli("--as", "Alpha", "claim", "Migrate database to postgres", "--product", "x")
        old = self.m.iso(self.m.now() - timedelta(hours=30))
        with self.m.Lock(): self.m.append("tasks", {"_op": "patch", "id": "T-0001", "heartbeat_at": old})
        code, out, _ = self.run_cli("--as", "Beta", "list", "--stale"); self.assertIn("T-0001", out)
        code, out, _ = self.run_cli("--as", "Beta", "claim", "Migrate database to postgres", "--product", "x")
        self.assertEqual(code, 0); self.assertIn("took over", out)
        c = self.m.cards()["T-0001"]; self.assertEqual(c["owner_name"], "Beta"); self.assertFalse(self.m.is_stale(c))
        self.assertEqual(len(self.m.cards()), 1)

    def test_superseded_and_expired_hidden(self):
        self.run_cli("announce", "--kind", "rule", "--title", "Old", "--body", "b")
        self.run_cli("announce", "--kind", "rule", "--title", "New", "--body", "b", "--supersedes", "A-0001")
        self.run_cli("announce", "--kind", "info", "--title", "Gone", "--body", "b", "--expires", "2020-01-01")
        titles = [a["title"] for a in json.loads(self.run_cli("--json", "announcements")[1])]
        self.assertEqual(titles, ["New"])
        self.assertEqual(len(json.loads(self.run_cli("announcements", "--all", "--json")[1])), 3)

    def test_ian_queue_dedupe(self):
        self.run_cli("--as", "Alpha", "claim", "Pick price for SubShark", "--product", "subshark")
        self.run_cli("--as", "Beta", "claim", "Totally different tax work", "--product", "subshark", "--force")
        self.run_cli("--as", "Alpha", "ask-ian", "T-0001", "Approve $9/mo price?")
        self.run_cli("--as", "Beta", "ask-ian", "T-0002", "approve $9/mo price")
        q = json.loads(self.run_cli("ian-queue", "--json")[1])
        self.assertEqual(len(q["subshark"]), 1); self.assertEqual(sorted(q["subshark"][0]["cards"]), ["T-0001", "T-0002"])
        self.run_cli("--as", "Alpha", "done", "T-0001"); self.run_cli("--as", "Beta", "done", "T-0002")
        self.assertEqual(json.loads(self.run_cli("ian-queue", "--json")[1]), {})

    def test_concurrent_appends(self):
        with mp.get_context("fork").Pool(8) as p: p.map(_worker, [(self.home, i) for i in range(8)])
        lines = open(os.path.join(self.home, "events.jsonl")).read().splitlines()
        self.assertEqual(len(lines), 8 * 21); [json.loads(l) for l in lines]
        ids = sorted(self.m.cards()); self.assertEqual(ids, [f"T-{i:04d}" for i in range(1, 9)])

    def test_checkins_record_and_list(self):
        # no identity -> no check-in written
        self.run_cli("start")
        self.assertFalse(os.path.exists(os.path.join(self.home, "checkins.jsonl")))
        ev_before = open(os.path.join(self.home, "events.jsonl")).read() if os.path.exists(os.path.join(self.home, "events.jsonl")) else ""
        # with identity -> append checkins.jsonl only (not events)
        self.run_cli("--as", "Alpha", "start")
        self.run_cli("--as", "Alpha", "brief")  # alias also records
        lines = open(os.path.join(self.home, "checkins.jsonl")).read().splitlines()
        self.assertEqual(len(lines), 2)
        rows = [json.loads(l) for l in lines]
        for r in rows:
            self.assertEqual(r["agent_id"], "aaa-111111")
            self.assertEqual(r["agent_name"], "Alpha (SF)")
            self.assertIn("at", r)
        ev_after = open(os.path.join(self.home, "events.jsonl")).read() if os.path.exists(os.path.join(self.home, "events.jsonl")) else ""
        self.assertEqual(ev_before, ev_after)  # start must not touch events.jsonl
        # listing: Alpha seen, Beta never; most-recent first; window count
        code, out, _ = self.run_cli("checkins")
        self.assertEqual(code, 0)
        self.assertIn("Alpha (SF)", out); self.assertIn("Beta", out); self.assertIn("never", out)
        # Alpha line appears before Beta (seen before never)
        self.assertLess(out.index("Alpha (SF)"), out.index("Beta"))
        data = json.loads(self.run_cli("checkins", "--json")[1])
        self.assertEqual(data["checked_in"], 1)
        by_name = {b["agent_name"]: b for b in data["bots"]}
        self.assertNotEqual(by_name["Alpha (SF)"]["last_checkin"], "never")
        self.assertEqual(by_name["Beta"]["last_checkin"], "never")
        self.assertTrue(by_name["Alpha (SF)"]["in_window"])
        self.assertFalse(by_name["Beta"]["in_window"])

    def test_json_outputs(self):
        self.run_cli("--as", "Alpha", "claim", "Write spec", "--product", "p")
        self.run_cli("--as", "Beta", "object", "T-0001", "scope too big")
        self.run_cli("decide", "--product", "p", "Price is $5")
        for cmd in (["start", "--as", "Alpha"], ["announcements"], ["list"], ["show", "T-0001"], ["check", "write spec"],
                    ["ian-queue"], ["decisions"], ["who", "pricing"], ["digest"]):
            _, out, _ = self.run_cli(*cmd, "--json"); json.loads(out)
        s = json.loads(self.run_cli("--json", "start", "--as", "Alpha")[1]); self.assertEqual(len(s["my_cards"]), 1)
        d = json.loads(self.run_cli("digest", "--json")[1]); self.assertEqual(len(d["objections"]), 1)
        self.assertEqual(json.loads(self.run_cli("who", "pricing", "--json")[1])[0]["name"], "Beta")

if __name__ == "__main__": unittest.main()

class HtmlTests(unittest.TestCase):
    def test_html_renders_and_escapes(self):
        home = tempfile.mkdtemp()
        try:
            m = load(home)
            with redirect_stdout(io.StringIO()):
                m.main(["--as", "tester", "claim", "Fix <script>alert(1)</script> widget", "--product", "demo", "--goal", "g"])
                m.main(["--as", "tester", "claim", "Plain card title", "--product", "demo", "--force"])
                m.main(["html"])
            h = open(os.path.join(home, "board.html")).read()
            self.assertIn("<!doctype html>", h); self.assertIn("Plain card title", h)
            self.assertNotIn("<script>alert", h); self.assertIn("&lt;script&gt;", h)
            for sec in ("Announcements", "Waiting on Ian", "Task board", "Decisions", "Recent activity", "Bot directory", "Last check-in"): self.assertIn(sec, h)
        finally: shutil.rmtree(home)
