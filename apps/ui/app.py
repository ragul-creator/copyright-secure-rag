import os, requests, streamlit as st
API=os.getenv("API_URL","http://localhost:8000")
st.set_page_config(page_title="Secure Support RAG",layout="wide")
st.title("Copyright-Secure Customer Support RAG")
st.caption("Licensed-source retrieval • provenance • runtime copyright reproduction guardrails")

with st.sidebar:
    st.header("Register source")
    sid=st.text_input("Source ID","SRC-001")
    name=st.text_input("Name","Refund Policy")
    holder=st.text_input("Rights holder","Example Corp")
    lic=st.text_input("SPDX/license","LicenseRef-Proprietary")
    limit=st.number_input("Verbatim word limit",8,200,28)
    if st.button("Register"):
        r=requests.post(API+"/sources",json={"source_id":sid,"name":name,"rights_holder":holder,"license_spdx":lic,
          "quote_word_limit":limit,"rag_allowed":True,"generation_allowed":True,"status":"approved"})
        st.write(r.json())
    st.header("Ingest text")
    did=st.text_input("Document ID","DOC-001")
    txt=st.text_area("Document text",height=180)
    if st.button("Ingest"):
        r=requests.post(API+"/ingest",json={"source_id":sid,"document_id":did,"text":txt})
        st.write(r.json())

q=st.chat_input("Ask a support question")
if q:
    with st.chat_message("user"): st.write(q)
    r=requests.post(API+"/chat",json={"question":q,"top_k":4})
    data=r.json()
    with st.chat_message("assistant"):
        st.write(data.get("answer"))
        st.markdown(f"**Security decision:** `{data.get('decision')}`")
        if data.get("citations"):
            st.markdown("**Approved sources**")
            for c in data["citations"]: st.write(f"- {c['source_name']} ({c['document_id']}) — retrieval {c['score']}")
        with st.expander("Copyright signals"):
            st.json(data.get("copyright_signals",{}))
