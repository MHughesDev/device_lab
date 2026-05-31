"""WebRTC stream negotiation routes."""
import uuid
from fastapi import APIRouter, HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.models import StreamNegotiateRequest, StreamNegotiateResponse

router = APIRouter(prefix="/devices/{device_id}/stream", tags=["stream"])


@router.post("/negotiate", response_model=StreamNegotiateResponse, status_code=201)
async def negotiate_stream(
    device_id: uuid.UUID,
    body: StreamNegotiateRequest,
    db: SessionDep,
    _current_user: CurrentUser,
) -> StreamNegotiateResponse:
    from app.stream.gateway import negotiate
    try:
        session, sdp_answer = await negotiate(db, device_id, body.sdp_offer, body.client_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return StreamNegotiateResponse(
        sdp_answer=sdp_answer,
        session_token=session.session_token,
        input_channel_id="input",
    )


@router.post("/reconnect", response_model=StreamNegotiateResponse)
async def reconnect_stream(
    device_id: uuid.UUID,
    session_token: str,
    db: SessionDep,
    _current_user: CurrentUser,
) -> StreamNegotiateResponse:
    from app.stream.gateway import reconnect
    try:
        session = await reconnect(db, device_id, session_token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return StreamNegotiateResponse(
        sdp_answer="",   # client must re-offer; server returns existing token
        session_token=session.session_token,
        input_channel_id="input",
    )


@router.delete("/{session_id}", status_code=204)
async def close_stream(
    device_id: uuid.UUID,
    session_id: uuid.UUID,
    db: SessionDep,
    _current_user: CurrentUser,
) -> None:
    from app.stream.gateway import close_session
    await close_session(db, session_id)
