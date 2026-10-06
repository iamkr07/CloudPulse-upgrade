// Use the Render backend URL from Vercel env vars, with a localhost fallback for local development.
const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");

export const fetchResources = async () => {
  const res = await fetch(`${API_BASE}/api/resources`);
  
  if (!res.ok) {
    throw new Error("Failed to fetch resources");
  }

  return res.json();
};

export const simulateResource = async (resourceId, cpuScale) => {
  const res = await fetch(`${API_BASE}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resource_id: resourceId, cpu_scale: cpuScale }),
  });

  if (!res.ok) {
    throw new Error('Simulation request failed');
  }

  return res.json();
};

export const fetchResourceExplanation = async (resourceId) => {
  const res = await fetch(`${API_BASE}/api/resources/${resourceId}/explain`);

  if (!res.ok) {
    throw new Error("Failed to fetch resource explanation");
  }

  return res.json();
};

export const fetchResourceForecast = async (resourceId, scale = 1.0) => {
  const res = await fetch(`${API_BASE}/api/resources/${resourceId}/forecast?scale=${encodeURIComponent(scale)}`);

  if (!res.ok) {
    throw new Error("Failed to fetch resource forecast");
  }

  return res.json();
};

