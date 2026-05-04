import { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const WS_BASE = import.meta.env.VITE_WS_BASE || "ws://localhost:8000";

function App() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const socketRef = useRef(null);
  const frameIdRef = useRef(0);
  const timerRef = useRef(null);
  const sessionIdRef = useRef("");

  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [processedImage, setProcessedImage] = useState("");
  const [boxes, setBoxes] = useState([]);
  const [statusMessage, setStatusMessage] = useState("");
  const [uploadedImage, setUploadedImage] = useState("");
  const [uploadedBoxes, setUploadedBoxes] = useState([]);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    return () => stopStream();
  }, []);

  const startStream = async () => {
    setError("");
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoRef.current.srcObject = mediaStream;
      await fetch(`${API_BASE}/stream/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_name: "webcam" }),
      })
        .then((response) => response.json())
        .then((data) => {
          sessionIdRef.current = data.session_id || "";
        });

      const socket = new WebSocket(`${WS_BASE}/stream`);
      socketRef.current = socket;
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.error) {
          setError(data.error.message || "Stream error.");
          return;
        }
        setProcessedImage(`data:image/jpeg;base64,${data.image_base64}`);
        setBoxes(data.rois || []);
        setStatusMessage(data.message || "");
      };
      socket.onerror = () => setError("WebSocket error.");

      timerRef.current = setInterval(sendFrame, 500);
      setRunning(true);
    } catch (err) {
      setError("Failed to start stream.");
    }
  };

  const sendFrame = () => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.videoWidth === 0) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    frameIdRef.current += 1;
    socket.send(
      JSON.stringify({
        frame_id: frameIdRef.current,
        session_id: sessionIdRef.current,
        image_base64: canvas.toDataURL("image/jpeg", 0.8),
      })
    );
  };

  const stopStream = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;

    if (socketRef.current) socketRef.current.close();
    socketRef.current = null;
    sessionIdRef.current = "";

    const media = videoRef.current?.srcObject;
    if (media) {
      media.getTracks().forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }

    setRunning(false);
  };

  const uploadPhoto = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setError("");
    setUploadMessage("");
    setUploading(true);
    try {
      const body = new FormData();
      body.append("image", file);

      const response = await fetch(`${API_BASE}/stream/upload-image`, {
        method: "POST",
        body,
      });

      const payload = await response.json();
      if (!response.ok) {
        const detail = payload?.detail || "Failed to process uploaded image.";
        throw new Error(detail);
      }

      setUploadedImage(`data:image/jpeg;base64,${payload.image_base64}`);
      setUploadedBoxes(payload.rois || []);
      setUploadMessage(payload.message || "Face detection finished for uploaded image.");
    } catch (err) {
      setError(err.message || "Failed to upload image.");
      setUploadedImage("");
      setUploadedBoxes([]);
      setUploadMessage("");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  return (
    <main className="container">
      <h1>Real-Time Face Detection</h1>
      <p className="muted">WebSocket stream with backend-drawn bounding boxes.</p>

      <div className="actions">
        <button onClick={startStream} disabled={running}>
          Start
        </button>
        <button onClick={stopStream} disabled={!running}>
          Stop
        </button>
        <label className="upload-btn">
          {uploading ? "Uploading..." : "Upload Photo"}
          <input
            type="file"
            accept="image/*"
            onChange={uploadPhoto}
            disabled={uploading}
            className="hidden-input"
          />
        </label>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <section className="grid">
        <div>
          <h3>Raw Camera</h3>
          <video ref={videoRef} autoPlay playsInline muted className="panel" />
        </div>
        <div>
          <h3>Processed Output</h3>
          {processedImage ? (
            <img src={processedImage} alt="processed stream" className="panel" />
          ) : (
            <div className="panel placeholder">Waiting for frames...</div>
          )}
          <p className="muted">Detected faces: {boxes.length}</p>
          {processedImage ? (
            <p className="muted">
              {boxes.length > 0 ? "Face detected ✅" : "No face detected ⚠️"}
            </p>
          ) : null}
          {statusMessage ? <p className="muted">{statusMessage}</p> : null}
        </div>
      </section>

      {uploadedImage ? (
        <section className="upload-result">
          <h3>Uploaded Photo Result</h3>
          <img src={uploadedImage} alt="uploaded result" className="panel" />
          <p className="muted">Detected faces: {uploadedBoxes.length}</p>
          {uploadMessage ? <p className="muted">{uploadMessage}</p> : null}
        </section>
      ) : null}

      <canvas ref={canvasRef} className="hidden" />
    </main>
  );
}

export default App;
