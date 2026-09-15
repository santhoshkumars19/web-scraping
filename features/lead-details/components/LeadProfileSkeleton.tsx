export function LeadProfileSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Breadcrumb skeleton */}
      <div className="h-4 w-36 bg-slate-200 rounded" />

      {/* Header banner skeleton */}
      <div className="rounded-xl border border-border bg-white p-6 h-32 flex justify-between items-center">
        <div className="flex gap-4 items-center">
          <div className="h-12 w-12 bg-slate-200 rounded-xl" />
          <div className="space-y-2">
            <div className="h-5 w-48 bg-slate-200 rounded" />
            <div className="h-3 w-32 bg-slate-100 rounded" />
          </div>
        </div>
        <div className="flex gap-2">
          <div className="h-9 w-24 bg-slate-100 rounded" />
          <div className="h-9 w-24 bg-slate-200 rounded" />
        </div>
      </div>

      {/* Two column grid skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        <div className="space-y-6">
          <div className="rounded-xl border border-border bg-white p-6 h-48" />
          <div className="rounded-xl border border-border bg-white p-6 h-64" />
          <div className="rounded-xl border border-border bg-white p-6 h-40" />
        </div>

        <div className="space-y-6">
          <div className="rounded-xl border border-border bg-white p-5 h-44" />
          <div className="rounded-xl border border-border bg-white p-5 h-40" />
          <div className="rounded-xl border border-border bg-white p-5 h-48" />
        </div>
      </div>
    </div>
  );
}
