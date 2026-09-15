"use client";

import { useState, useMemo, useEffect, useCallback } from "react";
import Link from "next/link";
import { Plus, Download, RefreshCw, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PrimaryButton } from "@/components/shared/PrimaryButton";
import { toast } from "sonner";

import { getLeads, getTaskLeads, type LeadQueryParams } from "@/services/leads";
import type {
  Lead,
  LeadFilterState,
  LeadSortField,
  SortDirection,
  ColumnVisibilityState,
} from "@/types/lead";

import { LeadSummaryCards } from "./components/LeadSummaryCards";
import { LeadSearch } from "./components/LeadSearch";
import { LeadFilters } from "./components/LeadFilters";
import { ActiveFilterChips } from "./components/ActiveFilterChips";
import { ColumnVisibility } from "./components/ColumnVisibility";
import { BulkActionBar } from "./components/BulkActionBar";
import { DeleteLeadDialog } from "./components/DeleteLeadDialog";
import { ExportDialog } from "@/features/export/ExportDialog";
import type { ExportSourceType } from "@/types/export";
import { LeadTable } from "./components/LeadTable";
import { LeadMobileCard } from "./components/LeadMobileCard";
import { LeadPagination } from "./components/LeadPagination";
import { EmptyLeadsState } from "./components/EmptyLeadsState";
import { LeadsLoadingState } from "./components/LeadsLoadingState";
import { LeadsErrorState } from "./components/LeadsErrorState";

const DEFAULT_FILTERS: LeadFilterState = {
  search: "",
  categories: [],
  locations: [],
  verifications: [],
  hasPhone: false,
  hasEmail: false,
  hasWebsite: false,
  hasWhatsApp: false,
  hasContactPerson: false,
  hasSocialLinks: false,
  taskId: "",
  dateRange: "all",
};

const DEFAULT_COLUMNS: ColumnVisibilityState = {
  organization: true,
  category: true,
  location: true,
  phone: true,
  email: true,
  website: true,
  address: true,
  whatsapp: true,
  contactPerson: true,
  verification: true,
  scrapedDate: true,
};

interface LeadsPageProps {
  initialTaskId?: string;
}

export function LeadsPage({ initialTaskId }: LeadsPageProps) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Filters & Search
  const [filters, setFilters] = useState<LeadFilterState>(() => ({
    ...DEFAULT_FILTERS,
    taskId: initialTaskId || "",
  }));

  // Debounced search state (350ms)
  const [debouncedSearch, setDebouncedSearch] = useState(filters.search);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(filters.search);
    }, 350);
    return () => clearTimeout(timer);
  }, [filters.search]);

  // Sorting
  const [sortField, setSortField] = useState<LeadSortField>("organizationName");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Selection
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Modals
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [leadToDelete, setLeadToDelete] = useState<Lead | null>(null);
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [exportSourceType, setExportSourceType] = useState<ExportSourceType>("ALL_LEADS");

  // Column Visibility
  const [columns, setColumns] = useState<ColumnVisibilityState>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("leadscout_col_visibility");
        if (saved) return JSON.parse(saved);
      } catch {}
    }
    return DEFAULT_COLUMNS;
  });

  // Update taskId filter if query prop changes
  useEffect(() => {
    if (initialTaskId) {
      setFilters((prev) => ({ ...prev, taskId: initialTaskId }));
    }
  }, [initialTaskId]);

  // Map frontend sort fields to backend column keys
  const backendSortBy = useMemo<LeadQueryParams["sortBy"]>(() => {
    switch (sortField) {
      case "organizationName":
        return "organization";
      case "category":
        return "category";
      case "location":
        return "location";
      case "verification":
        return "verification";
      default:
        return "scraped_date";
    }
  }, [sortField]);

  // Active filter count
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.categories.length > 0) count += filters.categories.length;
    if (filters.locations.length > 0) count += filters.locations.length;
    if (filters.verifications.length > 0) count += filters.verifications.length;
    if (filters.hasPhone) count += 1;
    if (filters.hasEmail) count += 1;
    if (filters.hasWebsite) count += 1;
    if (filters.hasWhatsApp) count += 1;
    if (filters.hasContactPerson) count += 1;
    if (filters.hasSocialLinks) count += 1;
    if (filters.taskId && filters.taskId !== initialTaskId) count += 1;
    return count;
  }, [filters, initialTaskId]);

  const isFiltered = useMemo(() => {
    return Boolean(filters.search || activeFilterCount > 0);
  }, [filters.search, activeFilterCount]);

  // ── Data Fetching Pipeline ──────────────────────────────────────────────────

  const loadLeads = useCallback(async () => {
    setLoading(true);
    setError(false);

    try {
      const isTaskScoped = Boolean(filters.taskId);
      const params = {
        page,
        limit: pageSize,
        search: debouncedSearch || undefined,
        category: filters.categories[0] || undefined,
        location: filters.locations[0] || undefined,
        verification: filters.verifications[0] || undefined,
        hasPhone: filters.hasPhone ? true : undefined,
        hasEmail: filters.hasEmail ? true : undefined,
        hasWebsite: filters.hasWebsite ? true : undefined,
        hasWhatsApp: filters.hasWhatsApp ? true : undefined,
        hasContactPerson: filters.hasContactPerson ? true : undefined,
        hasSocialLinks: filters.hasSocialLinks ? true : undefined,
        sortBy: backendSortBy,
        sortOrder: sortDirection,
      };

      const result = isTaskScoped
        ? await getTaskLeads(filters.taskId, params)
        : await getLeads(params);

      setLeads(result.data);
      setTotalItems(result.pagination.total);
      setTotalPages(result.pagination.totalPages);
    } catch (err) {
      console.error("Failed to load leads from backend:", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [
    filters,
    debouncedSearch,
    page,
    pageSize,
    backendSortBy,
    sortDirection,
    sortField,
  ]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  // Sorting toggle
  const handleSortChange = (field: LeadSortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
    setPage(1);
  };

  // Selection handlers
  const handleToggleSelectAll = () => {
    const visibleIds = leads.map((l) => l.id);
    const allVisibleSelected = visibleIds.every((id) => selectedIds.includes(id));

    if (allVisibleSelected) {
      setSelectedIds((prev) => prev.filter((id) => !visibleIds.includes(id)));
    } else {
      setSelectedIds((prev) => Array.from(new Set([...prev, ...visibleIds])));
    }
  };

  const handleToggleSelectOne = (id: string, selected: boolean) => {
    if (selected) {
      setSelectedIds((prev) => [...prev, id]);
    } else {
      setSelectedIds((prev) => prev.filter((item) => item !== id));
    }
  };

  const handleDeselectAll = () => {
    setSelectedIds([]);
  };

  // Refresh handler
  const handleRefresh = useCallback(() => {
    loadLeads();
    toast.success("Leads refreshed.");
  }, [loadLeads]);

  // Filter reset
  const handleResetFilters = () => {
    setFilters({ ...DEFAULT_FILTERS, taskId: initialTaskId || "" });
    setPage(1);
  };

  // Delete requests
  const handleDeleteSingleRequest = (lead: Lead) => {
    setLeadToDelete(lead);
    setDeleteDialogOpen(true);
  };

  const handleDeleteBulkRequest = () => {
    setLeadToDelete(null);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (leadToDelete) {
      setLeads((prev) => prev.filter((l) => l.id !== leadToDelete.id));
      setSelectedIds((prev) => prev.filter((id) => id !== leadToDelete.id));
      setTotalItems((prev) => Math.max(0, prev - 1));
      toast.success("1 lead deleted.");
      setLeadToDelete(null);
    } else if (selectedIds.length > 0) {
      const count = selectedIds.length;
      setLeads((prev) => prev.filter((l) => !selectedIds.includes(l.id)));
      setSelectedIds([]);
      setTotalItems((prev) => Math.max(0, prev - count));
      toast.success(`${count} leads deleted.`);
    }
  };

  if (error) {
    return (
      <LeadsErrorState
        onRetry={() => {
          setError(false);
          loadLeads();
        }}
      />
    );
  }

  return (
    <div className="space-y-6 pb-6">
      {/* ── Optional Task Origin Banner ── */}
      {initialTaskId && (
        <div className="flex items-center justify-between p-3 rounded-xl bg-primary/5 border border-primary/20 text-xs">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" asChild className="h-7 -ml-1 gap-1 text-primary hover:text-primary/80">
              <Link href={`/tasks/${initialTaskId}/progress`}>
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Task Progress</span>
              </Link>
            </Button>
            <span className="text-muted-foreground">·</span>
            <span className="text-muted-foreground">
              Displaying leads scraped by task{" "}
              <span className="font-mono font-semibold text-primary">{initialTaskId}</span>
            </span>
          </div>

          <button
            onClick={() => setFilters((prev) => ({ ...prev, taskId: "" }))}
            className="text-[11px] text-primary hover:underline"
          >
            Show All Leads
          </button>
        </div>
      )}

      {/* ── Page Header ── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-[-0.035em] text-[#0E0E0E]">Leads</h1>
          <p className="text-xs text-[#5C5A53] mt-0.5">
            Manage, review, and organize your discovered organizations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            className="h-9 gap-1.5 text-xs bg-white"
            title="Reload leads"
          >
            <RefreshCw className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="hidden sm:inline">Refresh</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setExportSourceType(
                isFiltered ? "FILTERED_LEADS" : "ALL_LEADS"
              );
              setExportModalOpen(true);
            }}
            className="h-9 gap-1.5 text-xs bg-white font-medium"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export</span>
          </Button>

          <PrimaryButton asChild className="h-9 text-xs">
            <Link href="/tasks/new">
              <Plus className="h-4 w-4" />
              <span>New Scraping Task</span>
            </Link>
          </PrimaryButton>
        </div>
      </div>

      {/* ── Summary Metrics ── */}
      <LeadSummaryCards
        leads={leads}
        totalUnfiltered={totalItems}
        isFiltered={isFiltered}
      />

      {/* ── Loading Skeleton ── */}
      {loading ? (
        <LeadsLoadingState />
      ) : leads.length === 0 ? (
        <EmptyLeadsState
          isSearchOrFilter={isFiltered}
          onClearFilters={handleResetFilters}
        />
      ) : (
        <div className="space-y-3">
          {/* ── Search & Filter Controls ── */}
          <div className="flex flex-col sm:flex-row gap-2.5 items-stretch sm:items-center justify-between">
            <LeadSearch
              value={filters.search}
              onChange={(val) => {
                setFilters((prev) => ({ ...prev, search: val }));
                setPage(1);
              }}
              resultCount={totalItems}
            />

            <div className="flex items-center gap-2 shrink-0">
              <LeadFilters
                filters={filters}
                onFilterChange={(f) => {
                  setFilters(f);
                  setPage(1);
                }}
                onReset={handleResetFilters}
                activeCount={activeFilterCount}
              />

              <ColumnVisibility columns={columns} onChange={setColumns} />
            </div>
          </div>

          {/* ── Active Filter Chips ── */}
          <ActiveFilterChips
            filters={filters}
            onFilterChange={(f) => {
              setFilters(f);
              setPage(1);
            }}
            onReset={handleResetFilters}
          />

          {/* ── Bulk Action Toolbar (When rows selected) ── */}
          <BulkActionBar
            selectedCount={selectedIds.length}
            onDeselectAll={handleDeselectAll}
            onExportSelected={() => {
              setExportSourceType("SELECTED_LEADS");
              setExportModalOpen(true);
            }}
            onDeleteSelected={handleDeleteBulkRequest}
          />

          {/* ── Table & Cards Results ── */}
          <>
            {/* Desktop / Tablet Table View */}
            <div className="hidden md:block">
              <LeadTable
                leads={leads}
                selectedIds={selectedIds}
                onToggleSelectAll={handleToggleSelectAll}
                onToggleSelectOne={handleToggleSelectOne}
                sortField={sortField}
                sortDirection={sortDirection}
                onSortChange={handleSortChange}
                columns={columns}
                onDeleteRequest={handleDeleteSingleRequest}
              />
            </div>

            {/* Mobile Card List View */}
            <div className="md:hidden space-y-3">
              {leads.map((lead) => (
                <LeadMobileCard
                  key={lead.id}
                  lead={lead}
                  isSelected={selectedIds.includes(lead.id)}
                  onSelectChange={(selected) =>
                    handleToggleSelectOne(lead.id, selected)
                  }
                  onDeleteRequest={handleDeleteSingleRequest}
                />
              ))}
            </div>

            {/* Pagination */}
            <LeadPagination
              currentPage={page}
              totalPages={totalPages}
              pageSize={pageSize}
              totalItems={totalItems}
              onPageChange={setPage}
              onPageSizeChange={(size) => {
                setPageSize(size);
                setPage(1);
              }}
            />
          </>
        </div>
      )}

      {/* ── Delete Confirmation Dialog ── */}
      <DeleteLeadDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        count={leadToDelete ? 1 : selectedIds.length}
        onConfirm={handleConfirmDelete}
      />

      {/* ── Reusable Export Dialog ── */}
      <ExportDialog
        open={exportModalOpen}
        onOpenChange={setExportModalOpen}
        allLeads={leads}
        filteredLeads={leads}
        selectedLeads={leads.filter((l) => selectedIds.includes(l.id))}
        initialSourceType={exportSourceType}
        taskId={filters.taskId || undefined}
      />
    </div>
  );
}
