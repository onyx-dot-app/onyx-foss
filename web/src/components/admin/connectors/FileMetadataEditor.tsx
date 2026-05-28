"use client";

import { useState } from "react";
import { Button } from "@opal/components";
import { SvgPlus, SvgX } from "@opal/icons";
import Text from "@/refresh-components/texts/Text";

export interface FileMetadata {
  title?: string;
  link?: string;
  primary_owners?: string[];
  [key: string]: unknown;
}

interface CustomTag {
  key: string;
  value: string;
}

interface FileMetadataEditorProps {
  fileName: string;
  initialMetadata?: FileMetadata;
  onChange: (fileName: string, metadata: FileMetadata) => void;
}

function parseCustomTags(meta: FileMetadata): CustomTag[] {
  const reserved = new Set(["title", "link", "primary_owners"]);
  return Object.entries(meta)
    .filter(([k]) => !reserved.has(k))
    .map(([k, v]) => ({ key: k, value: String(v ?? "") }));
}

export function FileMetadataEditor({
  fileName,
  initialMetadata = {},
  onChange,
}: FileMetadataEditorProps) {
  const [title, setTitle] = useState(String(initialMetadata.title ?? ""));
  const [link, setLink] = useState(String(initialMetadata.link ?? ""));
  const [primaryOwners, setPrimaryOwners] = useState(
    (initialMetadata.primary_owners ?? []).join(", ")
  );
  const [customTags, setCustomTags] = useState<CustomTag[]>(() =>
    parseCustomTags(initialMetadata)
  );

  const emitChange = (
    newTitle: string,
    newLink: string,
    newPrimaryOwners: string,
    newCustomTags: CustomTag[]
  ) => {
    const meta: FileMetadata = {};
    if (newTitle) meta.title = newTitle;
    if (newLink) meta.link = newLink;
    const owners = newPrimaryOwners
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (owners.length > 0) meta.primary_owners = owners;
    for (const { key, value } of newCustomTags) {
      if (key) meta[key] = value;
    }
    onChange(fileName, meta);
  };

  const handleTitleChange = (val: string) => {
    setTitle(val);
    emitChange(val, link, primaryOwners, customTags);
  };

  const handleLinkChange = (val: string) => {
    setLink(val);
    emitChange(title, val, primaryOwners, customTags);
  };

  const handlePrimaryOwnersChange = (val: string) => {
    setPrimaryOwners(val);
    emitChange(title, link, val, customTags);
  };

  const addCustomTag = () => {
    const updated = [...customTags, { key: "", value: "" }];
    setCustomTags(updated);
    emitChange(title, link, primaryOwners, updated);
  };

  const updateCustomTag = (index: number, field: "key" | "value", val: string) => {
    const updated = customTags.map((tag, i) =>
      i === index ? { ...tag, [field]: val } : tag
    );
    setCustomTags(updated);
    emitChange(title, link, primaryOwners, updated);
  };

  const removeCustomTag = (index: number) => {
    const updated = customTags.filter((_, i) => i !== index);
    setCustomTags(updated);
    emitChange(title, link, primaryOwners, updated);
  };

  return (
    <div className="space-y-3 p-3 bg-background-50 rounded border border-border">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Text as="label" figureSmallValue className="block mb-1 font-medium">
            Title
          </Text>
          <input
            type="text"
            value={title}
            onChange={(e) => handleTitleChange(e.target.value)}
            placeholder={fileName}
            className="w-full text-sm border border-border rounded px-2 py-1.5 bg-background focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
        <div>
          <Text as="label" figureSmallValue className="block mb-1 font-medium">
            Link / URL
          </Text>
          <input
            type="url"
            value={link}
            onChange={(e) => handleLinkChange(e.target.value)}
            placeholder="https://..."
            className="w-full text-sm border border-border rounded px-2 py-1.5 bg-background focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
      </div>

      <div>
        <Text as="label" figureSmallValue className="block mb-1 font-medium">
          Primary Owners{" "}
          <span className="font-normal text-text-500">(comma-separated)</span>
        </Text>
        <input
          type="text"
          value={primaryOwners}
          onChange={(e) => handlePrimaryOwnersChange(e.target.value)}
          placeholder="Alice, Bob"
          className="w-full text-sm border border-border rounded px-2 py-1.5 bg-background focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      {/* Custom key-value tags */}
      {customTags.length > 0 && (
        <div className="space-y-2">
          <Text as="label" figureSmallValue className="block font-medium">
            Custom Tags
          </Text>
          {customTags.map((tag, index) => (
            <div key={index} className="flex gap-2 items-center">
              <input
                type="text"
                value={tag.key}
                onChange={(e) => updateCustomTag(index, "key", e.target.value)}
                placeholder="key"
                className="flex-1 text-sm border border-border rounded px-2 py-1.5 bg-background focus:outline-none focus:ring-1 focus:ring-accent"
              />
              <input
                type="text"
                value={tag.value}
                onChange={(e) => updateCustomTag(index, "value", e.target.value)}
                placeholder="value"
                className="flex-1 text-sm border border-border rounded px-2 py-1.5 bg-background focus:outline-none focus:ring-1 focus:ring-accent"
              />
              <Button
                icon={SvgX}
                variant="danger"
                prominence="tertiary"
                size="sm"
                onClick={() => removeCustomTag(index)}
                tooltip="Remove tag"
                title="Remove tag"
              />
            </div>
          ))}
        </div>
      )}

      <Button
        prominence="tertiary"
        size="sm"
        icon={SvgPlus}
        onClick={addCustomTag}
      >
        Add Custom Tag
      </Button>
    </div>
  );
}
