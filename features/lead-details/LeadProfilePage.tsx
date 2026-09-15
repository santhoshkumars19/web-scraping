"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { getLead } from "@/services/leads";
import type { Lead } from "@/types/lead";

import { LeadProfileHeader } from "./components/LeadProfileHeader";
import { OrganizationOverview } from "./components/OrganizationOverview";
import { ContactInformation } from "./components/ContactInformation";
import { OnlinePresence } from "./components/OnlinePresence";
import { SourceInformation } from "./components/SourceInformation";
import { LeadActivity } from "./components/LeadActivity";
import { LeadQuickActions } from "./components/LeadQuickActions";
import { VerificationCard } from "./components/VerificationCard";
import { DataCoverage } from "./components/DataCoverage";
import { DiscoveryTaskCard } from "./components/DiscoveryTaskCard";
import { EditLeadDialog } from "./components/EditLeadDialog";
import { DeleteLeadModal } from "./components/DeleteLeadModal";
import { ExportDialog } from "@/features/export/ExportDialog";
import { LeadNotFound } from "./components/LeadNotFound";
import { LeadProfileSkeleton } from "./components/LeadProfileSkeleton";
import { LeadProfileError } from "./components/LeadProfileError";

interface LeadProfilePageProps {
  leadId: string;
}

export function LeadProfilePage({ leadId }: LeadProfilePageProps) {
  const router = useRouter();

  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [exportModalOpen, setExportModalOpen] = useState(false);

  // Load lead data from live API
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(false);
    setNotFound(false);

    try {
      const found = await getLead(leadId);
      setLead(found);
    } catch (err: unknown) {
      if (
        (err as { status?: number })?.status === 404 ||
        (err as Error)?.message?.toLowerCase().includes("not found")
      ) {
        setNotFound(true);
      } else {
        setError(true);
      }
    } finally {
      setLoading(false);
    }
  }, [leadId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Edit handler
  const handleSaveEdit = (updated: Lead) => {
    setLead(updated);
    toast.success("Lead updated.", {
      description: "Changes have been updated in your view.",
    });
  };

  // Delete handler
  const handleConfirmDelete = () => {
    if (!lead) return;
    toast.info("Lead deletion is governed by retention policies.");
    router.push("/leads");
  };

  // Export handler
  const handleExport = () => {
    setExportModalOpen(true);
  };

  if (loading) {
    return <LeadProfileSkeleton />;
  }

  if (notFound) {
    return <LeadNotFound />;
  }

  if (error || !lead) {
    return <LeadProfileError onRetry={loadData} />;
  }

  return (
    <div className="space-y-6 pb-6">
      {/* ── Header ── */}
      <LeadProfileHeader
        lead={lead}
        onEdit={() => setEditDialogOpen(true)}
        onDelete={() => setDeleteModalOpen(true)}
        onExport={handleExport}
      />

      {/* ── Main Two-Column Layout ── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left 2 Columns: Primary Data */}
        <div className="space-y-6 lg:col-span-2">
          <OrganizationOverview lead={lead} />
          <ContactInformation lead={lead} />
          <OnlinePresence socialLinks={lead.socialLinks} />
          <SourceInformation sourcePages={lead.sourcePages} website={lead.website} />
          <LeadActivity lead={lead} />
        </div>

        {/* Right 1 Column: Meta & Verification */}
        <div className="space-y-6">
          <LeadQuickActions lead={lead} />
          <VerificationCard verification={lead.verification} />
          <DataCoverage lead={lead} />
          <DiscoveryTaskCard lead={lead} />
        </div>
      </div>

      {/* ── Modals & Dialogs ── */}
      <EditLeadDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        lead={lead}
        onSave={handleSaveEdit}
      />

      <DeleteLeadModal
        open={deleteModalOpen}
        onOpenChange={setDeleteModalOpen}
        organizationName={lead.organizationName}
        onConfirm={handleConfirmDelete}
      />

      <ExportDialog
        open={exportModalOpen}
        onOpenChange={setExportModalOpen}
        singleLead={lead}
        dialogTitle="Export Lead Profile"
        dialogSubtitle={`Export data record for ${lead.organizationName}.`}
        initialSourceType="SINGLE_LEAD"
      />
    </div>
  );
}
