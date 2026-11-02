const STATUSES = ["new", "viewed", "applied", "rejected", "archived"];

function formatSalary(min, max) {
  // TODO 12: port your Python logic. Both -> "$30,000-$56,000",
  //   only min -> "$30,000+", only max -> "Up to $56,000", neither -> "".
  //   Hint: (30000).toLocaleString() gives "30,000".
}

export default function JobCard({ job, onStatusChange }) {
  return (
    <div style={{ border: "1px solid #ccc", padding: 12, margin: "12px 0" }}>
      {/* TODO 13: title as a link (<a href={job.job_url} target="_blank">),
          then company | location | salary | Remote or Onsite | site | date.
          Use `||` fallbacks like "Unknown Company" for null fields. */}

      {/* TODO 14: <select> bound to job.status that calls
          onStatusChange(job.id, e.target.value) */}

      {/* TODO 15: show job.description inside a <details> element
          (built-in expander, no state needed), only if it exists */}
    </div>
  );
}