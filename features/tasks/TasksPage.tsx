"use client";

import { useState, useMemo, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PrimaryButton } from "@/components/shared/PrimaryButton";
import { toast } from "sonner";

import type {
  TaskItem,
  TaskFilterState,
  TaskSortField,
  SortDirection,
  TaskHistoryStatus,
} from "@/types/task";
import { saveDraft } from "@/types/task-form";
import { tasksApi, BackendTaskListItem } from "@/lib/api";

import { TaskSummaryCards } from "./components/TaskSummaryCards";
import { TaskSearch } from "./components/TaskSearch";
import { TaskStatusTabs } from "./components/TaskStatusTabs";
import { TaskFilters } from "./components/TaskFilters";
import { TaskActiveFilterChips } from "./components/TaskActiveFilterChips";
import { TaskTable } from "./components/TaskTable";
import { TaskMobileCard } from "./components/TaskMobileCard";
import { TaskPagination } from "./components/TaskPagination";
import { TaskBulkActionBar } from "./components/TaskBulkActionBar";
import { CancelTaskDialog } from "./components/CancelTaskDialog";
import { DeleteTaskDialog } from "./components/DeleteTaskDialog";
import { ExportDialog } from "@/features/export/ExportDialog";
import { TaskEmptyState } from "./components/TaskEmptyState";
import { TaskLoadingSkeleton } from "./components/TaskLoadingSkeleton";
import { TaskErrorState } from "./components/TaskErrorState";

const DEFAULT_FILTERS: TaskFilterState = {
  search: "",
  status: [],
  locations: [],
  dateRange: "all",
  hasResults: "all",
};

function mapBackendTaskToItem(t: BackendTaskListItem): TaskItem {
  return {
    id: t.task_id,
    keyword: t.keyword,
    location: t.location,
    searchRadius: "25 km",
    maxResults: 50,
    maxPagesPerSite: 5,
    status: (t.status?.toUpperCase() as TaskHistoryStatus) || "PENDING",
    progress: t.progress,
    resultsCount: t.results_count,
    verifiedCount: t.verified_count,
    createdAt: new Date(t.created_at).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }),
    duration: t.duration ? `${t.duration}s` : "—",
  };
}

export function TasksPage() {
  const router = useRouter();

  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Filters & Tabs
  const [statusTab, setStatusTab] = useState<TaskHistoryStatus | "ALL">("ALL");
  const [filters, setFilters] = useState<TaskFilterState>(DEFAULT_FILTERS);

  // Debounced search
  const [debouncedSearch, setDebouncedSearch] = useState(filters.search);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(filters.search), 350);
    return () => clearTimeout(timer);
  }, [filters.search]);

  // Sorting
  const [sortField, setSortField] = useState<TaskSortField>("createdAt");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Selection
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // Dialogs
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [taskToCancel, setTaskToCancel] = useState<TaskItem | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [taskToDelete, setTaskToDelete] = useState<TaskItem | null>(null);
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [taskToExport, setTaskToExport] = useState<TaskItem | null>(null);

  // ── Load tasks from live API ────────────────────────────────────────────────
  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(false);

    try {
      let statusParam: string | undefined = undefined;
      if (statusTab !== "ALL") {
        statusParam = statusTab;
      } else if (filters.status.length === 1) {
        statusParam = filters.status[0];
      }

      let sortByBackend = "created_at";
      if (sortField === "keyword") sortByBackend = "keyword";
      else if (sortField === "location") sortByBackend = "location";
      else if (sortField === "status") sortByBackend = "status";
      else if (sortField === "resultsCount") sortByBackend = "results_count";

      const res = await tasksApi.getTasks({
        page,
        limit: pageSize,
        search: debouncedSearch || undefined,
        status: statusParam,
        location: filters.locations[0] || undefined,
        sort_by: sortByBackend,
        sort_order: sortDirection,
      });

      const mapped = (res.data || []).map(mapBackendTaskToItem);
      setTasks(mapped);
      setTotalItems(res.pagination.total);
      setTotalPages(res.pagination.total_pages);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, debouncedSearch, statusTab, filters.status, filters.locations, sortField, sortDirection]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  // Sync tab clicks with filters.status
  const handleStatusTabSelect = (tab: TaskHistoryStatus | "ALL") => {
    setStatusTab(tab);
    setFilters((prev) => ({
      ...prev,
      status: tab === "ALL" ? [] : [tab],
    }));
    setPage(1);
  };

  // Sync advanced filter status changes back to tab
  const handleFilterChange = (newFilters: TaskFilterState) => {
    setFilters(newFilters);
    if (newFilters.status.length === 1) {
      setStatusTab(newFilters.status[0]);
    } else {
      setStatusTab("ALL");
    }
    setPage(1);
  };

  // Status counts for tabs
  const tabCounts = useMemo(() => {
    return {
      all: totalItems,
      running: tasks.filter((t) => t.status === "RUNNING").length,
      completed: tasks.filter((t) => t.status === "COMPLETED").length,
      failed: tasks.filter((t) => t.status === "FAILED").length,
      cancelled: tasks.filter((t) => t.status === "CANCELLED").length,
    };
  }, [totalItems, tasks]);

  // Active filter count
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.status.length > 0 && statusTab === "ALL") count += filters.status.length;
    if (filters.locations.length > 0) count += filters.locations.length;
    if (filters.hasResults !== "all") count += 1;
    if (filters.dateRange !== "all") count += 1;
    return count;
  }, [filters, statusTab]);

  const isFiltered = useMemo(() => {
    return Boolean(filters.search || activeFilterCount > 0 || statusTab !== "ALL");
  }, [filters.search, activeFilterCount, statusTab]);

  // Sorting change
  const handleSortChange = (field: TaskSortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  // Selection handlers
  const handleToggleSelectAll = () => {
    const visibleIds = tasks.map((t) => t.id);
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

  // Reset all filters
  const handleResetFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setStatusTab("ALL");
    setPage(1);
  };

  // Cancel Task Action
  const handleCancelRequest = (task: TaskItem) => {
    setTaskToCancel(task);
    setCancelDialogOpen(true);
  };

  const handleConfirmCancel = () => {
    if (!taskToCancel) return;
    toast.info("Cancellation notice received. Any collected data remains preserved.");
    setTaskToCancel(null);
    setCancelDialogOpen(false);
  };

  // Delete Task
  const handleDeleteRequest = (task: TaskItem) => {
    setTaskToDelete(task);
    setDeleteDialogOpen(true);
  };

  const handleDeleteBulkRequest = () => {
    setTaskToDelete(null);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    toast.info("Task deletion is restricted to administrative retention policies.");
    setDeleteDialogOpen(false);
    setTaskToDelete(null);
  };

  // Retry / Duplicate Task: navigate to /tasks/new with pre-filled values
  const handleRetryRequest = (task: TaskItem) => {
    saveDraft({
      location: task.location,
      keyword: task.keyword,
      searchRadius: task.searchRadius || "25",
      maxResults: task.maxResults || 100,
      maxPagesPerSite: task.maxPagesPerSite || 20,
      selectedFields: task.selectedFields || ["phone", "email", "website", "address"],
      crawlDepth: 3,
      followInternalLinks: true,
      prioritizeContact: true,
      prioritizeAbout: true,
      prioritizeAdmissions: true,
      prioritizeStaffManagement: true,
    });
    router.push(
      `/tasks/new?keyword=${encodeURIComponent(task.keyword)}&location=${encodeURIComponent(
        task.location
      )}`
    );
  };

  const handleDuplicateRequest = (task: TaskItem) => {
    handleRetryRequest(task);
  };

  // Export Task Leads
  const handleExportRequest = (task: TaskItem) => {
    setTaskToExport(task);
    setExportModalOpen(true);
  };

  return (
    <div className="space-y-6 pb-6">
      {/* ── Page Header ── */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            Task History
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Monitor background discovery pipelines, review active crawls, and access generated leads.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={loadTasks}
            disabled={loading}
            className="h-9 gap-1.5 text-xs bg-white hover:bg-slate-50 border-border"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </Button>

          <PrimaryButton asChild size="sm" className="h-9 gap-1.5 text-xs">
            <Link href="/tasks/new">
              <Plus className="h-3.5 w-3.5" />
              <span>New Task</span>
            </Link>
          </PrimaryButton>
        </div>
      </div>

      {/* ── Metric Cards ── */}
      <TaskSummaryCards
        tasks={tasks}
        totalUnfiltered={totalItems}
        isFiltered={isFiltered}
      />

      {/* ── Search & Filter Controls ── */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <TaskSearch
            value={filters.search}
            onChange={(val) => {
              setFilters((prev) => ({ ...prev, search: val }));
              setPage(1);
            }}
            resultCount={totalItems}
          />

          <TaskFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            onReset={handleResetFilters}
            activeCount={activeFilterCount}
          />
        </div>

        {/* Status Tab Bar */}
        <TaskStatusTabs
          selectedStatus={statusTab}
          onSelect={handleStatusTabSelect}
          counts={tabCounts}
        />

        {/* Active Filter Chips */}
        {isFiltered && (
          <TaskActiveFilterChips
            filters={filters}
            onFilterChange={(f) => {
              setFilters(f);
              setPage(1);
            }}
            onReset={handleResetFilters}
          />
        )}
      </div>

      {/* ── Main Data Display ── */}
      {loading ? (
        <TaskLoadingSkeleton />
      ) : error ? (
        <TaskErrorState onRetry={loadTasks} />
      ) : tasks.length === 0 ? (
        <TaskEmptyState isSearchOrFilter={isFiltered} onClearFilters={handleResetFilters} />
      ) : (
        <>
          {/* Desktop Table View */}
          <div className="hidden md:block">
            <TaskTable
              tasks={tasks}
              selectedIds={selectedIds}
              onToggleSelectAll={handleToggleSelectAll}
              onToggleSelectOne={handleToggleSelectOne}
              sortField={sortField}
              sortDirection={sortDirection}
              onSortChange={handleSortChange}
              onCancelRequest={handleCancelRequest}
              onDeleteRequest={handleDeleteRequest}
              onRetryRequest={handleRetryRequest}
              onDuplicateRequest={handleDuplicateRequest}
              onExportRequest={handleExportRequest}
            />
          </div>

          {/* Mobile Cards View */}
          <div className="space-y-3 md:hidden">
            {tasks.map((task) => (
              <TaskMobileCard
                key={task.id}
                task={task}
                isSelected={selectedIds.includes(task.id)}
                onSelectChange={(selected: boolean) => handleToggleSelectOne(task.id, selected)}
                onCancelRequest={() => handleCancelRequest(task)}
                onDeleteRequest={() => handleDeleteRequest(task)}
                onRetryRequest={() => handleRetryRequest(task)}
                onDuplicateRequest={() => handleDuplicateRequest(task)}
                onExportRequest={() => handleExportRequest(task)}
              />
            ))}
          </div>

          {/* Pagination */}
          <TaskPagination
            currentPage={page}
            totalPages={totalPages}
            totalItems={totalItems}
            pageSize={pageSize}
            onPageChange={setPage}
            onPageSizeChange={(newSize) => {
              setPageSize(newSize);
              setPage(1);
            }}
          />
        </>
      )}

      {/* Bulk Action Bar */}
      <TaskBulkActionBar
        selectedCount={selectedIds.length}
        onDeselectAll={handleDeselectAll}
        onDeleteSelected={handleDeleteBulkRequest}
      />

      {/* Dialogs */}
      <CancelTaskDialog
        open={cancelDialogOpen}
        onOpenChange={setCancelDialogOpen}
        taskId={taskToCancel?.id || ""}
        onConfirm={handleConfirmCancel}
      />

      <DeleteTaskDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        count={selectedIds.length || (taskToDelete ? 1 : 0)}
        taskId={taskToDelete?.id}
        onConfirm={handleConfirmDelete}
      />

      {taskToExport && (
        <ExportDialog
          open={exportModalOpen}
          onOpenChange={setExportModalOpen}
          taskId={taskToExport.id}
          dialogTitle="Export Task Results"
          dialogSubtitle={`Export all leads discovered during ${taskToExport.id}.`}
          initialSourceType="TASK"
        />
      )}
    </div>
  );
}
