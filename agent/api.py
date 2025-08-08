from fastapi import FastAPI
from pydantic import BaseModel
from agent.core import scan_dependencies

app = FastAPI()


class ScanRequest(BaseModel):
    file_path: str


@app.post("/scan")
def run_scan(request: ScanRequest):
    result = scan_dependencies(request.file_path)
    return result
