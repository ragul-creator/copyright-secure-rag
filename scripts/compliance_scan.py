from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

p=argparse.ArgumentParser(description="Run available copyright/license compliance scanners and emit a signed-input manifest.")
p.add_argument("path")
p.add_argument("--out",default="compliance-results")
a=p.parse_args()
source=Path(a.path).resolve(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
if not source.exists(): raise SystemExit(f"missing path: {source}")

def sha256_file(path: Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

manifest={"input":str(source),"tools":{},"files":[]}
for f in ([source] if source.is_file() else [p for p in source.rglob("*") if p.is_file()]):
    manifest["files"].append({"path":str(f.relative_to(source.parent if source.is_file() else source)),"sha256":sha256_file(f)})

if shutil.which("scancode"):
    target=out/"scancode.json"
    subprocess.run(["scancode","--license","--copyright","--info","--json-pp",str(target),str(source)],check=True)
    manifest["tools"]["scancode"]={"artifact":str(target),"sha256":sha256_file(target)}
else:
    manifest["tools"]["scancode"]={"status":"not-installed"}

if shutil.which("ort"):
    target=out/"ort"
    subprocess.run(["ort","analyze","-i",str(source),"-o",str(target)],check=True)
    manifest["tools"]["ort"]={"artifact":str(target)}
else:
    manifest["tools"]["ort"]={"status":"not-installed"}

manifest_path=out/"manifest.json"
manifest_path.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(manifest_path)
