"use client";

import { Phone, Mail, MessageSquare, Globe, Copy, Check } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import type { Lead } from "@/types/lead";

interface LeadQuickActionsProps {
  lead: Lead;
}

export function LeadQuickActions({ lead }: LeadQuickActionsProps) {
  const [copiedPhone, setCopiedPhone] = useState(false);
  const [copiedEmail, setCopiedEmail] = useState(false);

  const copyText = async (text: string, label: string, type: "phone" | "email") => {
    try {
      await navigator.clipboard.writeText(text);
      if (type === "phone") {
        setCopiedPhone(true);
        setTimeout(() => setCopiedPhone(false), 2000);
      } else {
        setCopiedEmail(true);
        setTimeout(() => setCopiedEmail(false), 2000);
      }
      toast.success(`${label} copied.`);
    } catch {
      toast.error(`Failed to copy ${label}`);
    }
  };

  return (
    <div className="rounded-xl border border-border bg-white p-5 shadow-sm space-y-3">
      <h3 className="text-xs font-semibold text-foreground uppercase tracking-wider">
        Quick Contact Actions
      </h3>

      <div className="grid grid-cols-2 gap-2 text-xs">
        {/* Call */}
        {lead.phone ? (
          <Button
            variant="outline"
            size="sm"
            asChild
            className="h-9 gap-1.5 bg-white justify-start"
          >
            <a href={`tel:${lead.phone.replace(/\s+/g, "")}`}>
              <Phone className="h-3.5 w-3.5 text-blue-600" />
              <span>Call Phone</span>
            </a>
          </Button>
        ) : (
          <Button variant="outline" size="sm" disabled className="h-9 gap-1.5 justify-start opacity-40">
            <Phone className="h-3.5 w-3.5 text-muted-foreground" />
            <span>Call Phone</span>
          </Button>
        )}

        {/* Email */}
        {lead.email ? (
          <Button
            variant="outline"
            size="sm"
            asChild
            className="h-9 gap-1.5 bg-white justify-start"
          >
            <a href={`mailto:${lead.email}`}>
              <Mail className="h-3.5 w-3.5 text-amber-600" />
              <span>Send Email</span>
            </a>
          </Button>
        ) : (
          <Button variant="outline" size="sm" disabled className="h-9 gap-1.5 justify-start opacity-40">
            <Mail className="h-3.5 w-3.5 text-muted-foreground" />
            <span>Send Email</span>
          </Button>
        )}

        {/* WhatsApp */}
        {lead.whatsapp ? (
          <Button
            variant="outline"
            size="sm"
            asChild
            className="h-9 gap-1.5 bg-white justify-start text-emerald-700 hover:text-emerald-800 hover:bg-emerald-50"
          >
            <a
              href={`https://wa.me/${lead.whatsapp.replace(/\D/g, "")}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <MessageSquare className="h-3.5 w-3.5 text-emerald-600" />
              <span>WhatsApp</span>
            </a>
          </Button>
        ) : (
          <Button variant="outline" size="sm" disabled className="h-9 gap-1.5 justify-start opacity-40">
            <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />
            <span>WhatsApp</span>
          </Button>
        )}

        {/* Website */}
        {lead.website ? (
          <Button
            variant="outline"
            size="sm"
            asChild
            className="h-9 gap-1.5 bg-white justify-start text-primary"
          >
            <a href={lead.website} target="_blank" rel="noopener noreferrer">
              <Globe className="h-3.5 w-3.5" />
              <span>Website</span>
            </a>
          </Button>
        ) : (
          <Button variant="outline" size="sm" disabled className="h-9 gap-1.5 justify-start opacity-40">
            <Globe className="h-3.5 w-3.5 text-muted-foreground" />
            <span>Website</span>
          </Button>
        )}
      </div>

      <div className="pt-2 border-t border-border/60 flex items-center gap-2">
        {lead.phone && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => copyText(lead.phone!, "Phone number", "phone")}
            className="flex-1 h-7 text-[11px] gap-1 text-muted-foreground hover:text-foreground"
          >
            {copiedPhone ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
            <span>Copy Phone</span>
          </Button>
        )}

        {lead.email && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => copyText(lead.email!, "Email address", "email")}
            className="flex-1 h-7 text-[11px] gap-1 text-muted-foreground hover:text-foreground"
          >
            {copiedEmail ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
            <span>Copy Email</span>
          </Button>
        )}
      </div>
    </div>
  );
}
