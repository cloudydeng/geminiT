from google import genai

client = genai.Client()

models = client.models.list()
for m in models:
    print(f"Model name: {m.name}")
    # Inspect all attributes dynamically
    for k, v in m.dict().items():
        print(f"  {k}: {v}")
    print("-" * 40)
