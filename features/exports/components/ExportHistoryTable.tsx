"use client";

import {
  FileText,
  FileSpreadsheet,
  Download,
  Trash2,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ExportRecord } from "@/types/export";

interface ExportHistoryTableProps {
  records: ExportRecord[];
  onDownload: (record: ExportRecord) => void;
  onDeleteRequest: (record: ExportRecord) => void;
}

export function ExportHistoryTable({
  records,
  onDownload,
  onDeleteRequest,
}: ExportHistoryTableProps) {
  return (
    <div className="rounded-2xl border border-border bg-white overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-border bg-[#F8F7F0] font-semibold text-muted-foreground uppercase text-[11px] tracking-wider">
              <th className="py-3 px-4">File Name</th>
              <th className="py-3 px-3">Type</th>
              <th className="py-3 px-3">Records</th>
              <th className="py-3 px-3">Created</th>
              <th className="py-3 px-3">Status</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {records.map((record) => {
              const isExcel = record.format === "excel";
              const isSuccess = record.status === "COMPLETED";

              return (
                <tr
                  key={record.id}
                  className="hover:bg-[#FAF9F5] transition-colors group"
                >
                  {/* File Name */}
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`p-1.5 rounded-md shrink-0 ${
                          isExcel
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-primary/10 text-primary"
                        }`}
                      >
                        {isExcel ? (
                          <FileSpreadsheet className="h-4 w-4" />
                        ) : (
                          <FileText className="h-4 w-4" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <div
                          className="font-medium text-foreground truncate max-w-[240px] lg:max-w-[320px]"
                          title={record.fileName}
                        >
                          {record.fileName}
                        </div>
                        <div className="text-[10px] text-muted-foreground font-mono mt-0.5">
                          {record.fileSize || "18 KB"}
                          {record.taskId && ` • ${record.taskId}`}
                        </div>
                      </div>
                    </div>
                  </td>

                  {/* Type */}
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                        isExcel
                          ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                          : "bg-primary/10 text-primary border border-primary/20"
                      }`}
                    >
                      {record.format === "excel" ? "Excel" : "CSV"}
                    </span>
                  </td>

                  {/* Records */}
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span className="font-mono font-semibold text-foreground">
                      {record.recordCount} {record.recordCount === 1 ? "lead" : "leads"}
                    </span>
                  </td>

                  {/* Created */}
                  <td className="py-3 px-3 whitespace-nowrap text-muted-foreground text-[11px]">
                    {record.createdAt}
                  </td>

                  {/* Status */}
                  <td className="py-3 px-3 whitespace-nowrap">
                    {isSuccess ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        <CheckCircle2 className="h-3 w-3" />
                        <span>Completed</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                        <XCircle className="h-3 w-3" />
                        <span>Failed</span>
                      </span>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="py-3 px-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={!isSuccess}
                        onClick={() => onDownload(record)}
                        className="h-7 text-xs px-2.5 gap-1.5 border-border hover:bg-slate-100"
                      >
                        <Download className="h-3 w-3" />
                        <span>Download</span>
                      </Button>

                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => onDeleteRequest(record)}
                        className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive hover:bg-rose-50"
                        title="Delete export record"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        <span className="sr-only">Delete</span>
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
