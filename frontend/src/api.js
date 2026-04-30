import axios from "axios";

const api = axios.create({
  baseURL: "",
});

export const getIncidents = () => api.get("/api/incidents").then(r => r.data);
export const getStats = () => api.get("/api/incidents/stats/summary").then(r => r.data);
export const createAlert = (data) => api.post("/api/incidents/alerts", data).then(r => r.data);
export const updateStatus = (id, data) => api.patch(`/api/incidents/${id}/status`, data).then(r => r.data);
export const submitRCA = (id, data) => api.post(`/api/incidents/${id}/rca`, data).then(r => r.data);

export default api;
