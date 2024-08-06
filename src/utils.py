def format_retrieved_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
