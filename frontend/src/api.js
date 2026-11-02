const API_URL = "http://localhost:8000/jobs";

// Build "?a=1&b=2", skipping null/undefined/"" and false values
// (same job as requests dropping None params in app.py)
function toQuery(params) {
  // Building query helper function
  
  const searchParams = new URLSearchParams();

  for (const[key, value] of Object.entries(params)) {

    if (value !== undefined && value !== null && value !== '' && value !== false) {
        searchParams.append(key, value);
    }
  }
  
  const queryString = searchParams.toString();
  return queryString ? "?" + queryString : ``;
}

async function request(method, path, { params = {}, body } = {}) {
  // Handle requests helper
  
  // Build the ful URL with query parameters
  const url = `${API_URL}${path}${toQuery(params)}`;

  // Prepare tge fetch configuration options
  const options = {
    method: method,
  };

  // Attach headers and stringified body if a body is provided
  if (body) {
    options.headers = {
        "Content-Type": "application/json",
    };
    options.body = JSON.stringify(body)
  }

  // Fire network request
  const res = await fetch(url, options);

  // Handle HTTP error statuses
  if (!res.ok) {
    throw new Error(`Request failed with status ${res.status}`);
  }

  // Handle no content responses safely
  if (res.status === 204) {
    return null;
  }

  // Parse and return the JSON payload
  return await res.json();

}

export const getJobs = (params) => request("GET", "/", { params });
export const getCount = (params) => request("GET", "/count", { params });
export const getMetrics = () => request("GET", "/metrics");

export const updateStatus = (id, status) => {
  return request("PATCH", `/${id}`, { body: { status }});
};

export const startScrape = (payload) => {
  return request("POST", "/scrape", { body: payload });
};