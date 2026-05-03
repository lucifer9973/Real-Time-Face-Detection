import base64
from io import BytesIO

from PIL import Image


def test_start_stream(client):
    response = client.post("/stream/start", json={"source_name": "webcam"})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "started"
    assert isinstance(body["session_id"], str)
    assert len(body["session_id"]) > 0


def test_get_roi_empty(client):
    response = client.get("/roi")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_stream_websocket_roundtrip(client):
    session_id = client.post("/stream/start", json={"source_name": "webcam"}).json()[
        "session_id"
    ]
    image = Image.new("RGB", (8, 8), color="white")
    buff = BytesIO()
    image.save(buff, format="JPEG")
    encoded = base64.b64encode(buff.getvalue()).decode("utf-8")

    with client.websocket_connect("/stream") as websocket:
        websocket.send_json(
            {
                "frame_id": 1,
                "session_id": session_id,
                "image_base64": encoded,
            }
        )
        response = websocket.receive_json()
        assert response["frame_id"] == 1
        assert "image_base64" in response
        assert "rois" in response
