export function TaskLoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Metrics skeleton */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl border border-border bg-white p-4 h-24 flex flex-col justify-between"
          >
            <div className="h-3 w-16 bg-slate-200 rounded" />
            <div className="h-6 w-12 bg-slate-200 rounded" />
            <div className="h-2 w-20 bg-slate-100 rounded" />
          </div>
        ))}
      </div>

      {/* Tabs & Search skeleton */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="h-10 w-72 bg-slate-100 rounded-lg" />
        <div className="h-10 flex-1 bg-white border border-border rounded-md" />
        <div className="h-10 w-24 bg-white border border-border rounded-md" />
      </div>

      {/* Table skeleton */}
      <div className="rounded-xl border border-border bg-white overflow-hidden p-4 space-y-4">
        <div className="h-6 bg-slate-100 rounded w-full" />
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 py-2 border-b border-border/50">
            <div className="h-4 w-4 bg-slate-200 rounded" />
            <div className="h-4 w-24 bg-slate-200 rounded" />
            <div className="h-4 w-36 bg-slate-100 rounded" />
            <div className="h-4 w-24 bg-slate-100 rounded" />
            <div className="h-4 w-20 bg-slate-100 rounded" />
            <div className="h-4 w-20 bg-slate-200 rounded-full" />
            <div className="h-4 w-28 bg-slate-100 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
