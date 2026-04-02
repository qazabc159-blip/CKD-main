from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.service import (
    build_clinical_response,
    build_research_response,
    extract_inputs,
    health_payload,
)


app = FastAPI(
    title="CKD Prediction Prototype Backend",
    version="0.1.0",
    description="Minimal local inference backend for the CKD Prediction Studio research prototype.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return health_payload()


@app.post("/predict")
def predict(payload: dict) -> dict:
    mode = str(payload.get("mode", "research")).strip().lower()
    try:
        inputs = extract_inputs(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if mode == "clinical":
        return build_clinical_response(inputs).to_dict()
    if mode == "research":
        return build_research_response(inputs, "research").to_dict()

    raise HTTPException(status_code=400, detail="Unsupported mode. Use `clinical` or `research`.")


@app.post("/predict/research")
def predict_research(payload: dict) -> dict:
    try:
        inputs = extract_inputs(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_research_response(inputs, "research").to_dict()


@app.post("/predict/clinical")
def predict_clinical(payload: dict) -> dict:
    try:
        inputs = extract_inputs(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return build_clinical_response(inputs).to_dict()
