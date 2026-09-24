import os
import requests
import streamlit as st

API=os.getenv("API_URL","http://localhost:8000")
st.set_page_config(page_title="Secure Support RAG",layout="wide")
st.title("Copyright-Secure Customer Support RAG")
st.caption("Tenant-scoped licensed retrieval • provenance • runtime reproduction guardrails • audit chain")

token=st.sidebar.text_input("Bearer token (leave empty when AUTH_MODE=disabled)",type="password")
headers={"Authorization":f"Bearer {token}"} if token else {}

def api(method,path,**kwargs):
    kwargs.setdefault("headers",headers)
    r=requests.request(method,API+path,timeout=30,**kwargs)
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
        txt=st.text_area("Document text",height=200)
        if st.button("Ingest approved document"):
            st.json(api("POST","/ingest",json={"source_id":sid,"document_id":did,"text":txt}) or {})
    st.subheader("Current sources")
    sources=api("GET","/sources")
    if sources is not None:
        st.dataframe(sources,use_container_width=True)

with security_tab:
    if st.button("Refresh security overview"):
        st.session_state["overview"]=api("GET","/admin/overview")
    if st.session_state.get("overview"):
        st.json(st.session_state["overview"])
    st.subheader("Audit chain")
    verify=api("GET","/audit/verify")
    if verify:
        st.metric("Tamper-evident chain valid","YES" if verify.get("valid") else "NO")
    events=api("GET","/audit/recent?limit=50")
    if events is not None:
        st.dataframe(events,use_container_width=True)
