"""Regressions for abstention, Git provenance and the separation of the three routes."""
import json
from pathlib import Path
import tempfile
import unittest

from router import Router, wordforms


class MachineRouteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.commit = "a" * 40
        (self.base/"manifest.json").write_text(json.dumps({"commit": self.commit}))
        rows=[
            ("codec.py","1"*40,"python"),("verify.py","2"*40,"python"),
            ("ports.h","3"*40,"header"),("unused.py","4"*40,"python")]
        self.write("files.jsonl",[{"path":p,"blob":b,"mode":"100644","lang":lang} for p,b,lang in rows])
        self.write("symbols.jsonl",[{"path":"codec.py","blob":rows[0][1],"line":5,"name":"PacketFrame_AVX2","kind":"py_class"},
                                     {"path":"unused.py","blob":"0"*40,"line":1,"name":"PacketFrame_AVX2","kind":"py_class"}])
        edges=[]
        for i,confidence in [(1,"exact"),(2,"candidate")]:
            edges.append({"src":rows[0][0],"src_blob":rows[0][1],"dst":rows[i][0],"dst_blob":rows[i][1],
                          "rel":"named_import","confidence":confidence,"line":4,"token":"target"})
        self.write("edges.jsonl",edges)
        ref=lambda i: {"role":"primary" if i==0 else "support","path":rows[i][0],"blob":rows[i][1]}
        rec={"key":"checked-format","kind":"reviewed","commit":self.commit,"evidence":[ref(0),ref(2)],
             "atoms":[["PacketFrame_AVX2","validates","format_boundary"]]}
        self.write("machine-records.jsonl",[rec,dict(rec,key="invalid-ref",evidence=[dict(ref(3),blob="0"*40)])])

    def write(self,name,rows):
        (self.base/name).write_text("".join(json.dumps(r)+"\n" for r in rows))

    def route(self,mode,text):
        return Router(self.base,self.base/"machine-records.jsonl",mode=mode).query(text)

    def test_token_preservation(self):
        self.assertIn("avx2",wordforms("PacketFrame_AVX2"))
        self.assertIn("packet",wordforms("PacketFrame_AVX2"))

    def test_exact_graph_and_roles(self):
        base=self.route("lexical","PacketFrame_AVX2")
        self.assertEqual(base["paths"],["codec.py"])
        self.assertEqual(base["hits"][0]["tags"][0]["line"],5)
        graph=self.route("graph","PacketFrame_AVX2")
        self.assertEqual(graph["paths"],["codec.py","verify.py"])
        self.assertEqual(graph["hits"][1]["edge"]["line"],4)

    def test_typed_claim_and_stale_evidence(self):
        semantic=self.route("semantic","PacketFrame_AVX2 format")
        refs={r["path"]:r for r in semantic["hits"]}
        self.assertEqual(refs["ports.h"]["claim"]["key"],"checked-format")
        self.assertNotIn("unused.py",refs)

    def test_abstention(self):
        self.assertEqual(self.route("graph","不存在的 LostProtocol 如何校验")["status"],"abstain")
        self.assertEqual(self.route("lexical","呢吗呀")["paths"],[])


if __name__ == "__main__":
    unittest.main()
