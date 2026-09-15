import { cn } from "@/lib/utils";

interface DecorativeBulletProps {
  className?: string;
}

/**
 * Signature SecureFlow decorative crimson bullet point (square with soft rounding).
 * Placed before preheadings, section titles, and status tags.
 */
export function DecorativeBullet({ className }: DecorativeBulletProps) {
  return (
    <span
      className={cn(
        "inline-block h-1.5 w-1.5 rounded-[2px] bg-primary shrink-0 align-middle",
        className
      )}
      aria-hidden="true"
    />
  );
}

