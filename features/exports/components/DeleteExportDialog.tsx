"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Trash2 } from "lucide-react";
import type { ExportRecord } from "@/types/export";

interface DeleteExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  record: ExportRecord | null;
  onConfirm: (recordId: string) => void;
}

export function DeleteExportDialog({
  open,
  onOpenChange,
  record,
  onConfirm,
}: DeleteExportDialogProps) {
  if (!record) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-full bg-rose-50 text-rose-600">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <DialogTitle className="text-sm font-bold text-foreground">
                Delete this export record?
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground mt-0.5">
                This removes the export from your history.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="py-2 text-xs text-muted-foreground">
          <div className="p-2.5 rounded-lg border border-border/80 bg-slate-50 font-mono text-[11px] text-foreground truncate">
            {record.fileName}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed">
            Note: This will not delete previously downloaded files from your local computer.
          </p>
        </div>

        <DialogFooter className="gap-2 sm:gap-0 mt-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="text-xs"
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            size="sm"
            onClick={() => {
              onConfirm(record.id);
              onOpenChange(false);
            }}
            className="text-xs gap-1.5"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>Delete Record</span>
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
