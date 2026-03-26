import { useState, useEffect } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [videoURL, setVideoURL] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(true);

  // Load theme
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme === "light") {
      document.documentElement.classList.remove("dark");
      setDarkMode(false);
    } else {
      document.documentElement.classList.add("dark");
      setDarkMode(true);
    }
  }, []);

  // Toggle theme
  const toggleTheme = () => {
    if (darkMode) {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    } else {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    }
    setDarkMode(!darkMode);
  };

  const handleFileChange = (f) => {
    setFile(f);
    setVideoURL(URL.createObjectURL(f));
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return alert("Upload a video");

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
      alert("Error during prediction");
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center transition-all duration-500
      bg-gray-100 dark:bg-gradient-to-br dark:from-purple-900 dark:via-blue-900 dark:to-indigo-900">

      {/* Toggle Button */}
      <div className="absolute top-5 right-5">
        <button
          onClick={toggleTheme}
          className="px-4 py-2 rounded-lg bg-black text-white dark:bg-white dark:text-black"
        >
          {darkMode ? "☀️ Light" : "🌙 Dark"}
        </button>
      </div>

      {/* Card */}
      <div className="p-8 rounded-2xl shadow-2xl w-[500px]
        bg-white text-black
        dark:bg-white/10 dark:text-white backdrop-blur-xl">

        <h1 className="text-3xl font-bold text-center mb-6">
          🎭 Deepfake AI Analyzer
        </h1>

        {/* Upload */}
        <div
          className="border-2 border-dashed p-6 rounded-lg text-center cursor-pointer
            border-gray-400 hover:bg-gray-200
            dark:border-white/40 dark:hover:bg-white/10"
          onClick={() => document.getElementById("fileInput").click()}
        >
          <p>Drag & Drop or Click to Upload Video</p>
          <input
            id="fileInput"
            type="file"
            accept="video/*"
            hidden
            onChange={(e) => handleFileChange(e.target.files[0])}
          />
        </div>

        {/* Preview */}
        {videoURL && (
          <div className="mt-4">
            <video src={videoURL} controls className="rounded-lg w-full" />
            <p className="text-sm mt-2">
              📁 {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          </div>
        )}

        {/* Button */}
        <button
          onClick={handleUpload}
          className="mt-6 w-full bg-cyan-400 text-black py-2 rounded-lg font-semibold hover:bg-cyan-300"
        >
          {loading ? "Analyzing..." : "Run AI Analysis"}
        </button>

        {/* Loading */}
        {loading && (
          <div className="mt-4 text-center animate-pulse">
            🤖 AI analyzing...
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="mt-6 p-4 rounded-lg
            bg-gray-200
            dark:bg-black/30">

            <h2 className={`text-2xl font-bold ${
              result.label === "FAKE" ? "text-red-500" : "text-green-500"
            }`}>
              {result.label}
            </h2>

            {/* Confidence */}
            <div className="mt-3">
              <p>Confidence</p>
              <div className="w-full bg-gray-400 dark:bg-gray-700 rounded-full h-3 mt-1">
                <div
                  className="bg-green-500 h-3 rounded-full"
                  style={{ width: `${result.confidence * 100}%` }}
                ></div>
              </div>
              <p className="text-sm mt-1">
                {(result.confidence * 100).toFixed(2)}%
              </p>
            </div>

            <div className="mt-4 text-sm">
              <p>🟢 Real: {(result.real_prob * 100).toFixed(2)}%</p>
              <p>🔴 Fake: {(result.fake_prob * 100).toFixed(2)}%</p>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}

export default App;