import { useState, useEffect } from "react";
import { getJobs, getCount, getMetrics, updateStatus } from "./api";
import Filters from "./components/Filters";
import JobCard from "./components/JobCard";

export default function App() {
  const [filters, setFilters] = useState({
    keyword: "", company: "", remote_only: false, status: "all",
  });
  const [page, setPage] = useState(1);
  const [limit] = useState(50);
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [metrics, setMetrics] = useState({ total: 0, new: 0, applied: 0 });
  const [error, setError] = useState(null);

  // The API doesn't understand status="all", so strip it here
  const apiParams = {
    ...filters,
    status: filters.status === "all" ? null : filters.status,
  };

  async function load() {
    try {
      // TODO 5: fetch jobs, count, and metrics together with Promise.all.
      //   jobs needs { ...apiParams, limit, offset: (page - 1) * limit }.
      //   Then call setJobs, setTotal (count.total), setMetrics, and
      //   clear the error with setError(null).
    } catch (e) {
      setError(e.message);
    }
  }

  // TODO 6: useEffect that runs load() whenever filters or page change.
  //   Think carefully about the dependency array: what happens if you
  //   leave it off? What if you include `jobs`?

  function handleFilterChange(newFilters) {
    // TODO 7: setFilters(newFilters) AND setPage(1)
    //   (same job as resetPage() in app.py)
  }

  async function handleStatusChange(id, status) {
    // TODO 8: await updateStatus(id, status), then load() to refresh
  }

  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div>
      <h1>💼 Job Tracker</h1>
      {error && <p style={{ color: "red" }}>API error: {error}</p>}

      {/* TODO 9: three metric boxes using metrics.total / .new / .applied */}

      <Filters filters={filters} onChange={handleFilterChange} />

      {/* TODO 10: Previous / Next buttons + "Page X of Y".
          Disable Previous on page 1 and Next on the last page.
          Use setPage(p => p - 1) style updates. */}

      {jobs.length === 0
        ? <p>No job listings match your filters.</p>
        : jobs.map((job) => (
            <JobCard key={job.id} job={job} onStatusChange={handleStatusChange} />
          ))}
    </div>
  );
}