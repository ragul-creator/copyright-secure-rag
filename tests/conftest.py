import os
import tempfile

os.environ["SQLITE_DB"]=tempfile.mktemp(suffix=".db")
os.environ["AUDIT_LOG"]=tempfile.mktemp(suffix=".jsonl")
os.environ["DATABASE_URL"]=""
os.environ["OPA_URL"]=""
os.environ["OPA_RIGHTS_URL"]=""
os.environ["LLM_PROVIDER"]="extractive"
os.environ["VECTOR_BACKEND"]="local"
os.environ["AUTH_MODE"]="disabled"
os.environ["OTEL_ENABLED"]="false"
