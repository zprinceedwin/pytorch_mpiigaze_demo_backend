from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "QuizSecure Backend is working!"}

@app.get("/test")
async def test():
    return {"status": "OK", "message": "FastAPI is running correctly"}

if __name__ == "__main__":
    print("Testing basic FastAPI server...")
    uvicorn.run(app, host="127.0.0.1", port=8000)