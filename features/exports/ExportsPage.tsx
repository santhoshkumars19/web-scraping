"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  Download,
  Search,
  ArrowUpDown,
  Filter,
  FileSpreadsheet,
  FileText,
  Users,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

import type { ExportRecord, ExportFormat, ExportStatus } from "@/types/export";
import {
  loadExportHistory,
  deleteExportRecord,
  SESSION_EXPORT_BLOBS,
} from "@/mock/exports";
import { MOCK_LEADS } from "@/mock/leads";
import { DEFAULT_SELECTED_FIELDS, downloadBlob } from "@/lib/export/exportUtils";
import { exportToCsv } from "@/lib/export/csv";
import { exportToExcel } from "@/lib/export/excel";

import { ExportHistoryTable } from "./components/ExportHistoryTable";
import { ExportHistoryCard } from "./components/ExportHistoryCard";
import { DeleteExportDialog } from "./components/DeleteExportDialog";
import { ExportDialog } from "@/features/export/ExportDialog";

export function ExportsPage() {
  const [records, setRecords] = useState<ExportRecord[]>(() => loadExportHistory());
  const [search, setSearch] = useState("");
  const [formatFilter, setFormatFilter] = useState<"ALL" | ExportFormat>("ALL");
  const [statusFilter, setStatusFilter] = useState<"ALL" | ExportStatus>("ALL");
  const [sortOrder, setSortOrder] = useState<"newest" | "oldest">("newest");

  // Dialogs
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [recordToDelete, setRecordToDelete] = useState<ExportRecord | null>(null);
  const [exportModalOpen, setExportModalOpen] = useState(false);

  // Filtered and sorted records
  const filteredRecords = useMemo(() => {
    return records
      .filter((r) => {
        // Search by filename or task
        if (search.trim()) {
          const q = search.toLowerCase();
          const matchName = r.fileName.toLowerCase().includes(q);
          const matchTask = r.taskId?.toLowerCase().includes(q);
          if (!matchName && !matchTask) return false;
        }
        // Format filter
        if (formatFilter !== "ALL" && r.format !== formatFilter) {
          return false;
        }
        // Status filter
        if (statusFilter !== "ALL" && r.status !== statusFilter) {
          return false;
        }
        return true;
      })
      .sort((a, b) => {
        if (sortOrder === "oldest") {
          return a.id.localeCompare(b.id);
        }
        return b.id.localeCompare(a.id);
      });
  }, [records, search, formatFilter, statusFilter, sortOrder]);

  // Handle Download from History
  const handleDownload = (record: ExportRecord) => {
    if (record.status !== "COMPLETED") return;

    // 1. Check in-memory session cache
    const cached = SESSION_EXPORT_BLOBS.get(record.id);
    if (cached) {
      downloadBlob(cached.blob, cached.fileName);
      toast.success("Download started.", {
        description: `Downloading ${cached.fileName}`,
      });
      return;
    }

    // 2. Generate on-the-fly from mock data if it was a pre-existing mock item
    const count = Math.min(record.recordCount || 10, MOCK_LEADS.length);
    const leadsSlice = MOCK_LEADS.slice(0, count);
    const nameWithoutExt = record.fileName.replace(/\.(csv|xlsx)$/i, "");

    if (record.format === "excel") {
      exportToExcel(leadsSlice, DEFAULT_SELECTED_FIELDS, nameWithoutExt);
    } else {
      exportToCsv(leadsSlice, DEFAULT_SELECTED_FIELDS, nameWithoutExt);
    }

    toast.success("Download started.", {
      description: `Downloading ${record.fileName}`,
    });
  };

  // Handle Record Delete
  const handleDeleteConfirm = (id: string) => {
    const updated = deleteExportRecord(id);
    setRecords(updated);
    toast.success("Export record deleted.", {
      description: "Removed from your export history.",
    });
  };

  return (
    <div className="space-y-6 pb-6">
      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            Exports
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            View your recently generated exports and download files.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={() => setExportModalOpen(true)}
            className="text-xs gap-1.5 bg-[#BE0B31] hover:bg-[#A5082A] text-white font-semibold rounded-xl shadow-xs"
          >
            <Download className="h-3.5 w-3.5" />
            <span>New Export</span>
          </Button>
        </div>
      </div>

      {/* ── Toolbar: Search, Filters & Sorting ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-3 rounded-xl border border-border/80 bg-white shadow-2xs">
        {/* Search */}
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search exports by filename or task..."
            className="pl-8 h-8 text-xs bg-slate-50/50 border-border/70"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Format Filter */}
          <Select
            value={formatFilter}
            onValueChange={(v) => setFormatFilter(v as "ALL" | ExportFormat)}
          >
            <SelectTrigger className="h-8 text-xs w-[125px]">
              <SelectValue placeholder="Format" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Formats</SelectItem>
              <SelectItem value="csv">CSV (.csv)</SelectItem>
              <SelectItem value="excel">Excel (.xlsx)</SelectItem>
            </SelectContent>
          </Select>

          {/* Status Filter */}
          <Select
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v as "ALL" | ExportStatus)}
          >
            <SelectTrigger className="h-8 text-xs w-[125px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Statuses</SelectItem>
              <SelectItem value="COMPLETED">Completed</SelectItem>
              <SelectItem value="FAILED">Failed</SelectItem>
            </SelectContent>
          </Select>

          {/* Sort Order */}
          <Select
            value={sortOrder}
            onValueChange={(v) => setSortOrder(v as "newest" | "oldest")}
          >
            <SelectTrigger className="h-8 text-xs w-[115px]">
              <SelectValue placeholder="Sort" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="newest">Newest First</SelectItem>
              <SelectItem value="oldest">Oldest First</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* ── Table & Cards or Empty State ── */}
      {filteredRecords.length > 0 ? (
        <>
          {/* Desktop Table View */}
          <div className="hidden md:block">
            <ExportHistoryTable
              records={filteredRecords}
              onDownload={handleDownload}
              onDeleteRequest={(record) => {
                setRecordToDelete(record);
                setDeleteDialogOpen(true);
              }}
            />
          </div>

          {/* Mobile Cards View */}
          <div className="grid grid-cols-1 gap-3 md:hidden">
            {filteredRecords.map((record) => (
              <ExportHistoryCard
                key={record.id}
                record={record}
                onDownload={handleDownload}
                onDeleteRequest={(r) => {
                  setRecordToDelete(r);
                  setDeleteDialogOpen(true);
                }}
              />
            ))}
          </div>
        </>
      ) : records.length === 0 ? (
        /* Empty State: No exports in storage */
        <div className="rounded-xl border border-dashed border-border bg-white p-12 text-center space-y-4">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center">
            <Download className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-foreground">No exports yet</h3>
            <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
              Your generated CSV and Excel files will appear here.
            </p>
          </div>
          <Button asChild size="sm" className="gap-1.5 text-xs">
            <Link href="/leads">
              <Users className="h-3.5 w-3.5" />
              <span>View Leads</span>
            </Link>
          </Button>
        </div>
      ) : (
        /* Empty Filter State */
        <div className="rounded-xl border border-border/80 bg-white p-8 text-center space-y-3">
          <p className="text-xs text-muted-foreground">
            No export records match your search and filter criteria.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setSearch("");
              setFormatFilter("ALL");
              setStatusFilter("ALL");
            }}
            className="text-xs"
          >
            Clear Filters
          </Button>
        </div>
      )}

      {/* Delete Record Dialog */}
      <DeleteExportDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        record={recordToDelete}
        onConfirm={handleDeleteConfirm}
      />

      {/* Reusable Export Dialog */}
      <ExportDialog
        open={exportModalOpen}
        onOpenChange={setExportModalOpen}
        allLeads={MOCK_LEADS}
        onExportComplete={(newRecord) => {
          setRecords((prev) => [newRecord, ...prev]);
        }}
      />
    </div>
  );
}
