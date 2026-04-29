import urllib.request, urllib.error, json

key = "AIzaSyCp2u0up5MTpKMKqKbYSHL7m_onuGNhquM"

configs = [
    ("https://generativelanguage.googleapis.com/v1beta", "gemini-2.0-flash"),
    ("https://generativelanguage.googleapis.com/v1beta", "gemini-1.5-flash"),
    ("https://generativelanguage.googleapis.com/v1beta", "gemini-pro"),
    ("https://generativelanguage.googleapis.com/v1", "gemini-2.0-flash"),
    ("https://generativelanguage.googleapis.com/v1", "gemini-1.5-flash"),
    ("https://generativelanguage.googleapis.com/v1", "gemini-pro"),
]

for base_url, model in configs:
    url = f"{base_url}/models/{model}:generateContent?key={key}"
    payload = json.dumps({"contents": [{"parts": [{"text": "Say hi"}]}]})
    
    try:
        req = urllib.request.Request(url, data=payload.encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read().decode("utf-8"))
        text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        print(f"SUCCESS: {base_url} + {model} => {text[:50]}")
        break
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:150]
        print(f"FAIL: {model} @ {base_url.split('/')[-1]} => {e.code}: {body}")
    except Exception as e:
        print(f"FAIL: {model} @ {base_url.split('/')[-1]} => {str(e)[:100]}")
