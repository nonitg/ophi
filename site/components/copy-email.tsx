"use client";

import { useEffect, useState } from "react";
import { Icon } from "@/components/icons";
import { pill, pillIcon, pillTag } from "@/components/pill";

export function CopyEmail({ email, className }: { email: string; className?: string }) {
  const [status, setStatus] = useState<"idle" | "copied" | "manual">("idle");

  // Return to "Copy" so the address can be copied again.
  useEffect(() => {
    if (status !== "copied") return;
    const timer = setTimeout(() => setStatus("idle"), 2000);
    return () => clearTimeout(timer);
  }, [status]);

  async function copyAddress() {
    try {
      await navigator.clipboard.writeText(email);
      setStatus("copied");
    } catch {
      // Clipboard access can be blocked; the visible address stays selectable for manual copying.
      setStatus("manual");
    }
  }

  return (
    <span className={className}>
      <button type="button" className={pill({ className: "copy-email-button cursor-copy" })} onClick={copyAddress} aria-label={`Copy email address ${email}`}>
        <span className="text-[15px] select-text">{email}</span>
        <span className={pillTag()} aria-hidden="true" data-done={status === "copied" || undefined}>
          {status === "copied" ? "Copied" : "Copy"}
          <Icon name={status === "copied" ? "check" : "copy"} className={pillIcon} />
        </span>
      </button>
      <span className="sr-only" role="status">{status === "copied" ? "Email address copied to clipboard." : status === "manual" ? "Copy blocked. Select the address to copy it." : ""}</span>
    </span>
  );
}
