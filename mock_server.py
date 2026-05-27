from fastapi import FastAPI, Request
import json, uvicorn

app = FastAPI()

@app.post("/events")
async def receive_event(request: Request):
    body = await request.json()
    print(json.dumps(body, indent=2))
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
