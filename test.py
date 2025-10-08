from langchain_openai import OpenAIEmbeddings

# create embeddings object
emb = OpenAIEmbeddings()

# test a simple query
res = emb.embed_query("Hello world")

print("Embedding vector length:", len(res))
print("First 5 values:", res[:5])
