from flask import Flask, request
from utils.ocr_utils import do_ocr
from utils.prompt_utils import return_prompt
from openai import OpenAI
import chromadb
import time
from sentence_transformers import CrossEncoder
import uuid
from concurrent.futures.thread import ThreadPoolExecutor

chroma_client = chromadb.PersistentClient("/home/tensorthiru/.chroma")
chroma_collection = chroma_client.get_or_create_collection(name="Zania_Task_Collection")

rerank_model = CrossEncoder(
    model_name="cross-encoder/ms-marco-TinyBERT-L-2-v2", max_length=512
)

client = OpenAI(api_key="YOUR API KEY HERE")
app = Flask(__name__)


@app.route("/query-bot", methods=["POST"])
def main():
    print("**** querying ****")

    ocr_result = []
    request_query_json = eval(request.get_json())
    print(request_query_json)
    print(type(request_query_json))

    query = request_query_json["query"]
    doc_path = request_query_json["docpath"]
    doc_name = doc_path.split("/")[-1]

    doc_ext = doc_name.split(".")[-1]
    existing_ids = chroma_collection.get()["ids"]
    print(existing_ids)

    # extract text from pdf file
    if doc_ext == "pdf":
        resp = do_ocr(doc_path)
        ocr_result.extend(resp)
        print(len(ocr_result))
        # new_ids = [f"{doc_name}_pg_{num}" for num in range(len(ocr_result))]

        new_id_dict = [
            {str(uuid.uuid3(uuid.NAMESPACE_DNS, f"{ocr_result[x]}_{x}")): ocr_result[x]}
            for x in range(len(ocr_result))
        ]

        new_ids = [list(x.keys())[0] for x in new_id_dict]
        non_existing_ids = [x for x in new_ids if x not in existing_ids]

        #adding non-existing documents
        if len(non_existing_ids) > 0:
            print(f"*** Adding new docs - {len(non_existing_ids)}***")
            for non_id in non_existing_ids:
                doc = new_id_dict[non_id]
                chroma_collection.add(documents=doc, ids=non_id)

    if isinstance(query, str):

        #Re-Ranking
        rerank_inp = []
        query_result = chroma_collection.query(query_texts=[query], n_results=5)[
            "documents"
        ][0]
        for i in range(len(query_result)):
            rerank_inp.append((query, query_result[i]))

        rerank_scores = rerank_model.predict(rerank_inp).tolist()
        max_score = max(rerank_scores)
        max_ind = rerank_scores.index(max_score)

        best_hit = query_result[max_ind]

        #prompt Construction
        prompt = return_prompt(best_hit=best_hit, query=query)

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        response = completion.choices[0].message.content
        return {"query": query, "response": response}

    elif isinstance(query, list):
        query_result = chroma_collection.query(query_texts=query, n_results=5)[
            "documents"
        ]

        # with ThreadPoolExecutor(max_workers=len(query)) as e:
        #     e.submit
        best_hit = []
        responses = []

        for i in range(len(query_result)):
            rerank_inp = []
            queries = query[i]
            query_res = query_result[i]
            if len(query_res) > 0:
                for j in query_res:
                    rerank_inp.append((queries, j))
                rerank_scores = rerank_model.predict(rerank_inp).tolist()
                max_score = max(rerank_scores)
                max_ind = rerank_scores.index(max_score)
                best_hit.append(query_res[max_ind])

        print(best_hit)

        prompt = return_prompt(best_hit=best_hit, query=query)
        msgs = [{"role": "user", "content": i} for i in prompt]

        for msg in msgs:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[msg],
            )

            responses.append(completion.choices[0].message.content)

        chat_response_pairs = [{query[i]: responses[i]} for i in range(len(responses))]
        return {"Chat_Responses": chat_response_pairs}
