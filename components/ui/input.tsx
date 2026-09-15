import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-9 w-full rounded-xl border border-[#E3E0D5] bg-white px-3 py-2 text-sm text-[#0E0E0E] shadow-2xs transition-all",
          "placeholder:text-[#9E9B93]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#BE0B31]/30 focus-visible:border-[#BE0B31]",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "file:border-0 file:bg-transparent file:text-sm file:font-medium",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
