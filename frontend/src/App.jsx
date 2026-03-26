import { useState } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return alert("Select a video");

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/predict/",
        formData
      );

      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Error occurred");
    }

    setLoading(false);
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #1e3c72, #2a5298)",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      color: "white"
    }}>
      <div style={{
        background: "rgba(255,255,255,0.1)",
        padding: "40px",
        borderRadius: "15px",
        backdropFilter: "blur(10px)",
        textAlign: "center",
        width: "400px"
      }}>
        <h1>🎭 Deepfake Detector</h1>

        <input
          type="file"
          accept="video/*"
          onChange={(e) => setFile(e.target.files[0])}
          style={{ marginTop: "20px" }}
        />

        <br /><br />

        <button
          onClick={handleUpload}
          style={{
            padding: "10px 20px",
            borderRadius: "8px",
            border: "none",
            cursor: "pointer",
            background: "#00c6ff",
            color: "black",
            fontWeight: "bold"
          }}
        >
          {loading ? "Processing..." : "Analyze Video"}
        </button>

        {result && (
          <div style={{ marginTop: "30px" }}>
            <h2 style={{
              color: result.label === "FAKE" ? "#ff4d4d" : "#00ffcc"
            }}>
              {result.label}
            </h2>

            <p>
              Confidence: {(result.confidence * 100).toFixed(2)}%
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;