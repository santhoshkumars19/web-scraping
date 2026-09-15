"use client";

import { useState } from "react";
import {
  Phone,
  Mail,
  MessageSquare,
  User,
  Copy,
  Check,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import type { Lead } from "@/types/lead";

interface ContactInformationProps {
  lead: Lead;
}

export function ContactInformation({ lead }: ContactInformationProps) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyToClipboard = async (text: string, label: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000);
      toast.success(`${label} copied.`);
    } catch {
      toast.error(`Unable to copy ${label}`);
    }
  };

  return (
    <div className="rounded-xl border border-border bg-white p-5 sm:p-6 shadow-sm">
      <div className="flex items-center gap-2 border-b border-border pb-3 mb-4">
        <Phone className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-foreground">Contact Information</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        {/* Primary Phone */}
        <div className="p-3.5 rounded-lg border border-border/70 bg-slate-50/50 flex flex-col justify-between gap-2.5">
          <div>
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
              Primary Phone Number
            </span>
            {lead.phone ? (
              <span className="text-sm font-semibold font-mono text-foreground">
                {lead.phone}
              </span>
            ) : (
              <span className="text-sm text-muted-foreground/60 italic">
                Not available
              </span>
            )}
          </div>

          {lead.phone && (
            <div className="flex items-center gap-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(lead.phone!, "Phone number", "phone")}
                className="h-7 text-xs gap-1.5 bg-white"
              >
                {copiedKey === "phone" ? (
                  <Check className="h-3 w-3 text-emerald-600" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
                <span>Copy</span>
              </Button>

              <Button
                size="sm"
                asChild
                className="h-7 text-xs gap-1.5 bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary"
              >
                <a href={`tel:${lead.phone.replace(/\s+/g, "")}`}>
                  <Phone className="h-3 w-3" />
                  <span>Call</span>
                </a>
              </Button>
            </div>
          )}
        </div>

        {/* Alternate Phone */}
        <div className="p-3.5 rounded-lg border border-border/70 bg-slate-50/50 flex flex-col justify-between gap-2.5">
          <div>
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
              Alternate Phone
            </span>
            {lead.alternatePhone ? (
              <span className="text-sm font-semibold font-mono text-foreground">
                {lead.alternatePhone}
              </span>
            ) : (
              <span className="text-sm text-muted-foreground/60 italic">
                Not available
              </span>
            )}
          </div>

          {lead.alternatePhone && (
            <div className="flex items-center gap-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(lead.alternatePhone!, "Alternate phone", "altPhone")}
                className="h-7 text-xs gap-1.5 bg-white"
              >
                {copiedKey === "altPhone" ? (
                  <Check className="h-3 w-3 text-emerald-600" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
                <span>Copy</span>
              </Button>

              <Button
                size="sm"
                asChild
                className="h-7 text-xs gap-1.5 bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary"
              >
                <a href={`tel:${lead.alternatePhone.replace(/\s+/g, "")}`}>
                  <Phone className="h-3 w-3" />
                  <span>Call</span>
                </a>
              </Button>
            </div>
          )}
        </div>

        {/* Official Email */}
        <div className="p-3.5 rounded-lg border border-border/70 bg-slate-50/50 flex flex-col justify-between gap-2.5">
          <div>
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
              Official Email Address
            </span>
            {lead.email ? (
              <span className="text-sm font-semibold text-foreground break-all">
                {lead.email}
              </span>
            ) : (
              <span className="text-sm text-muted-foreground/60 italic">
                Not available
              </span>
            )}
          </div>

          {lead.email && (
            <div className="flex items-center gap-2 pt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => copyToClipboard(lead.email!, "Email address", "email")}
                className="h-7 text-xs gap-1.5 bg-white"
              >
                {copiedKey === "email" ? (
                  <Check className="h-3 w-3 text-emerald-600" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
                <span>Copy</span>
              </Button>

              <Button
                size="sm"
                asChild
                className="h-7 text-xs gap-1.5 bg-primary/10 text-primary hover:bg-primary/20 hover:text-primary"
              >
                <a href={`mailto:${lead.email}`}>
                  <Mail className="h-3 w-3" />
                  <span>Email</span>
                </a>
              </Button>
            </div>
          )}
        </div>

        {/* WhatsApp */}
        <div className="p-3.5 rounded-lg border border-border/70 bg-slate-50/50 flex flex-col justify-between gap-2.5">
          <div>
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
              WhatsApp Business / Contact
            </span>
            {lead.whatsapp ? (
              <span className="text-sm font-semibold font-mono text-emerald-700">
                {lead.whatsapp}
              </span>
            ) : (
              <span className="text-sm text-muted-foreground/60 italic">
                Not available
              </span>
            )}
          </div>

          {lead.whatsapp && (
            <div className="flex items-center gap-2 pt-1">
              <Button
                size="sm"
                asChild
                className="h-7 text-xs gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <a
                  href={`https://wa.me/${lead.whatsapp.replace(/\D/g, "")}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <MessageSquare className="h-3 w-3" />
                  <span>Open WhatsApp</span>
                </a>
              </Button>
            </div>
          )}
        </div>

        {/* Contact Person */}
        <div className="p-3.5 rounded-lg border border-border/70 bg-slate-50/50 sm:col-span-2 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
              <User className="h-3 w-3 text-muted-foreground/70" />
              Primary Contact Person
            </span>
            {lead.contactPerson ? (
              <div>
                <p className="text-sm font-bold text-foreground">
                  {lead.contactPerson}
                </p>
                {lead.designation && (
                  <p className="text-xs text-muted-foreground">
                    {lead.designation}
                  </p>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground/60 italic">
                Not available
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
