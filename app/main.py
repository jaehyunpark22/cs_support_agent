from fastapi import FastAPI


app = FastAPI(
    title="쇼핑몰 고객센터 AI Agent",
    version="0.1.0",
)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"message": "server is running"}