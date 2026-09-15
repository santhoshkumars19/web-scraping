import { cn } from "@/lib/utils";

interface FormSectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * Card wrapper for each section of the scraping task form.
 * Provides consistent padding, border, and header layout.
 */
export function FormSection({
  title,
  description,
  children,
  className,
}: FormSectionProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border bg-white shadow-sm",
        className
      )}
    >
      {/* Section header */}
      <div className="border-b border-border px-5 py-4">
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
        {description && (
          <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
        )}
      </div>

      {/* Content */}
      <div className="px-5 py-5">{children}</div>
    </div>
  );
}
