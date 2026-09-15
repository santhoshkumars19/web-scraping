import { Button, type ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface PrimaryButtonProps extends ButtonProps {
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

/**
 * Primary action button — the main CTA throughout the app.
 * Uses the primary design token color (Crimson #BE0B31).
 *
 * Note: When asChild=true, leftIcon/rightIcon are ignored because Radix Slot
 * requires a single React element child. Put icons inside the child element instead.
 */
export function PrimaryButton({
  children,
  leftIcon,
  rightIcon,
  asChild,
  className,
  ...props
}: PrimaryButtonProps) {
  if (asChild) {
    // When using asChild, Slot must receive a single element — no icon siblings
    return (
      <Button
        variant="default"
        asChild
        className={cn("gap-2 font-medium", className)}
        {...props}
      >
        {children}
      </Button>
    );
  }

  return (
    <Button
      variant="default"
      className={cn("gap-2 font-medium", className)}
      {...props}
    >
      {leftIcon}
      {children}
      {rightIcon}
    </Button>
  );
}
