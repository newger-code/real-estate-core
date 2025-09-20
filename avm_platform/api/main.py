from fastapi import FastAPI
app = FastAPI()
@app.get("/health")
def health():
    return {"status": "ok"}
from avm_platform.version import __version__
@app.get("/version")
def version():
    return {"version": __version__}
