from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

from ingestion import structured_chunks


# --------------------------------------------------
# Load embedding model
# --------------------------------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# --------------------------------------------------
# Prepare document embeddings
# --------------------------------------------------

texts = []

for item in structured_chunks:
    combined_text = f"{item['title']}\n{item['text']}"
    texts.append(combined_text)


vectors = model.encode(texts)


# --------------------------------------------------
# Find a chunk directly by section number
# --------------------------------------------------

def find_chunk_by_section(section_number):

    for chunk in structured_chunks:

        if chunk["section"] == section_number:
            return chunk

    return None


# --------------------------------------------------
# Detect references such as "Section 4.2"
# --------------------------------------------------

def find_references(text):

    references = re.findall(
        r"\bSection\s+(\d+\.\d+)\b",
        text,
        re.IGNORECASE
    )

    return references


# --------------------------------------------------
# Retrieve context
# --------------------------------------------------

def retrieve_context(question, top_k=3, candidate_k=3):

    # Encode user's question
    question_vector = model.encode(question)


    # Similarity between question and every chunk
    scores = cosine_similarity(
        question_vector.reshape(1, -1),
        vectors
    )[0]


    # Rank all chunks from highest to lowest similarity
    ranked_indices = np.argsort(scores)[::-1]


    # Actual chunks that will be retrieved
    top_indices = ranked_indices[:top_k]


    # Candidates used only for routing decisions
    candidate_indices = ranked_indices[:candidate_k]


    # --------------------------------------------------
    # Candidate metadata
    # --------------------------------------------------

    candidates = []

    for index in candidate_indices:

        chunk = structured_chunks[index]

        candidates.append({
            "section": chunk["section"],
            "title": chunk["title"],
            "score": float(scores[index])
        })


    # --------------------------------------------------
    # Semantic retrieval
    # --------------------------------------------------

    selected_chunks = []
    sources = []

    added_sections = set()


    for index in top_indices:

        chunk = structured_chunks[index]

        selected_chunks.append(chunk)

        added_sections.add(chunk["section"])

        sources.append({
            "section": chunk["section"],
            "title": chunk["title"],
            "type": "semantic"
        })


    # --------------------------------------------------
    # Resolve cross-references
    # --------------------------------------------------

    chunks_to_check = selected_chunks.copy()


    for chunk in chunks_to_check:

        references = find_references(chunk["text"])


        for reference in references:

            # Avoid duplicates
            if reference in added_sections:
                continue


            referenced_chunk = find_chunk_by_section(reference)


            if referenced_chunk is not None:

                selected_chunks.append(referenced_chunk)

                added_sections.add(reference)

                sources.append({
                    "section": referenced_chunk["section"],
                    "title": referenced_chunk["title"],
                    "type": "cross-reference"
                })


    # --------------------------------------------------
    # Build context
    # --------------------------------------------------

    context = ""


    for chunk in selected_chunks:

        formatted = (
            f"Section {chunk['section']} - {chunk['title']}\n"
            f"{chunk['text']}"
        )

        context += formatted + "\n\n"


    return context, sources, candidates