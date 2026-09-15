import { cn } from "@/lib/utils";
import { DecorativeBullet } from "./DecorativeBullet";

interface SectionHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

/**
 * Consistent page/section header with title, signature decorative bullet,
 * optional description, and an action slot (e.g., buttons).
 */
export function SectionHeader({
  title,
  description,
  actions,
  className,
}: SectionHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between pb-1",
        className
      )}
    >
      <div>
        <div className="flex items-center gap-2">
          <DecorativeBullet />
          <h1 className="text-xl sm:text-2xl font-extrabold tracking-[-0.035em] text-[#0E0E0E] font-sans">
            {title}
          </h1>
        </div>
        {description && (
          <p className="mt-1 text-xs sm:text-sm text-[#5C5A53] leading-relaxed pl-3.5 border-l border-[#E3E0D5] ml-0.5">
            {description}
          </p>
        )}
      </div>

      {actions && (
        <div className="flex shrink-0 items-center gap-2">{actions}</div>
      )}
    </div>
  );
}

