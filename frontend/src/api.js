const API_URL = "http://localhost:8000/jobs";

// Build "?a=1&b=2", skipping null/undefined/"" and false values
// (same job as requests dropping None params in app.py)
function toQuery(params) {
  // TODO 1: loop over Object.entries(params), add each kept value to a
  //   URLSearchParams, and return "?" + searchParams.toString()
  //   (return "" if nothing was added)
}

async function request(method, path, { params = {}, body } = {}) {
  // TODO 2: call fetch(`${API_URL}${path}${toQuery(params)}`, {...})
  //   - set method
  //   - if body exists: headers {"Content-Type": "application/json"}
  //     and body: JSON.stringify(body)
  //   - fetch does NOT throw on 4xx/5xx, so check `res.ok` and throw
  //     new Error(...) if it's false
  //   - DELETE returns 204 with no body, so only call res.json()
  //     when res.status !== 204
}

export const getJobs = (params) => request("GET", "/", { params });
export const getCount = (params) => request("GET", "/count", { params });
export const getMetrics = () => request("GET", "/metrics");

export const updateStatus = (id, status) => {
  // TODO 3: PATCH `/${id}` with body { status }
};

export const startScrape = (payload) => {
  // TODO 4: POST "/scrape" with body: payload
  //   payload fields: search_term, location, results_wanted,
  //   hours_old, site_name (array)
};