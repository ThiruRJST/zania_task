import requests
import json

resp = requests.post(
    url="http://localhost:6000/query-bot",
    json=json.dumps(
        {
            "query": ["who is the ceo?", "what is the vacation policy?", "what is their termination policy?"],
            "docpath": "/media/tensorthiru/New Volume/zania_task/handbook.pdf",
        }
    ),
)
print(resp.status_code)
print(resp.content)
