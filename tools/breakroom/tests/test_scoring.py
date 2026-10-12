import io, json, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_breakroom import load

BOTS = ["Alpha", "Beta", "Gamma", "Delta"]
class S(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(); self.m = m = load(self.home)
        regs = [{"id": f"id-{n.lower()}", "name": n, "tag": "none", "owns": "", "does_not_own": ""} for n in BOTS]
        regs.append({"id": "room-1", "name": "Grok Bot, Ian Kinney", "tag": "none", "owns": "", "does_not_own": ""})
        with open(os.path.join(self.home, "registry.json"), "w") as f: json.dump({"bots": regs}, f)
        # freeze time on Wednesday of a known week (Sat 2026-10-10 .. Fri 2026-10-16 17:00)
        self.t = datetime(2026, 10, 14, 12, 0, tzinfo=m.TZ); m.now = lambda: self.t
        self.calls = []; m.gh_get = self.fake_gh; self.gh = {}
    def tearDown(self): shutil.rmtree(self.home)
    def fake_gh(self, path):
        self.calls.append(path)
        if path not in self.gh: raise OSError("boom")
        return self.gh[path]
    def cli(self, *argv):
        o, e = io.StringIO(), io.StringIO(); code = 0
        with redirect_stdout(o), redirect_stderr(e):
            try: code = self.m.main(list(argv))
            except SystemExit as x: code = x.code
        return code, o.getvalue(), e.getvalue()
    def say(self, who, text="hello"): return json.loads(self.cli("--as", who, "--json", "say", text)[1])["id"]
    def react(self, who, iid, v="like"): return self.cli("--as", who, "react", iid, v)
    def board(self, week="current"): return json.loads(self.cli("--json", "leaderboard", "--week", week)[1])
    def row(self, sc, bot): return next(r for r in sc["rows"] + sc["ineligible"] if r["bot"] == bot)

    def test_ids_and_backfill(self):
        self.cli("--as", "Alpha", "claim", "Thing", "--product", "p")
        with self.m.Lock(): self.m.append("tasks", {"_op": "patch", "id": "T-0001", "comments": [{"by": "Beta", "kind": "note", "text": "old", "at": self.m.iso()}]})
        self.cli("--as", "Gamma", "advise", "T-0001", "new one")
        ids = [c["id"] for c in self.m.cards()["T-0001"]["comments"]]; self.assertEqual(ids, ["C-0001", "C-0002"])
        self.assertEqual(self.say("Alpha"), "N-0001")
        self.assertIn("note", [e["kind"] for e in self.m.read_jsonl("events")])
        rows = json.loads(self.cli("--json", "feed")[1]); self.assertEqual({r["id"] for r in rows}, {"C-0001", "C-0002", "N-0001"})

    def test_react_own_rejected_and_rules(self):
        n = self.say("Alpha")
        self.assertNotEqual(self.react("Alpha", n)[0], 0)
        self.assertNotEqual(self.cli("react", n, "like")[0], 0)  # identity required
        self.assertNotEqual(self.react("Beta", "A-0001")[0], 0); self.assertNotEqual(self.react("Beta", "T-0001")[0], 0)
        self.assertEqual(self.react("Beta", n)[0], 0)

    def test_latest_reaction_wins(self):
        n = self.say("Alpha"); self.say("Beta")
        self.react("Beta", n, "like"); self.t += timedelta(minutes=1); self.react("Beta", n, "dislike")
        r = self.row(self.board(), "Alpha"); self.assertEqual((r["likes"], r["dislikes"]), (0, 1))
        self.t += timedelta(minutes=1); self.react("Beta", n, "clear")
        r = self.row(self.board(), "Alpha"); self.assertEqual((r["likes"], r["dislikes"], r["social"]), (0, 0, 0))

    def test_like_cap_per_giver(self):
        ns = [self.say("Alpha", f"n{i}") for i in range(5)]; self.say("Beta")
        for n in ns: self.react("Beta", n)
        r = self.row(self.board(), "Alpha"); self.assertEqual((r["likes"], r["social"]), (3, 3))

    def test_half_weight_non_author(self):
        n = self.say("Alpha"); self.react("Beta", n); self.react("Gamma", n, "dislike")  # neither authored
        r = self.row(self.board(), "Alpha"); self.assertEqual(r["social"], 0.5 - 0.25)

    def test_normalization_total_eligibility(self):
        a = self.say("Alpha"); b = self.say("Beta"); self.say("Gamma")
        self.react("Beta", a); self.react("Gamma", a); self.react("Alpha", b)
        self.react("Delta", b)  # Delta authored nothing: half weight, and not eligible
        self.cli("--as", "Ian", "react", a, "like")  # Ian half weight (no notes), never ranked
        sc = self.board(); names = [r["bot"] for r in sc["rows"]]
        self.assertNotIn("Delta", names); self.assertNotIn("Ian", names)
        ra, rb = self.row(sc, "Alpha"), self.row(sc, "Beta")
        self.assertEqual(ra["social"], 2.5); self.assertEqual(ra["social_score"], 50); self.assertEqual(rb["social_score"], 30)
        self.assertEqual(ra["commit_score"], 0); self.assertEqual(ra["total"], 50)
        self.assertEqual(self.row(sc, "Gamma")["total"], 0)
        # room never ranked even if it posts
        self.cli("--as", "Grok Bot, Ian Kinney", "say", "hi"); self.assertNotIn("Grok Bot, Ian Kinney", [r["bot"] for r in self.board()["rows"]])

    def test_tiebreak(self):
        a = self.say("Alpha"); self.t += timedelta(minutes=1); b = self.say("Beta"); self.t += timedelta(minutes=1); self.say("Gamma"); self.t += timedelta(minutes=1); self.say("Delta")
        self.react("Gamma", a); self.react("Gamma", b); self.react("Delta", b)  # Beta: 2 likers; Alpha gets 2nd like from Gamma below
        a2 = self.say("Alpha", "second"); self.react("Gamma", a2)
        sc = self.board(); self.assertEqual(self.row(sc, "Alpha")["social"], self.row(sc, "Beta")["social"])
        self.assertEqual([r["bot"] for r in sc["rows"][:2]], ["Beta", "Alpha"])  # 2 distinct likers beats 1
        # notes count, then earlier first note
        sc2 = self.m.score_week(*self.m.pick_week("current"))
        g, d = self.row(sc2, "Gamma"), self.row(sc2, "Delta")
        self.assertLess(g["rank"], d["rank"])  # all else equal: Gamma's first note is earlier
        self.say("Delta", "extra")
        sc3 = self.m.score_week(*self.m.pick_week("current")); self.assertLess(self.row(sc3, "Delta")["rank"], self.row(sc3, "Gamma")["rank"])

    def test_week_boundary_friday_5pm(self):
        m = self.m; s, e = m.week_bounds(datetime(2026, 10, 16, 16, 59, tzinfo=m.TZ))
        self.assertEqual((s.isoformat(), e.isoformat()), ("2026-10-10T00:00:00-04:00", "2026-10-16T17:00:00-04:00"))
        self.t = datetime(2026, 10, 16, 16, 59, tzinfo=m.TZ); a = self.say("Alpha"); self.say("Beta"); self.react("Beta", a)
        self.t = datetime(2026, 10, 16, 17, 0, tzinfo=m.TZ); b = self.say("Alpha", "late"); self.react("Beta", b)
        sc = m.score_week(*m.week_bounds(datetime(2026, 10, 14, tzinfo=m.TZ)))
        r = self.row(sc, "Alpha"); self.assertEqual((r["likes"], r["notes"]), (1, 1))
        self.assertEqual(m.ended_week()[0].isoformat(), "2026-10-10T00:00:00-04:00")  # at 17:00 Friday the week has ended
        self.t = datetime(2026, 10, 17, 0, 0, tzinfo=m.TZ); self.assertEqual(m.week_bounds(self.t)[0].date().isoformat(), "2026-10-17")

    def test_botw_finalize_idempotent(self):
        a = self.say("Alpha"); self.say("Beta"); self.react("Beta", a)
        self.assertNotEqual(self.cli("botw", "--finalize")[0], 0)  # week has not ended (it's Wednesday)
        self.t = datetime(2026, 10, 16, 17, 5, tzinfo=self.m.TZ)
        code, out, _ = self.cli("botw"); self.assertIn("PREVIEW", out); self.assertFalse(os.path.exists(os.path.join(self.home, "awards.jsonl")))
        self.assertEqual(self.cli("botw", "--finalize")[0], 0)
        self.assertEqual(self.cli("botw", "--finalize")[0], 3)
        aw = self.m.read_jsonl("awards"); self.assertEqual(len(aw), 1); self.assertEqual(aw[0]["winner"], "Alpha"); self.assertEqual(aw[0]["runner_up"], "Beta")
        anns = self.m.active_announcements(); self.assertEqual(anns[0]["title"], "Bot of the Week: Alpha"); self.assertEqual(anns[0]["kind"], "goal")
        # next week supersedes previous BotW announcement
        self.t = datetime(2026, 10, 20, 9, 0, tzinfo=self.m.TZ); b = self.say("Beta"); self.say("Alpha"); self.react("Alpha", b)
        self.t = datetime(2026, 10, 23, 18, 0, tzinfo=self.m.TZ); self.assertEqual(self.cli("botw", "--finalize")[0], 0)
        titles = [x["title"] for x in self.m.active_announcements() if x["title"].startswith("Bot of the Week")]
        self.assertEqual(titles, ["Bot of the Week: Beta"])

    def test_commit_counting_mocked(self):
        U = "https://github.com/o/r/pull/7"; U2 = "https://github.com/o/r/pull/8"; SHA = "https://github.com/o/r/commit/abcdef1"
        self.gh = {"/repos/o/r/pulls/7": {"merged_at": "2026-10-13T15:00:00Z"}, "/repos/o/r/pulls/7/commits?per_page=100": [{}] * 30,
                   "/repos/o/r/pulls/8": {"merged_at": "2026-10-01T15:00:00Z"}, "/repos/o/r/pulls/8/commits?per_page=100": [{}] * 5,
                   "/repos/o/r/commits/abcdef1": {"commit": {"committer": {"date": "2026-10-12T10:00:00Z"}}}}
        self.cli("--as", "Alpha", "claim", "Ship it", "--product", "p", "--link", f"{U} (green)", "--link", U2, "--link", SHA)
        self.cli("--as", "Beta", "help", "T-0001", "on it"); self.say("Alpha"); self.say("Beta")
        sc = self.board(); a, b = self.row(sc, "Alpha"), self.row(sc, "Beta")
        self.assertEqual(a["commits"], 21); self.assertEqual(b["commits"], 10.5)   # cap 20 + 1 direct commit; helper 50%
        self.assertEqual(a["commit_score"], 50); self.assertEqual(b["commit_score"], 25); self.assertFalse(sc["partial"])
        n = len(self.calls); self.board(); self.assertEqual(len(self.calls), n)  # merged PRs cached permanently
        self.assertIn(U, self.m.load_cache())
        # fail soft: an API error marks partial instead of crashing
        self.cli("--as", "Gamma", "claim", "Other job entirely zebra", "--product", "q", "--link", "https://github.com/o/r/pull/99")
        sc = self.board(); self.assertTrue(sc["partial"]); self.assertEqual(self.row(sc, "Alpha")["commits"], 21)

    def test_start_sections_and_html(self):
        self.cli("--as", "Beta", "say", "tip: use --json")
        _, out, _ = self.cli("--as", "Alpha", "start")
        for s in ("LOBBY", "THIS WEEK", "react with: breakroom react <id> like", "You haven't left a note this week."): self.assertIn(s, out)
        self.assertIn("N-0001", out); self.say("Alpha")
        self.assertNotIn("You haven't left a note", self.cli("--as", "Alpha", "start")[1])
        self.cli("html")
        with open(os.path.join(self.home, "board.html")) as f: h = f.read()
        for s in ("Lobby", "This Week", "Past Bots of the Week"): self.assertIn(s, h)

if __name__ == "__main__": unittest.main()
