import faiss
import numpy as np

def store_embeddings(embeddings):

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    return index


def search_similar_chunks(
    index,
    query_embedding,
    chunks,
    top_k=3
):

    query_embedding = np.array(
        query_embedding,
        dtype="float32"
    )

    distances, indices = index.search(
        query_embedding,
        top_k
    )

    retrieved_chunks = []

    for idx in indices[0]:

        retrieved_chunks.append(
            chunks[idx]
        )

    return retrieved_chunks