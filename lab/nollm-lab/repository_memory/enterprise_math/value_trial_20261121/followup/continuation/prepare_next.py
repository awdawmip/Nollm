"""Store a first reader's earned conclusion and a local correction in two equal-content memories."""
import argparse
import json
from pathlib import Path
from shutil import copyfile, copytree
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare import write

OLD = "CRT.X6.offsets.v1"
NEW = "CRT.X6.offsets.v2"
TITLE = "六格表的平方和平移诊断｜先区分允许的偏移和原始前缀"
BASE = """研究者推导。按原稿行序，基线 ρ=(n,n+1)、γ=(1,n,n)、e=n 给出 x(t)=(0,t,n−t,1,n−t,t)，t∈{0,…,n}，C(3)=t。允许在同一初态副本上任意有符号整数平移、同偏移精确读 q4 和 q6。应用单模全平移稳定子求交，在表族上恰区分 t mod 6。偏移 0 与第二坐标的单位向量使每模的差减 1 等于 2t，解 parity 与 mod 3 后得类号。n=5 可恢复全部前缀，n=6 的 t=0,6 在所有允许偏移下碰撞。"""
OLD_TEXT = TITLE + "\n" + BASE + " 两次成对偏移给出上界，本版尚无受限表族的匹配下界。"
NEW_TEXT = TITLE + "\n" + BASE + """ 后续核对平面读者的下界：固定任一偏移后，平方和为 A+2Bt+4t²，模 4 最多两值，模 3 是首项为 1 的二次式最多两值。一对读数与该整数模 12 等价，所以单偏移最多四种，不足分开 n=5 的六张表。对此基线，两次固定成对偏移确为最少。误读或更改允许平移集合须另行推导。"""


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('first','root','runtime'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    sys.path.insert(0,str(a.runtime))
    from enterprise_math.research import describe, save_statement, walk
    a.root.mkdir(parents=True,exist_ok=True)
    started = perf_counter()
    copytree(a.first/'N',a.root/'N')
    copyfile(a.first/'paths.json',a.root/'paths.json')
    notes = json.loads((a.first/'flat.json').read_text())
    write(a.root/'flat.json',notes)
    receipt = {'copy_ms':(perf_counter()-started)*1000}
    by_id = {n['id']: n for n in notes}
    refs = [by_id[k]['sources'][0] for k in ('NT-SUP-CRT-CARRY','CRT.repair','X6-QUADRATIC-MODULAR.v2')]
    for note_id,body,rev in [(OLD,OLD_TEXT,None),(NEW,NEW_TEXT,OLD)]:
        if not rev:
            page = walk(a.root/'N',[],0,8,1,5,'local')
            # Host chose the original CRT neighbourhood after viewing its Surface.
            receipt['placement_menu'] = page
        args = (note_id, body, refs, None if rev else (0,0), rev)
        at = perf_counter()
        saved = save_statement(a.root/'N',*args)
        native_ms = (perf_counter()-at)*1000
        at = perf_counter()
        if rev:
            notes[-1]['current'] = False
        item = {'id':note_id,'text':body,'sources':refs,'current':True}
        if rev:
            item['revises'] = rev
        notes.append(item)
        write(a.root/'flat.json',notes)
        receipt[note_id] = {'saved': saved,'native_ms':native_ms,'flat_ms':(perf_counter()-at)*1000,
                            'body_bytes':len(body.encode()), 'source_bytes':sum(len(r.encode()) for r in refs)}
    assert [describe(a.root/'N', n['id']) for n in notes] == notes
    receipt['bytes'] = {'F':(a.root/'flat.json').stat().st_size,
                        'N':sum(f.stat().st_size for f in (a.root/'N').rglob('*') if f.is_file())}
    write(a.root/'formation.json',receipt)


if __name__ == '__main__':
    main()
