import asyncio
import httpx
import json

async def test_ollama():
    urls = [
        "http://host.docker.internal:11434/v1/chat/completions",
        "http://172.19.0.1:11434/v1/chat/completions"
    ]
    payload = {
        "model": "phi3:mini",
        "messages": [{"role": "user", "content": "Say hello in JSON format"}],
        "response_format": {"type": "json_object"}
    }
    
    for url in urls:
        print(f"Testing connectivity to {url}...")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json=payload)
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error for {url}: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
