import hashlib
import json
import os
import requests
import streamlit as st

API=os.getenv("API_URL","http://localhost:8000")
st.set_page_config(page_title="Secure Support RAG",layout="wide")
st.title("Copyright-Secure Customer Support RAG")
st.caption("Tenant-scoped licensed retrieval • provenance • compliance evidence • reproduction guardrails • audit chain")

token=st.sidebar.text_input("Bearer token (leave empty when AUTH_MODE=disabled)",type="password")
headers={"Authorization":f"Bearer {token}"} if token else {}

def api(method,path,**kwargs):
    kwargs.setdefault("headers",headers)
    try:
        r=requests.request(method,API+path,timeout=30,**kwargs)
    except requests.RequestException as exc:
        st.error(f"API unavailable: {exc}")
        return None
    if r.status_code >= 400:
        st.error(f"{r.status_code}: {r.text}")
        return None
    return r.json()

chat_tab,kb_tab,security_tab=st.tabs(["Support chat","Knowledge & rights","Security operations"])

with chat_tab:
    q=st.chat_input("Ask a support question")
    if q:
        with st.chat_message("user"): st.write(q)
        data=api("POST","/chat",json={"question":q,"top_k":4})
        if data:
            with st.chat_message("assistant"):
                st.write(data.get("answer"))
                st.markdown(f"**Security decision:** `{data.get('decision')}`")
                if data.get("citations"):
                    st.markdown("**Approved sources**")
                    for c in data["citations"]:
                        st.write(f"- {c['source_name']} ({c['document_id']}) — retrieval {c['score']}")
                with st.expander("Copyright signals"):
                    st.json(data.get("copyright_signals",{}))

with kb_tab:
    left,right=st.columns(2)
    with left:
        st.subheader("Register rights-controlled source")
        sid=st.text_input("Source ID","SRC-001")
        name=st.text_input("Name","Refund Policy")
        holder=st.text_input("Rights holder","Example Corp")
        lic=st.text_input("SPDX/license","LicenseRef-Proprietary")
        limit=st.number_input("Verbatim word limit",0,500,28)
        attribution=st.checkbox("Attribution required")
        if st.button("Register source"):
            st.json(api("POST","/sources",json={"source_id":sid,"name":name,"rights_holder":holder,"license_spdx":lic,
                "quote_word_limit":limit,"attribution_required":attribution,"rag_allowed":True,"generation_allowed":True,"status":"approved"}) or {})
    with right:
        st.subheader("Ingest document")
        did=st.text_input("Document ID","DOC-001")
        txt=st.text_area("Document text",height=180)
        if st.button("Ingest approved document"):
            st.json(api("POST","/ingest",json={"source_id":sid,"document_id":did,"text":txt}) or {})

    st.subheader("Compliance evidence")
    ev1,ev2,ev3=st.columns(3)
    with ev1: tool=st.selectbox("Scanner/tool",["scancode","ort","manual","other"])
    with ev2: verdict=st.selectbox("Verdict",["approved","review","rejected"])
    with ev3: artifact=st.text_input("Artifact URI","file://compliance-results/manifest.json")
    evidence_text=st.text_area("Evidence/details JSON",value='{"note":"reviewed"}',height=80)
    if st.button("Attach compliance evidence"):
        try: details=json.loads(evidence_text or "{}")
        except json.JSONDecodeError:
            st.error("Evidence/details must be valid JSON"); details=None
        if details is not None:
            digest=hashlib.sha256((artifact+evidence_text).encode()).hexdigest()
            st.json(api("POST",f"/sources/{sid}/evidence",json={"tool":tool,"artifact_uri":artifact,
                "artifact_sha256":digest,"verdict":verdict,"details":details}) or {})

    st.subheader("Current sources")
    sources=api("GET","/sources")
    if sources is not None:
        st.dataframe(sources,use_container_width=True)
        if sources:
            manage_id=st.selectbox("Manage source",[s["source_id"] for s in sources])
            new_status=st.selectbox("New source status",["approved","review","revoked"])
            if st.button("Apply source status"):
                st.json(api("PATCH",f"/sources/{manage_id}/status",json={"status":new_status}) or {})
            evidence=api("GET",f"/sources/{manage_id}/evidence")
            with st.expander("Compliance evidence for selected source"):
                st.dataframe(evidence or [],use_container_width=True)

with security_tab:
    overview=api("GET","/admin/overview")
    if overview:
        cols=st.columns(5)
        cols[0].metric("Sources",overview.get("sources",0))
        cols[1].metric("Approved",overview.get("approved_sources",0))
        cols[2].metric("Documents",overview.get("documents",0))
        cols[3].metric("Chunks",overview.get("chunks",0))
        cols[4].metric("Approved evidence",overview.get("approved_evidence",0))
        st.metric("Audit chain", "VALID" if overview.get("audit_chain_valid") else "INVALID")
    st.subheader("Recent security events")
    events=api("GET","/audit/recent?limit=100")
    if events is not None:
        st.dataframe(events,use_container_width=True)
