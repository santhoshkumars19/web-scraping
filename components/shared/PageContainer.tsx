import { cn } from "@/lib/utils";

interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Main content wrapper providing consistent padding, max-width,
 * and responsive spacing for all page content.
 */
export function PageContainer({ children, className }: PageContainerProps) {
  return (
    <main
      className={cn(
        "w-full px-4 py-4 sm:px-6 sm:py-6 lg:px-8",
        className
      )}
    >
      <div className="mx-auto w-full max-w-7xl animate-fade-in">
        {children}
      </div>
    </main>
  );
}
