import os
import requests

from dotenv import load_dotenv
from embeddings import retrieve_context


# --------------------------------------------------
# Environment variables
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model_name = os.getenv("OPENROUTER_MODEL")

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}


NO_ANSWER = (
    "The information is not available in the provided documents."
)


# --------------------------------------------------
# Send request to OpenRouter
# --------------------------------------------------

def ask_llm(prompt):

    request_data = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=request_data,
            timeout=60
        )

    except requests.RequestException as error:

        print("Request error:", error)
        return None


    if response.status_code == 200:

        data = response.json()

        return data["choices"][0]["message"]["content"]


    print("Request failed.")
    print("Status code:", response.status_code)

    try:
        print(response.json())

    except Exception:
        print(response.text)

    return None


# --------------------------------------------------
# Main RAG pipeline
# --------------------------------------------------

def answer_question(question):

    max_k = 3

    # --------------------------------------------------
    # Step 1: Start with top-1
    # --------------------------------------------------

    context, sources, candidates = retrieve_context(
        question,
        top_k=1,
        candidate_k=max_k
    )

    top_k = 1


    # --------------------------------------------------
    # Step 2: Deterministic ambiguity check
    # --------------------------------------------------

    if len(candidates) >= 2:

        first_score = candidates[0]["score"]
        second_score = candidates[1]["score"]

        retrieved_sections = {
            source["section"]
            for source in sources
        }

        second_section = candidates[1]["section"]


        # If top-1 and top-2 are close,
        # use top-2 before calling the LLM.
        if (
            second_score >= first_score * 0.85
            and second_section not in retrieved_sections
        ):

            top_k = 2

            context, sources, candidates = retrieve_context(
                question,
                top_k=top_k,
                candidate_k=max_k
            )


    # --------------------------------------------------
    # Step 3: Optional top-3 ambiguity check
    # --------------------------------------------------

    if top_k == 2 and len(candidates) >= 3:

        second_score = candidates[1]["score"]
        third_score = candidates[2]["score"]

        retrieved_sections = {
            source["section"]
            for source in sources
        }

        third_section = candidates[2]["section"]


        # Only expand again if the third result
        # is also very close to the second.
        if (
            third_score >= second_score * 0.90
            and third_section not in retrieved_sections
        ):

            top_k = 3

            context, sources, candidates = retrieve_context(
                question,
                top_k=top_k,
                candidate_k=max_k
            )


    # --------------------------------------------------
    # Step 4: Build final prompt
    # --------------------------------------------------

    prompt = f"""
You are an insurance document assistant.

Answer the user's question using only the information
provided in the context below.

Rules:

- Do not use outside knowledge.

- Answer only using information explicitly available
  in the context.

- If the information needed to answer the question
  is not available in the context, say exactly:

  "{NO_ANSWER}"

- Do not invent missing information.

- Do not mention section numbers or source references
  in the answer.

- Do not include reasoning, metadata, safety labels,
  classifications, or commentary.

- Keep the answer clear and concise.

CONTEXT:

{context}

QUESTION:

{question}

ANSWER:
"""


    # --------------------------------------------------
    # Step 5: ONE LLM call
    # --------------------------------------------------

    answer = ask_llm(prompt)


    if answer is None:

        return (
            "Something went wrong while generating the answer.",
            []
        )


    answer = answer.strip()


    # No sources if document does not contain the answer
    if answer == NO_ANSWER:

        return answer, []


    return answer, sources


# --------------------------------------------------
# Terminal testing
# --------------------------------------------------

if __name__ == "__main__":

    question = input("What's your question?: ")

    answer, sources = answer_question(question)


    print("\nAnswer:")
    print(answer)


    if sources:

        print("\nSources:")

        for source in sources:

            if source["type"] == "cross-reference":

                print(
                    f"Section {source['section']} - "
                    f"{source['title']} "
                    f"[cross-reference]"
                )

            else:

                print(
                    f"Section {source['section']} - "
                    f"{source['title']}"
                )