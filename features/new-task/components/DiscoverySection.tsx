"use client";

import { useFormContext } from "react-hook-form";
import { MapPin, Tag, Radius } from "lucide-react";
import { FormSection } from "./FormSection";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SEARCH_RADIUS_OPTIONS } from "@/types/task-form";
import type { ScrapingTaskFormData } from "@/types/task-form";
import { cn } from "@/lib/utils";

interface FieldWrapperProps {
  label: string;
  htmlFor?: string;
  helper?: string;
  error?: string;
  required?: boolean;
  optional?: boolean;
  icon?: React.ElementType;
  children: React.ReactNode;
}

function FieldWrapper({
  label,
  htmlFor,
  helper,
  error,
  required,
  optional,
  icon: Icon,
  children,
}: FieldWrapperProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1.5">
        {Icon && <Icon className="h-3.5 w-3.5 text-muted-foreground" />}
        <Label htmlFor={htmlFor} className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {label}
          {required && <span className="ml-0.5 text-destructive">*</span>}
          {optional && (
            <span className="ml-1.5 font-normal normal-case tracking-normal text-muted-foreground/60">
              (optional)
            </span>
          )}
        </Label>
      </div>
      {children}
      {error ? (
        <p className="text-xs text-destructive">{error}</p>
      ) : helper ? (
        <p className="text-xs text-muted-foreground">{helper}</p>
      ) : null}
    </div>
  );
}

export function DiscoverySection() {
  const {
    register,
    setValue,
    watch,
    formState: { errors },
  } = useFormContext<ScrapingTaskFormData>();

  const searchRadius = watch("searchRadius");

  return (
    <FormSection
      title="Discovery"
      description="Define what kind of organizations you want to discover."
    >
      <div className="flex flex-col gap-5">
        {/* Location */}
        <FieldWrapper
          label="Location"
          htmlFor="location"
          required
          icon={MapPin}
          helper="Enter a city, area, or region."
          error={errors.location?.message}
        >
          <Input
            id="location"
            placeholder="e.g. Puducherry"
            autoComplete="off"
            className={cn(errors.location && "border-destructive focus-visible:ring-destructive")}
            {...register("location")}
          />
        </FieldWrapper>

        {/* Keyword */}
        <FieldWrapper
          label="Keyword or Category"
          htmlFor="keyword"
          required
          icon={Tag}
          helper="Describe the type of organizations you're looking for."
          error={errors.keyword?.message}
        >
          <Input
            id="keyword"
            placeholder="e.g. CBSE Schools"
            autoComplete="off"
            className={cn(errors.keyword && "border-destructive focus-visible:ring-destructive")}
            {...register("keyword")}
          />
          {/* Quick example chips */}
          <div className="flex flex-wrap gap-1.5 pt-0.5">
            {["CBSE Schools", "Hospitals", "IT Companies", "Law Firms", "Restaurants"].map(
              (example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setValue("keyword", example, { shouldValidate: true })}
                  className="rounded-full border border-border bg-slate-50 px-2.5 py-0.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary/5 hover:text-primary"
                >
                  {example}
                </button>
              )
            )}
          </div>
        </FieldWrapper>

        {/* Search Radius */}
        <FieldWrapper
          label="Search Radius"
          optional
          icon={Radius}
          helper="Approximate area around the location to search."
        >
          <Select
            value={searchRadius}
            onValueChange={(val) => setValue("searchRadius", val)}
          >
            <SelectTrigger className="w-full sm:w-48">
              <SelectValue placeholder="Select radius" />
            </SelectTrigger>
            <SelectContent>
              {SEARCH_RADIUS_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FieldWrapper>
      </div>
    </FormSection>
  );
}
