import { ShieldCheck } from "lucide-react";

export function ResponsibleCrawlingCard() {
  return (
    <div className="flex gap-3 rounded-xl border border-border bg-slate-50/60 px-5 py-4">
      <div className="mt-0.5 shrink-0">
        <ShieldCheck className="h-4 w-4 text-emerald-600" />
      </div>
      <div>
        <p className="text-xs font-semibold text-foreground">
          Responsible Crawling
        </p>
        <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
          This platform works with publicly accessible information and follows
          reasonable crawling practices. Websites that restrict access are not
          bypassed.
        </p>
      </div>
    </div>
  );
}
