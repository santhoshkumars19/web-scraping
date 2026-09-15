"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

interface DeleteTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  count: number;
  taskId?: string;
  onConfirm: () => void;
}

export function DeleteTaskDialog({
  open,
  onOpenChange,
  count,
  taskId,
  onConfirm,
}: DeleteTaskDialogProps) {
  const isMultiple = count > 1;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <div className="flex items-center gap-2 text-rose-600 mb-1">
            <AlertTriangle className="h-5 w-5" />
            <DialogTitle>
              {isMultiple ? `Delete ${count} selected tasks?` : `Delete task ${taskId || ""}?`}
            </DialogTitle>
          </div>
          <DialogDescription className="text-xs text-muted-foreground leading-relaxed pt-1">
            {isMultiple
              ? `This will remove the ${count} selected tasks from your task history. Leads already collected from these tasks may remain available in your Leads list.`
              : `This will remove this task from your task history. Leads already collected from this task may remain available.`}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-4 gap-2 sm:gap-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => {
              onConfirm();
              onOpenChange(false);
            }}
          >
            Delete {isMultiple ? "Tasks" : "Task"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
