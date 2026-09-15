import Link from "next/link";
import { cn } from "@/lib/utils";

interface SunburstIconProps {
  className?: string;
}

/**
 * Signature SecureFlow radiating 12-ray sunburst mark in rich crimson #BE0B31.
 */
export function SunburstIcon({ className = "h-5 w-5" }: SunburstIconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className={cn("text-primary shrink-0", className)}
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="3.2" />
      {/* 12 radiating rounded rays */}
      <line x1="12" y1="1.5" x2="12" y2="4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="12" y1="19.5" x2="12" y2="22.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="1.5" y1="12" x2="4.5" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="19.5" y1="12" x2="22.5" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="4.57" y1="4.57" x2="6.7" y2="6.7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="17.3" y1="17.3" x2="19.43" y2="19.43" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="4.57" y1="19.43" x2="6.7" y2="17.3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="17.3" y1="6.7" x2="19.43" y2="4.57" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="7.25" y1="2.8" x2="8.35" y2="5.6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="15.65" y1="18.4" x2="16.75" y2="21.2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="2.8" y1="16.75" x2="5.6" y2="15.65" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="18.4" y1="8.35" x2="21.2" y2="7.25" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

interface BrandLogoProps {
  variant?: "light" | "dark" | "icon";
  href?: string | null;
  className?: string;
  size?: "sm" | "default" | "lg";
}

export function BrandLogo({
  variant = "light",
  href = "/dashboard",
  className,
  size = "default",
}: BrandLogoProps) {
  const iconSizes = {
    sm: "h-4 w-4",
    default: "h-5 w-5",
    lg: "h-7 w-7",
  };

  const textSizes = {
    sm: "text-xs",
    default: "text-sm",
    lg: "text-lg",
  };

  const content = (
    <div className={cn("flex items-center gap-2.5 select-none", className)}>
      <div className="flex items-center justify-center">
        <SunburstIcon className={iconSizes[size]} />
      </div>

      {variant !== "icon" && (
        <div className="flex flex-col leading-none">
          <span
            className={cn(
              "font-extrabold tracking-[-0.03em] font-sans",
              textSizes[size],
              variant === "dark" ? "text-white" : "text-foreground"
            )}
          >
            LeadScout
          </span>
          <span
            className={cn(
              "text-[10px] font-medium tracking-normal mt-0.5",
              variant === "dark" ? "text-white/60" : "text-muted-foreground"
            )}
          >
            Lead Discovery
          </span>
        </div>
      )}
    </div>
  );

  if (href) {
    return (
      <Link
        href={href}
        className={cn(
          "inline-flex items-center focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg",
          className
        )}
      >
        {content}
      </Link>
    );
  }

  return content;
}