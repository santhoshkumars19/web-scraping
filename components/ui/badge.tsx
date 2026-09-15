import * as React from "react";
import { cn } from "@/lib/utils";

const badgeVariants = {
  default: "bg-[#BE0B31]/10 text-[#BE0B31] border border-[#BE0B31]/20",
  secondary: "bg-[#0E0E0E] text-white",
  outline: "border border-[#E3E0D5] bg-white text-[#0E0E0E]",
  destructive: "bg-[#BE0B31] text-white border border-[#BE0B31]",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: keyof typeof badgeVariants;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
          badgeVariants[variant],
          className
        )}
        {...props}
      />
    );
  }
);
Badge.displayName = "Badge";

export { Badge };
