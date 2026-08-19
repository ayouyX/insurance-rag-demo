import os
import re
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
# Parse ANSWER + COMPLETE
# --------------------------------------------------

def parse_response(answer):

    match = re.search(
        r"ANSWER:\s*(.*?)\s*COMPLETE:\s*(YES|NO)",
        answer,
        re.IGNORECASE | re.DOTALL
    )

    if match:

        final_answer = match.group(1).strip()
        complete = match.group(2).upper()

        return final_answer, complete

    return None, None


# --------------------------------------------------
# Main RAG pipeline
# --------------------------------------------------

def answer_question(question):

    top_k = 1
    max_k = 3

    final_answer = None
    complete = "NO"
    sources = []


    while top_k <= max_k:

        # ------------------------------------------
        # Retrieve chunks
        # ------------------------------------------

        context, sources, candidates = retrieve_context(
            question,
            top_k=top_k,
            candidate_k=max_k
        )


        # ------------------------------------------
        # Deterministic ambiguity check
        # ------------------------------------------

        if top_k == 1 and len(candidates) >= 2:

            first_score = candidates[0]["score"]
            second_score = candidates[1]["score"]

            retrieved_sections = {
                source["section"]
                for source in sources
            }

            second_section = candidates[1]["section"]


            # If the second result is very close to the first,
            # retrieve another chunk before asking the LLM.
            if (
                second_score >= first_score * 0.85
                and second_section not in retrieved_sections
            ):

                top_k += 1
                continue


        # ------------------------------------------
        # Build prompt
        # ------------------------------------------

        prompt = f"""
You are an insurance document assistant.

Answer the user's question using only the information
provided in the context below.

Rules:

- Do not use outside knowledge.

- Answer only using information explicitly available
  in the provided context.

- COMPLETE: YES means the current context fully answers
  every part of the user's question.

- COMPLETE: NO means more document information is needed.

- If only part of the user's question can be answered,
  return COMPLETE: NO.

- Do not mention section numbers or source references
  in the final answer.

- Do not include reasoning, metadata, safety labels,
  classifications, or commentary.

- Keep the answer clear and concise.


Return exactly:

ANSWER: <your answer>
COMPLETE: YES or NO


CONTEXT:

{context}


QUESTION:

{question}
"""


        # ------------------------------------------
        # Ask LLM
        # ------------------------------------------

        response = ask_llm(prompt)


        if response is None:

            return (
                "Something went wrong while generating the answer.",
                []
            )


        # ------------------------------------------
        # Parse response
        # ------------------------------------------

        final_answer, complete = parse_response(response)


        if final_answer is None or complete is None:

            return (
                "Something went wrong while processing the answer.",
                []
            )


        # ------------------------------------------
        # Stop if context is enough
        # ------------------------------------------

        if complete == "YES":

            return final_answer, sources


        # ------------------------------------------
        # Otherwise expand retrieval
        # ------------------------------------------

        top_k += 1


    # ----------------------------------------------
    # No sufficient answer found
    # ----------------------------------------------

    return (
        "The information is not available in the provided documents.",
        []
    )


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