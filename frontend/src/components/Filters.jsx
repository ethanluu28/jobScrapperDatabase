const STATUSES = ["new", "viewed", "applied", "rejected", "archived"];

export default function Filters({ filters, onChange }) {
  // TODO 11: render a keyword input, company input, remote checkbox, and
  //   a status <select> (options: "all" + STATUSES).
  //   Each is a controlled input: value={filters.x} and an onChange that
  //   calls the parent's onChange({ ...filters, x: newValue }).
  //   Remember: checkboxes use e.target.checked, not e.target.value.
  return <div>{/* inputs here */}</div>;
}