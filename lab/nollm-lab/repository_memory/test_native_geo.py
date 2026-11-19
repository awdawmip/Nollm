"""Native round trips, spatial queries, coordinate perturbations and source identity."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from geometry_cli import encode_volume
from native_geo import address, main, probe, read_native, write_native
from nollm_access import AccessDecision, AccessRuntime, FileHandleStore, FileStatementStore
from nollm_core import CoreRuntime

DICTIONARY = {"A":["owner","shared"],"B":["service"],"C":["public"],"D":[],"E":["tiny"]}
TAGS = {"A":"owner","B":"service","C":"public","E":"tiny"}


def sample():
    return [{"id":"code:alpha.py","tags":TAGS.copy(),"fields":{
        "F":"make widgets","R":"code:beta.py,database:missing","A":"-","S":"keep history"}},
        {"id":"code:beta.py","tags":TAGS.copy(),"fields":{"F":"persist"}}]


def move(field, a, b):
    with CoreRuntime(field) as core, AccessRuntime(core,FileStatementStore(field),FileHandleStore(field)) as access:
        handle,atom = core.atoms_at(a)[0]
        access.apply(AccessDecision("relocate", atom.atom_id, "move", target_cell=b, existing_handle=handle,
                                    decided_by="host", reason_text="Controlled geometry perturbation."))


class NativeGeometryTest(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.field=self.root/"native"
        self.rows=sample()
        self.info=write_native(self.rows,DICTIONARY,self.field)

    def test_storage_reopens_and_direction_routes_to_evidence(self):
        self.assertEqual(read_native(self.field,DICTIONARY)[0],self.rows)
        self.assertEqual(self.info["directed_bridges"],1)
        self.assertEqual(self.info["unresolved_reference_cells"],1)
        hit=probe(self.field,DICTIONARY,"code:alpha.py")
        self.assertEqual(hit["ports"]["F"],{"relative":[1,0],"path":["lateral"],"value":"make widgets"})
        self.assertEqual(hit["reference"]["target"],"code:beta.py")
        self.assertEqual(hit["projected_fields"],self.rows[0]["fields"])
        with self.assertRaisesRegex(ValueError,"dictionary"):
            read_native(self.field,dict(DICTIONARY,A=list(reversed(DICTIONARY["A"]))))

    def test_real_coordinate_swap_changes_field_meaning(self):
        before=sample()
        move(self.field,address(1,0),address(7,7))
        move(self.field,address(-1,0),address(1,0))
        move(self.field,address(7,7),address(-1,0))
        decoded=read_native(self.field,DICTIONARY)[0]
        self.assertEqual(decoded[0]["fields"]["F"],before[0]["fields"]["S"])
        self.assertEqual(decoded[0]["fields"]["S"],before[0]["fields"]["F"])

    def test_tag_displacement_rejects_off_axis_but_accepts_another_category(self):
        move(self.field,address(2,0),address(3,0))
        self.assertEqual(read_native(self.field,DICTIONARY)[0][0]["tags"]["A"],"shared")
        move(self.field,address(3,0),address(5,-3))
        with self.assertRaises(ValueError):
            read_native(self.field,DICTIONARY)

    def test_missing_native_bridge_detected(self):
        with CoreRuntime(self.field) as core:
            core.bridge_remove(core.bridges()[0].bridge_id)
        with self.assertRaisesRegex(ValueError,"bridge"):
            read_native(self.field,DICTIONARY)

    def test_pure_volume_to_native_field(self):
        spec=self.root/"dictionary.json"
        spec.write_text(json.dumps(DICTIONARY))
        volume=self.root/"shapes.nlg"
        volume.write_bytes(encode_volume(self.rows,DICTIONARY))
        dest=self.root/"other"
        main(["write","--geometry",str(volume),"--dictionary",str(spec),"--field",str(dest),"--out",str(self.root/"info")])
        self.assertEqual(read_native(dest,DICTIONARY)[0], self.rows)


if __name__ == "__main__":
    unittest.main()
