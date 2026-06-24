import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const apiClient = axios.create({
  baseURL,
  timeout: 5 * 60 * 1000,
});

export async function getHealth() {
  const { data } = await apiClient.get("/api/health");
  return data;
}

export async function predictVideo({ file, sequenceLength, onProgress }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("sequence_length", String(sequenceLength));

  const { data } = await apiClient.post("/api/predict", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) return;
      onProgress(Math.min(1, event.loaded / event.total));
    },
  });
  return data;
}

/**
 * Resolve a media URL coming from the API (e.g. "/media/...").
 * In dev with Vite proxy this is already correct; in prod we may want
 * to prefix it with VITE_API_BASE_URL.
 */
export function resolveMediaURL(url) {
  if (!url) return url;
  if (/^https?:\/\//i.test(url)) return url;
  return `${baseURL}${url}`;
}
