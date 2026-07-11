"""Resumable real-OpenClaw placement corpus executor."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, time, tempfile
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()
def dump(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
def main():
 p=argparse.ArgumentParser(); p.add_argument("--dataset",type=Path,required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--split",choices=("development","evaluation"),required=True); p.add_argument("--batch-size",type=int,default=12); p.add_argument("--max-batches",type=int,default=1); p.add_argument("--resume",action="store_true"); p.add_argument("--frozen-config",type=Path); a=p.parse_args()
 if not 6<=a.batch_size<=24: raise SystemExit("batch-size must be 6..24")
 cases=[json.loads(x) for x in a.dataset.read_text(encoding="utf-8").splitlines() if x.strip()]; cases=[x for x in cases if x["split"]==a.split]
 a.output.mkdir(parents=True,exist_ok=True); results=a.output/"results.jsonl"; done=set(); attempts={}; exhausted=set()
 if results.exists():
  for line in results.read_text(encoding="utf-8").splitlines():
   row=json.loads(line); cid=row["case_id"]; attempt=int(row.get("attempt",1)); key=(cid,attempt)
   while key in attempts: attempt+=1; key=(cid,attempt)
   attempts[key]=row
   if row.get("parse_status") != "model_failure": done.add(cid)
  for cid in {key[0] for key in attempts}:
   if max(key[1] for key in attempts if key[0]==cid)>=2 and cid not in done: exhausted.add(cid)
 if a.split=="evaluation" and not a.frozen_config: raise SystemExit("evaluation requires --frozen-config")
 if a.split=="development" and not (a.output/"frozen_run_config.json").exists(): dump(a.output/"frozen_run_config.json",{"provider":"meituan","model":"LongCat-2.0","prompt_version":"placement_v1","schema_version":"nollm_placement_v1","plugin_version":"0.1.0","openclaw_version":"2026.6.11","context_limits":{"candidate_cells":12}})
 pending=[x for x in cases if x["case_id"] not in done and x["case_id"] not in exhausted]; state={"dataset_file":str(a.dataset),"dataset_record_count":len(cases),"dataset_case_ids_digest":hashlib.sha256("\n".join(x["case_id"] for x in cases).encode()).hexdigest(),"split":a.split,"completed_case_ids":sorted(done),"failed_case_ids":sorted(exhausted),"deferred_case_ids":[],"pending_case_ids":[x["case_id"] for x in pending],"current_batch":0,"last_completed_case_id":None,"provider":"meituan","model":"LongCat-2.0","prompt_version":"placement_v1","schema_version":"nollm_placement_v1","started_at":now(),"updated_at":now()}
 batch_base=len(done)//a.batch_size
 for start in range(0,min(len(pending),a.batch_size*a.max_batches),a.batch_size):
  batch=pending[start:start+a.batch_size]; rows=[]
  for case in batch:
   began=time.monotonic(); model_case={key:value for key,value in case.items() if key not in {"expected","case_digest"}}; prompt="Use llm-task exactly once. Return JSON only with action reuse|new|revision|stitch|defer and reason. You are not a fact judge. Use only provided identities/candidate cells; defer if uncertain. Decide only from this bounded case: "+json.dumps(model_case,ensure_ascii=False)
   cli=shutil.which("openclaw.ps1") or str(Path(os.environ.get("LOCALAPPDATA", ""))/"Programs"/"nodejs"/"openclaw.ps1")
   if not cli: raise RuntimeError("openclaw.ps1 was not found on PATH")
   with tempfile.NamedTemporaryFile("w",encoding="utf-8",suffix=".txt",delete=False) as prompt_file: prompt_file.write(prompt); prompt_path=prompt_file.name
   cp=subprocess.run(["powershell","-NoProfile","-ExecutionPolicy","Bypass","-File",cli,"agent","--session-key",f"agent:main:placement-{case['case_id']}","--message-file",prompt_path,"--timeout","90","--json"],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=120)
   Path(prompt_path).unlink(missing_ok=True)
   raw=cp.stdout or cp.stderr; action="defer"; status="model_failure" if cp.returncode else "parsed"; error=None if cp.returncode==0 else cp.stderr.strip()
   try:
    payload=json.loads(raw); text=payload["result"]["payloads"][0]["text"].replace("```json","").replace("```","").strip(); decision=json.loads(text); action=decision.get("action","defer"); status="parsed" if action in {"reuse","new","revision","stitch","defer"} else "invalid_decision"
   except Exception as exc: decision=None; error=error or str(exc); action="defer"
   attempt=max([key[1] for key in attempts if key[0]==case["case_id"]],default=0)+1
   row={"case_id":case["case_id"],"split":a.split,"case_type":case["case_type"],"attempt":attempt,"provider":"meituan","model":"LongCat-2.0","auth_profile_id":None,"prompt_version":"placement_v1","schema_version":"nollm_placement_v1","started_at":now(),"finished_at":now(),"latency_ms":round((time.monotonic()-began)*1000),"placement_request":case,"raw_model_output":raw,"parsed_decision":decision,"parse_status":status,"core_validation_status":"not_mutated_corpus_evaluation","final_action":action,"selected_placement_id":None,"proposed_geometry_address":None,"revision_of":None,"stitch_target":None,"error_code":None if not error else "parse_or_model_error","error_message":error,"deferred_reason":None if action!="defer" else (decision or {}).get("reason"),"source_fallback_status":"not_applicable"};
   with results.open("a",encoding="utf-8") as f: f.write(json.dumps(row,ensure_ascii=False)+"\n")
   done.add(case["case_id"]); rows.append(row); print(f"[{len(done)}/{len(cases)}] {case['case_id']} {case['case_type']} {action} meituan/LongCat-2.0 {row['latency_ms']}ms {status}")
  batch_number=batch_base+start//a.batch_size+1
  dump(a.output/f"batch_{batch_number}_summary.json",{"case_count":len(rows),"success_count":sum(x["parse_status"]=="parsed" for x in rows),"defer_count":sum(x["final_action"]=="defer" for x in rows),"parse_failure_count":sum(x["parse_status"]=="invalid_decision" for x in rows),"model_failure_count":sum(x["parse_status"]=="model_failure" for x in rows),"core_rejection_count":0,"average_latency_ms":sum(x["latency_ms"] for x in rows)/len(rows),"p95_latency_ms":sorted(x["latency_ms"] for x in rows)[max(0,int(.95*len(rows))-1)]})
  state.update({"completed_case_ids":sorted(done),"pending_case_ids":[x["case_id"] for x in pending if x["case_id"] not in done],"current_batch":batch_number,"last_completed_case_id":batch[-1]["case_id"],"updated_at":now()}); dump(a.output/"run_state.json",state)
if __name__=="__main__": main()
