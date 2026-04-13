import requests
import json

def test_api():
    try:
        response = requests.get("https://api.frankfurter.app/latest?from=USD")
        data = response.json()
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(e)

if __name__ == "__main__":
    test_api()
