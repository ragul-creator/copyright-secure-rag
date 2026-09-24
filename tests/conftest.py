import os, tempfile
os.environ["SQLITE_DB"]=tempfile.mktemp(suffix=".db")
os.environ["AUDIT_LOG"]=tempfile.mktemp(suffix=".jsonl")
os.environ["OPA_URL"]=""
os.environ["LLM_PROVIDER"]="extractive"
