import unittest
from aoci_rows import parse_dictionary, parse_volume, render_volume


class CodeVolumeTests(unittest.TestCase):
    header = "#AOCI-CODE-VOLUME: 1\n"
    section = "===/<repository>/routes live/===\n"

    def test_extended_name_dotted_and_content(self):
        volume = self.header + "# project comment\n" + self.section
        volume += "[id].py[C.G.9.X.S]: F:read A:value | R:code:foo | A: | S:-\n"
        rows = parse_volume(volume)
        row, = rows
        self.assertEqual(row["id"],"code:routes live/[id].py")
        self.assertEqual(row["tags"],{"A":"C","B":"G","C":"9","D":"X","E":"S"})
        self.assertEqual(row["fields"],{"F":"read A:value","R":"code:foo","A":"","S":"-"})
        self.assertEqual(parse_volume(render_volume(rows)), rows)

    def test_absent_and_hyphen(self):
        row, = parse_volume(self.header + self.section + "f.py[CG3L]: F:- | A:\n")
        self.assertNotIn("R",row["fields"])
        self.assertEqual(row["fields"]["A"],"")
        self.assertEqual(row["fields"]["F"],"-")
        self.assertEqual(parse_volume(render_volume([row])), [row])

    def test_reject_ambiguous_and_legacy(self):
        for line in (
            "x.py[CG5S]: F:first | F:last", "x.py[CG5S]: F:x | S1:first",
            "x.py[C,G,5,S]: F:broken", "x.py[C.G..5.S]: F:broken",
            "../outside.py[CG5S]: F:no", "x.py[CG5S]: F:x | broken",
        ):
            with self.subTest(line=line), self.assertRaises(ValueError):
                parse_volume(self.header+self.section+line)
        with self.assertRaises(ValueError):
            parse_volume(self.header+self.section+"x.py[CG3T]: F:1\nx.py[CG3T]: F:2")

    def test_dictionary_enforces_codes_and_order(self):
        text = "#AOCI-META-VOLUME: 1\n#[Tag dictionary: code]\n#A Layer: C-Code\n#B Module: G-General CL-Client\n#C Importance: 9-Core 5-Routine\n#E Scale: L-Large T-Tiny\n#[Tag dictionary: database]\n#A Layer: D-Database\n"
        self.assertEqual(parse_dictionary(text),{"A":["C"], "B":["G","CL"],"C":["9","5"], "D":[], "E":["L","T"]})
        for broken in (text.replace("5-Routine","unknown"),text.replace("9-Core","10-Core"),text.replace("9-Core","5-Other")):
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                parse_dictionary(broken)
