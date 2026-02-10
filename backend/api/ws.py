"""
WebSocket endpoint for streaming solve responses.
"""
from __future__ import annotations

import json
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.models import SolveRequest, InputType, LLMProvider
from core.engine import MathEngine

router = APIRouter()
engine = MathEngine()


@router.websocket("/solve")
async def ws_solve(websocket: WebSocket):
    """Stream a solve operation step-by-step over WebSocket."""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            request = SolveRequest(
                input=data.get("input", ""),
                input_type=InputType(data.get("input_type", "text")),
                provider=LLMProvider(data.get("provider", "gemini")),
                show_steps=data.get("show_steps", True),
                visualize=data.get("visualize", False),
            )

            # Send status updates as we progress
            await websocket.send_json({"type": "status", "message": "Parsing input..."})

            result = await engine.solve(request)

            # Stream the result
            await websocket.send_json({
                "type": "result",
                "data": result.model_dump(),
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass
