"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Text from "@/refresh-components/texts/Text";
import InputTypeIn from "@/refresh-components/inputs/InputTypeIn";
import InputTextArea from "@/refresh-components/inputs/InputTextArea";
import Button from "@/refresh-components/buttons/Button";
import { useRouter } from "next/navigation";

interface BrandingConfig {
  application_name: string | null;
  use_custom_logo: boolean;
  use_custom_logotype: boolean;
  logo_display_style: "logo_and_name" | "logo_only" | "name_only" | null;
  custom_nav_items: { link: string; title: string }[];
  custom_lower_disclaimer_content: string | null;
  custom_header_content: string | null;
  two_lines_for_chat_header: boolean | null;
  custom_popup_header: string | null;
  custom_popup_content: string | null;
  enable_consent_screen: boolean | null;
  consent_screen_prompt: string | null;
  show_first_visit_notice: boolean | null;
  custom_greeting_message: string | null;
}

const DEFAULTS: BrandingConfig = {
  application_name: null,
  use_custom_logo: false,
  use_custom_logotype: false,
  logo_display_style: null,
  custom_nav_items: [],
  custom_lower_disclaimer_content: null,
  custom_header_content: null,
  two_lines_for_chat_header: null,
  custom_popup_header: null,
  custom_popup_content: null,
  enable_consent_screen: null,
  consent_screen_prompt: null,
  show_first_visit_notice: null,
  custom_greeting_message: null,
};

export default function ExtBrandingAdminPage() {
  const [config, setConfig] = useState<BrandingConfig>(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const fetchConfig = useCallback(async () => {
    try {
      const res = await fetch("/api/admin/enterprise-settings");
      if (res.ok) {
        setConfig(await res.json());
      }
    } catch {
      setMessage({ type: "error", text: "Failed to load config" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const res = await fetch("/api/admin/enterprise-settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      if (res.ok) {
        setMessage({ type: "success", text: "Saved successfully" });
        router.refresh();
      } else {
        const err = await res.json();
        setMessage({
          type: "error",
          text: err.detail || "Save failed",
        });
      }
    } catch {
      setMessage({ type: "error", text: "Network error" });
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/admin/enterprise-settings/logo", {
        method: "PUT",
        body: formData,
      });
      if (res.ok) {
        setMessage({ type: "success", text: "Logo uploaded" });
        setConfig((prev) => ({ ...prev, use_custom_logo: true }));
      } else {
        const err = await res.json();
        setMessage({
          type: "error",
          text: err.detail || "Logo upload failed",
        });
      }
    } catch {
      setMessage({ type: "error", text: "Network error" });
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const update = <K extends keyof BrandingConfig>(
    key: K,
    value: BrandingConfig[K]
  ) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <div className="p-8">
        <Text headingH2>Branding</Text>
        <Text text03 className="p-4">
          Loading...
        </Text>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl">
      <Text headingH2>Branding Configuration</Text>
      <Text text03 className="pb-6">
        Configure the look and feel of your application.
      </Text>

      {message && (
        <div
          className={`p-3 rounded-08 mb-4 ${
            message.type === "success"
              ? "bg-status-success-01 text-status-success-03"
              : "bg-status-error-01 text-status-error-03"
          }`}
        >
          <Text>{message.text}</Text>
        </div>
      )}

      {/* App Name */}
      <div className="pb-6">
        <Text mainUiAction className="pb-2">
          Application Name
        </Text>
        <InputTypeIn
          value={config.application_name || ""}
          onChange={(e) =>
            update(
              "application_name",
              e.target.value || null
            )
          }
          placeholder="e.g. VÖB Chatbot"
          maxLength={50}
        />
      </div>

      {/* Logo */}
      <div className="pb-6">
        <Text mainUiAction className="pb-2">
          Logo
        </Text>
        <div className="flex items-center gap-4">
          {config.use_custom_logo && (
            <img
              src="/api/enterprise-settings/logo"
              alt="Current logo"
              className="w-10 h-10 rounded-full object-cover"
            />
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg"
            onChange={handleLogoUpload}
            className="text-sm text-text-03"
          />
        </div>
        <Text text03 className="pt-1">
          PNG or JPEG, max 2 MB
        </Text>
      </div>

      {/* Logo Display Style */}
      <div className="pb-6">
        <Text mainUiAction className="pb-2">
          Logo Display Style
        </Text>
        <select
          value={config.logo_display_style || ""}
          onChange={(e) =>
            update(
              "logo_display_style",
              (e.target.value || null) as BrandingConfig["logo_display_style"]
            )
          }
          className="w-full p-2 rounded-08 border border-border-02 bg-background-neutral-01 text-text-01"
        >
          <option value="">Default</option>
          <option value="logo_and_name">Logo + Name</option>
          <option value="logo_only">Logo Only</option>
          <option value="name_only">Name Only</option>
        </select>
      </div>

      {/* Chat Header */}
      <div className="pb-6">
        <Text mainUiAction className="pb-2">
          Header Content
        </Text>
        <InputTypeIn
          value={config.custom_header_content || ""}
          onChange={(e) =>
            update("custom_header_content", e.target.value || null)
          }
          placeholder="e.g. Bundesverband Öffentlicher Banken"
          maxLength={100}
        />
      </div>

      {/* Chat Greeting */}
      <div className="pb-6">
        <Text mainUiAction className="pb-2">
          Chat Greeting Message
        </Text>
        <InputTypeIn
          value={config.custom_greeting_message || ""}
          onChange={(e) =>
            update("custom_greeting_message", e.target.value || null)
          }
          placeholder="e.g. Wie kann ich Ihnen helfen?"
          maxLength={50}
        />
      </div>

      {/* Chat Footer */}
      <div className="pb-6">
        <Text mainUiAction className="pb-2">
          Chat Footer / Disclaimer
        </Text>
        <InputTypeIn
          value={config.custom_lower_disclaimer_content || ""}
          onChange={(e) =>
            update(
              "custom_lower_disclaimer_content",
              e.target.value || null
            )
          }
          placeholder="e.g. KI-generierte Antworten können fehlerhaft sein."
          maxLength={200}
        />
      </div>

      {/* Welcome Popup */}
      <div className="pb-6">
        <Text mainUiAction className="pb-2">
          First Visit Notice
        </Text>
        <label className="flex items-center gap-2 pb-2">
          <input
            type="checkbox"
            checked={config.show_first_visit_notice || false}
            onChange={(e) =>
              update("show_first_visit_notice", e.target.checked || null)
            }
          />
          <Text>Show popup on first visit</Text>
        </label>
        {config.show_first_visit_notice && (
          <div className="space-y-3 pt-2">
            <InputTypeIn
              value={config.custom_popup_header || ""}
              onChange={(e) =>
                update("custom_popup_header", e.target.value || null)
              }
              placeholder="Popup title"
              maxLength={100}
            />
            <InputTextArea
              value={config.custom_popup_content || ""}
              onChange={(e) =>
                update("custom_popup_content", e.target.value || null)
              }
              placeholder="Popup content (Markdown supported)"
              maxLength={500}
              rows={4}
            />
          </div>
        )}
      </div>

      {/* Consent Screen */}
      <div className="pb-6">
        <Text mainUiAction className="pb-2">
          Consent Screen
        </Text>
        <label className="flex items-center gap-2 pb-2">
          <input
            type="checkbox"
            checked={config.enable_consent_screen || false}
            onChange={(e) =>
              update("enable_consent_screen", e.target.checked || null)
            }
          />
          <Text>Require consent before using the app</Text>
        </label>
        {config.enable_consent_screen && (
          <InputTypeIn
            value={config.consent_screen_prompt || ""}
            onChange={(e) =>
              update("consent_screen_prompt", e.target.value || null)
            }
            placeholder="Consent text"
            maxLength={200}
          />
        )}
      </div>

      {/* Save */}
      <div className="flex gap-3">
        <Button main primary onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : "Save Configuration"}
        </Button>
      </div>
    </div>
  );
}
