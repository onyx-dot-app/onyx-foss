"use client";

import { useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { Route } from "next";
import {
  Button,
  InputTypeIn,
  MessageCard,
  Popover,
  Text,
} from "@opal/components";
import { IllustrationContent } from "@opal/layouts";
import SvgNoResult from "@opal/illustrations/no-result";
import {
  SvgBlocks,
  SvgEdit,
  SvgPlus,
  SvgSimpleLoader,
  SvgUploadCloud,
} from "@opal/icons";
import { SettingsLayouts, toast } from "@opal/layouts";
import TextSeparator from "@/refresh-components/TextSeparator";
import useOnMount from "@/hooks/useOnMount";
import useUserSkills from "@/hooks/useUserSkills";
import SkillCard, {
  type CustomSkillCardItem,
  type SkillCardItem,
} from "@/sections/cards/SkillCard";
import CreateSkillModal from "@/sections/modals/skills/CreateSkillModal";
import SkillPreviewModal from "@/sections/modals/SkillPreviewModal";
import type { BuiltinSkill, CustomSkill } from "@/lib/skills/types";
import LineItem from "@/refresh-components/buttons/LineItem";
import { setSkillEnabled } from "@/lib/skills/api";
import { useTranslations } from "next-intl";

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function SkillsPage() {
  const t = useTranslations("skills");
  const router = useRouter();
  const { data, error, isLoading, refresh } = useUserSkills();
  const [searchQuery, setSearchQuery] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [createMenuOpen, setCreateMenuOpen] = useState(false);
  const [previewTarget, setPreviewTarget] = useState<SkillCardItem | null>(
    null
  );
  const [pendingSkillIds, setPendingSkillIds] = useState<Set<string>>(
    new Set()
  );
  const [optimisticEnabledById, setOptimisticEnabledById] = useState<
    Map<string, boolean>
  >(new Map());
  const searchInputRef = useRef<HTMLInputElement>(null);

  useOnMount(() => {
    searchInputRef.current?.focus();
  });

  function handleEdit(item: CustomSkillCardItem) {
    router.push(`/craft/v1/skills/edit/${item.id}` as Route);
  }

  async function handleEnabledChange(item: SkillCardItem, enabled: boolean) {
    setPendingSkillIds((current) => new Set(current).add(item.id));
    setOptimisticEnabledById((current) =>
      new Map(current).set(item.id, enabled)
    );
    try {
      const updatedSkill = await setSkillEnabled(item.id, enabled);
      await refresh(
        (current) => {
          if (!current) return current;
          const key =
            updatedSkill.source === "builtin" ? "builtins" : "customs";
          return {
            ...current,
            [key]: current[key].map((skill) =>
              skill.id === updatedSkill.id ? updatedSkill : skill
            ),
          };
        },
        { revalidate: false }
      );
      void refresh().catch(() => {
        toast.error(
          `${item.name} was updated, but the skill list could not be refreshed.`
        );
      });
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : `Failed to ${enabled ? "enable" : "disable"} ${item.name}`
      );
    } finally {
      setOptimisticEnabledById((current) => {
        const next = new Map(current);
        next.delete(item.id);
        return next;
      });
      setPendingSkillIds((current) => {
        const next = new Set(current);
        next.delete(item.id);
        return next;
      });
    }
  }

  const items = useMemo<SkillCardItem[]>(() => {
    if (!data) return [];
    const builtinItems: SkillCardItem[] = data.builtins
      .filter(
        (b): b is BuiltinSkill =>
          b.source === "builtin" && b.is_available !== null
      )
      .map((b) => ({
        id: b.id,
        name: b.name,
        description: b.description,
        source: "builtin",
        enabled: optimisticEnabledById.get(b.id) ?? b.enabled,
        can_toggle: b.can_toggle,
        is_available: b.is_available,
        unavailable_reason: b.unavailable_reason,
      }));
    const customItems: SkillCardItem[] = data.customs
      .filter((c): c is CustomSkill => c.source === "custom")
      .map((c) => ({
        id: c.id,
        name: c.name,
        description: c.description,
        source: "custom",
        skill: c,
        author_email: c.author_email,
        is_personal: c.is_personal && c.user_permission === "OWNER",
        enabled: optimisticEnabledById.get(c.id) ?? c.enabled,
        can_toggle: c.can_toggle,
      }));
    // Group order: built-in, then custom (org-wide), then personal; alphabetical within each group.
    const groupRank = (item: SkillCardItem): number => {
      switch (item.source) {
        case "builtin":
          return 0;
        case "custom":
          return item.is_personal ? 2 : 1;
      }
    };
    return [...builtinItems, ...customItems].sort(
      (a, b) =>
        groupRank(a) - groupRank(b) ||
        a.name.localeCompare(b.name, undefined, { sensitivity: "base" })
    );
  }, [data, optimisticEnabledById]);

  const visibleItems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (item) =>
        item.name.toLowerCase().includes(q) ||
        item.description.toLowerCase().includes(q)
    );
  }, [items, searchQuery]);
  const previewUnavailableReason =
    previewTarget?.source === "builtin" && !previewTarget.is_available
      ? (previewTarget.unavailable_reason ??
        "This skill is currently unavailable.")
      : null;

  return (
    <SettingsLayouts.Root data-testid="SkillsPage/container">
      <SettingsLayouts.Header
        icon={SvgBlocks}
        title={t("title")}
        description={t("description")}
        rightChildren={
          <Popover open={createMenuOpen} onOpenChange={setCreateMenuOpen}>
            <Popover.Trigger asChild>
              <Button icon={SvgPlus}>{t("createSkill")}</Button>
            </Popover.Trigger>
            <Popover.Content align="end" sideOffset={4} width="xl">
              <Popover.Menu>
                <LineItem
                  icon={SvgEdit}
                  description={t("startFromScratchDescription")}
                  wrapDescription
                  onClick={() => {
                    setCreateMenuOpen(false);
                    router.push("/craft/v1/skills/new" as Route);
                  }}
                >
                  {t("startFromScratch")}
                </LineItem>
                <LineItem
                  icon={SvgUploadCloud}
                  description={t("uploadSkillDescription")}
                  wrapDescription
                  onClick={() => {
                    setCreateMenuOpen(false);
                    setCreateOpen(true);
                  }}
                >
                  {t("uploadSkill")}
                </LineItem>
              </Popover.Menu>
            </Popover.Content>
          </Popover>
        }
      >
        <InputTypeIn
          ref={searchInputRef}
          placeholder={t("searchPlaceholder")}
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
          searchIcon
        />
      </SettingsLayouts.Header>

      <SettingsLayouts.Body>
        {isLoading && <SvgSimpleLoader />}

        {error && !isLoading && (
          <MessageCard
            variant="error"
            title={t("failedToLoad")}
            description={t("failedToLoadDescription")}
          />
        )}

        {!isLoading && !error && (
          <>
            {visibleItems.length === 0 ? (
              <IllustrationContent
                illustration={SvgNoResult}
                title={
                  items.length === 0
                    ? t("noSkillsAvailable")
                    : t("noMatchingSkills")
                }
                description={
                  items.length === 0
                    ? t("noSkillsDescription")
                    : t("noMatchDescription")
                }
              />
            ) : (
              <>
                <section className="flex flex-col gap-2">
                  <Text font="secondary-body" color="text-03">
                    {t("browseSkills")}
                  </Text>
                  <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-2">
                    {visibleItems.map((item) => (
                      <SkillCard
                        key={item.id}
                        item={item}
                        onEdit={handleEdit}
                        onClick={setPreviewTarget}
                        onEnabledChange={handleEnabledChange}
                        enablementPending={pendingSkillIds.has(item.id)}
                      />
                    ))}
                  </div>
                </section>
                <TextSeparator
                  count={visibleItems.length}
                  text={visibleItems.length === 1 ? t("skill") : t("skills")}
                />
              </>
            )}
          </>
        )}
      </SettingsLayouts.Body>

      <CreateSkillModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(created) => {
          refresh();
          router.push(`/craft/v1/skills/edit/${created.id}` as Route);
        }}
      />

      <SkillPreviewModal
        open={previewTarget !== null}
        skillId={previewTarget?.id ?? null}
        fallbackTitle={previewTarget?.name}
        unavailableReason={previewUnavailableReason}
        onClose={() => setPreviewTarget(null)}
      />
    </SettingsLayouts.Root>
  );
}
