import unittest
import zlib
import struct

import geocode as g


VOCAB = {"A": ["source", "database"], "B": ["runtime", "storage"], "C": ["9", "7", "3"],
         "D": ["hotpath"], "E": ["L", "M", "S", "T"]}


def record(**fields):
    return {"id": "code:src/runner.py",
            "tags": {"A":"source", "B":"runtime", "C":"7", "E":"T"},
            "fields": fields}


class HexShapeTest(unittest.TestCase):
    def test_jointly_preserve_all_axes_and_roles(self):
        row = record(F="同一段文本", R="code:src/a.py,database:trades,code:src/a.py",
                     A="同一段文本", S="同一段文本")
        row["tags"]["D"] = "hotpath"
        cells = g.encode(row, VOCAB)
        self.assertEqual(g.object_id(cells), row["id"])
        self.assertEqual(g.decode(g.unpack(g.pack(reversed(cells))), VOCAB), row)
        self.assertEqual(g.relation_targets(cells), ["code:src/a.py","database:trades","code:src/a.py"])
        payloads = {payload for _, _, payload in cells if payload is not None}
        self.assertEqual(payloads, {"src/runner.py","src/a.py","trades","同一段文本"})
        self.assertIn((-2, 0, None), cells)
        self.assertIn((2, 2, "trades"), cells)

    def test_missing_absent_and_empty_are_distinct(self):
        rows = [record(), record(S="-"), record(S=""), record(S=" ")]
        shapes = [g.encode(row,VOCAB) for row in rows]
        self.assertEqual(len({g.pack(cells) for cells in shapes}), 4)
        self.assertEqual([g.field_value(cells,"S") for cells in shapes], [None, "-", "", " "])
        self.assertEqual([g.decode(cells,VOCAB) for cells in shapes], rows)
        self.assertTrue(g.match_axis(shapes[0],VOCAB,"D","missing"))

    def test_role_is_read_from_the_port(self):
        row = record(F="α", S="β")
        cells = g.encode(row,VOCAB)
        board = {(q,r):value for q,r,value in cells}
        p,s = g.PORTS["F"],g.PORTS["S"]
        board[p],board[s] = board[s],board[p]
        moved = [(q,r,v) for (q,r),v in board.items()]
        self.assertEqual(g.field_value(moved,"S"),"α")
        self.assertEqual(g.field_value(moved,"F"),"β")
        g.validate(moved,VOCAB)

    def test_reference_literals_without_a_lossless_typed_parse(self):
        for raw in ["code:missing, database:orders", "see architecture", "code:", "", "-", " code:foo"]:
            with self.subTest(raw=raw):
                cells=g.encode(record(R=raw),VOCAB)
                self.assertEqual(g.relation_targets(cells), [])
                self.assertEqual(g.field_value(cells,"R"),raw)
                self.assertEqual(g.decode(cells,VOCAB),record(R=raw))

    def test_geometry_predicates_and_numeric_threshold(self):
        cells=g.encode(record(),VOCAB)
        for value in (6,"6","7",1):
            self.assertTrue(g.match_axis(cells,VOCAB,"C","gte",value))
        self.assertFalse(g.match_axis(cells,VOCAB,"C","gte",8))
        self.assertFalse(g.match_axis(cells,VOCAB,"C","gte","7.0"))
        self.assertTrue(g.match_axis(cells,VOCAB,"A","eq","SOURCE"))
        self.assertFalse(g.match_axis(cells,VOCAB,"C","eq","6"))
        self.assertTrue(g.match_axis(cells,VOCAB,"E","gte","T"))
        self.assertFalse(g.match_axis(cells,VOCAB,"E","gte","S"))

    def test_incomplete_or_conflicting_geometry_rejected(self):
        cells=g.encode(record(R="code:ok"),VOCAB)
        for bad in [cells+[(2,0,None)], cells+[(3,0,None)], cells+[(0,42,None)],
                    cells+[(7,1,"extra")], [c for c in cells if c[:2]!=g.PORTS["R"]],
                    [c for c in cells if c[:2]!=(0,2)],
                    [c if c[:2]!=(2,0) else (2,0,"shadow") for c in cells]]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    g.validate(bad,VOCAB)

    def test_bad_input_not_silently_projected(self):
        empty = record()
        for bad in [{**empty, "tags":{}}, {**empty, "fields":{"F":None}}, {**empty,"id":"other:thing"},
                    {**empty,"tags":{**empty["tags"],"D":"unknown"}}, {**empty,"extra":"lost"}]:
            with self.assertRaises(ValueError):
                g.encode(bad,VOCAB)
        changed=dict(VOCAB,B=list(reversed(VOCAB["B"])))
        self.assertNotEqual(g.dictionary_digest(VOCAB),g.dictionary_digest(changed))
        with self.assertRaises(ValueError):
            g.dictionary_digest(dict(VOCAB,B=["X","X"]))

    def test_compiled_board_owns_immutable_geometry(self):
        row = record(F="hi", R="database:orders")
        cells = g.encode(row,VOCAB)
        compiled = g.compiled_cells(cells,VOCAB)
        cells.clear()
        self.assertEqual(g.field_value(compiled,"F"),"hi")
        self.assertTrue(g.match_axis(compiled,VOCAB,"C","gte",6))
        self.assertEqual(g.relation_targets(compiled),["database:orders"])
        self.assertEqual(g.decode(compiled,VOCAB),row)
        with self.assertRaises(TypeError):
            compiled.positions[(2,0)] = "mutate"

    def test_frame_canonicality_and_integrity(self):
        cells=g.encode(record(),VOCAB)
        self.assertEqual(g.pack(cells),g.pack(reversed(cells)))
        frame=g.pack(cells)
        for data in [frame[:-1],frame+b"\x00",frame[:5]+bytes([frame[5]^1])+frame[6:]]:
            with self.assertRaises(ValueError):
                g.unpack(data)
        prefix=g.MAGIC+b"\x80\x00"
        with self.assertRaisesRegex(ValueError,"noncanonical integer"):
            g.unpack(prefix+struct.pack(">I",zlib.crc32(prefix)))


if __name__=="__main__":
    unittest.main()
