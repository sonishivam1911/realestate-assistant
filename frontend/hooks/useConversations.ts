"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createConversation,
  deleteConversation,
  listConversations,
  updateConversation,
} from "@/lib/api";
import type { Conversation } from "@/types/chat";

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listConversations();
      setConversations(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load conversations");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const create = useCallback(
    async (
      title?: string,
      subject_address?: string,
      radius_miles = 5,
      user_email?: string,
    ) => {
      const conv = await createConversation({
        title,
        subject_address,
        radius_miles,
        user_email,
      });
      await refresh();
      return conv;
    },
    [refresh],
  );

  const updateEmail = useCallback(
    async (id: string, user_email: string) => {
      const conv = await updateConversation(id, { user_email });
      await refresh();
      return conv;
    },
    [refresh],
  );

  const remove = useCallback(
    async (id: string) => {
      await deleteConversation(id);
      await refresh();
    },
    [refresh],
  );

  return { conversations, loading, error, refresh, create, updateEmail, remove };
}
