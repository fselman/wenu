from openai import OpenAI

client = OpenAI()

for model in client.models.list():
    print(model.id)
