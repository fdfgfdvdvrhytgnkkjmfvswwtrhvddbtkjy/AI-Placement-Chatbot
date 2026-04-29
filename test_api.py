import urllib.request, urllib.error, json

key = "AIzaSyAeBOYPHoWQYXA1L6vPfwhJFABKSZgnJHI"

# Try newer models that might have separate quotas
models_to_try = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemma-3-4b-it",
    "gemma-3-12b-it",
]

for model in models_to_try:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = json.dumps({"contents": [{"parts": [{"text": "Say hello in one word"}]}]})
    
    try:
        req = urllib.request.Request(url, data=payload.encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read().decode("utf-8"))
        text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        print(f"SUCCESS {model}: '{text.strip()[:80]}'")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:150]
        print(f"FAIL {e.code} {model}: {body}")
    except Exception as e:
        print(f"FAIL {model}: {str(e)[:100]}")
