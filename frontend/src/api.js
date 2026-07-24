import axios from "axios";

const API_URL = "http://localhost:8000";

export const analyzeDiff = async (diffText) => {
  const response = await axios.post(`${API_URL}/analyze`, {
    diff: diffText,
    repo_path: "seed/"
  });
  return response.data;
};

export const fetchGraph = async () => {
  const response = await axios.get(`${API_URL}/graph`);
  return response.data;
};
