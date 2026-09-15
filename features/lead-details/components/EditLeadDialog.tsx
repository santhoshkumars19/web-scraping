"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import type { Lead } from "@/types/lead";

const editLeadSchema = z.object({
  organizationName: z.string().min(1, "Organization name is required"),
  category: z.string().min(1, "Category is required"),
  phone: z.string().optional(),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  website: z.string().optional(),
  address: z.string().optional(),
  contactPerson: z.string().optional(),
  designation: z.string().optional(),
});

type EditLeadFormData = z.infer<typeof editLeadSchema>;

interface EditLeadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  lead: Lead;
  onSave: (updated: Lead) => void;
}

export function EditLeadDialog({
  open,
  onOpenChange,
  lead,
  onSave,
}: EditLeadDialogProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EditLeadFormData>({
    resolver: zodResolver(editLeadSchema) as any,
    defaultValues: {
      organizationName: lead.organizationName,
      category: lead.category,
      phone: lead.phone || "",
      email: lead.email || "",
      website: lead.website || "",
      address: lead.address || "",
      contactPerson: lead.contactPerson || "",
      designation: lead.designation || "",
    },
  });

  const onSubmit = (data: EditLeadFormData) => {
    const updated: Lead = {
      ...lead,
      organizationName: data.organizationName,
      category: data.category,
      phone: data.phone || undefined,
      email: data.email || undefined,
      website: data.website || undefined,
      address: data.address || undefined,
      contactPerson: data.contactPerson || undefined,
      designation: data.designation || undefined,
    };
    onSave(updated);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-base">Edit Lead Information</DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Update contact and organizational details for {lead.organizationName}.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-2 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Organization Name */}
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="organizationName" className="text-xs">
                Organization Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="organizationName"
                {...register("organizationName")}
                className="h-8 text-xs"
              />
              {errors.organizationName && (
                <p className="text-[11px] text-destructive">
                  {errors.organizationName.message}
                </p>
              )}
            </div>

            {/* Category */}
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="category" className="text-xs">
                Category / Industry <span className="text-destructive">*</span>
              </Label>
              <Input
                id="category"
                {...register("category")}
                className="h-8 text-xs"
              />
              {errors.category && (
                <p className="text-[11px] text-destructive">
                  {errors.category.message}
                </p>
              )}
            </div>

            {/* Phone */}
            <div className="space-y-1">
              <Label htmlFor="phone" className="text-xs">Phone Number</Label>
              <Input
                id="phone"
                {...register("phone")}
                placeholder="+91..."
                className="h-8 text-xs font-mono"
              />
            </div>

            {/* Email */}
            <div className="space-y-1">
              <Label htmlFor="email" className="text-xs">Official Email</Label>
              <Input
                id="email"
                type="email"
                {...register("email")}
                placeholder="info@..."
                className="h-8 text-xs"
              />
              {errors.email && (
                <p className="text-[11px] text-destructive">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Website */}
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="website" className="text-xs">Website URL</Label>
              <Input
                id="website"
                {...register("website")}
                placeholder="https://..."
                className="h-8 text-xs font-mono"
              />
            </div>

            {/* Address */}
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="address" className="text-xs">Address</Label>
              <Input
                id="address"
                {...register("address")}
                className="h-8 text-xs"
              />
            </div>

            {/* Contact Person */}
            <div className="space-y-1">
              <Label htmlFor="contactPerson" className="text-xs">Contact Person</Label>
              <Input
                id="contactPerson"
                {...register("contactPerson")}
                className="h-8 text-xs"
              />
            </div>

            {/* Designation */}
            <div className="space-y-1">
              <Label htmlFor="designation" className="text-xs">Designation / Role</Label>
              <Input
                id="designation"
                {...register("designation")}
                placeholder="e.g. Principal"
                className="h-8 text-xs"
              />
            </div>
          </div>

          <DialogFooter className="mt-4 gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={isSubmitting}>
              Save Changes
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
