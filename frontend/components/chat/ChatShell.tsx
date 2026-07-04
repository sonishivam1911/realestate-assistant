"use client";

import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Composer } from "@/components/chat/Composer";
import { EmailChip } from "@/components/chat/EmailChip";
import { MessageList } from "@/components/chat/MessageList";
import { SettingsPanel } from "@/components/chat/SettingsPanel";
import { Sidebar, type SidebarView } from "@/components/chat/Sidebar";
import { Welcome } from "@/components/chat/Welcome";
import { useConversations } from "@/hooks/useConversations";
import { getMessages } from "@/lib/api";
import { isValidEmail } from "@/lib/emailStorage";
import {
  loadSettings,
  saveSettings,
  type UserSettings,
  validateSettings,
} from "@/lib/settingsStorage";
import { storedToUiMessages } from "@/lib/messages";
import styles from "./ChatShell.module.css";

export function ChatShell() {
  const [input, setInput] = useState("");
  const [radiusMiles, setRadiusMiles] = useState(5);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [settings, setSettings] = useState<UserSettings>({
    email: "",
    emailDeliveryEnabled: true,
  });
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [view, setView] = useState<SidebarView>("chat");

  const {
    conversations,
    loading: loadingConversations,
    refresh,
    create,
    updateEmail,
    remove,
  } = useConversations();

  useEffect(() => {
    setSettings(loadSettings());
  }, []);

  const hasEmail = isValidEmail(settings.email);
  const emailDeliveryOn = settings.emailDeliveryEnabled;

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: "/api/chat",
        prepareSendMessagesRequest: ({ messages, id, body }) => ({
          body: {
            ...body,
            messages,
            id,
            conversation_id: conversationId ?? id,
            radius_miles: radiusMiles,
            user_email: settings.email.trim() || undefined,
            email_delivery_enabled: settings.emailDeliveryEnabled,
          },
        }),
      }),
    [conversationId, radiusMiles, settings],
  );

  const { messages, sendMessage, status, stop, setMessages } = useChat({
    transport,
    onFinish: () => {
      refresh();
    },
  });

  const isLoading = status === "submitted" || status === "streaming";

  const applySettings = useCallback((next: UserSettings) => {
    setSettings(next);
    saveSettings(next);
    setSettingsError(null);
  }, []);

  const loadConversation = useCallback(
    async (id: string) => {
      setLoadingHistory(true);
      setConversationId(id);
      try {
        const rows = await getMessages(id);
        setMessages(storedToUiMessages(rows));
        const conv = conversations.find((c) => c.id === id);
        if (conv?.radius_miles) setRadiusMiles(conv.radius_miles);
        if (conv?.user_email) {
          applySettings({
            ...loadSettings(),
            email: conv.user_email,
          });
        }
      } catch (e) {
        console.error(e);
        setMessages([]);
      } finally {
        setLoadingHistory(false);
      }
    },
    [conversations, setMessages, applySettings],
  );

  const newChat = useCallback(async () => {
    setConversationId(null);
    setMessages([]);
    setInput("");
    setRadiusMiles(5);
    setSettingsError(null);
  }, [setMessages]);

  const handleSubmit = useCallback(async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    if (emailDeliveryOn) {
      const validationError = validateSettings(settings);
      if (validationError) {
        setSettingsError(validationError);
        setView("settings");
        return;
      }
    }

    setSettingsError(null);
    const email = settings.email.trim();

    let cid = conversationId;
    if (!cid) {
      try {
        const conv = await create(
          text.slice(0, 80),
          text,
          radiusMiles,
          email || undefined,
        );
        cid = conv.id;
        setConversationId(cid);
      } catch (e) {
        console.error("Failed to create conversation", e);
      }
    } else if (email) {
      try {
        await updateEmail(cid, email);
      } catch (e) {
        console.warn("Email update skipped", e);
      }
    }

    sendMessage({ text });
    setInput("");
  }, [
    input,
    isLoading,
    conversationId,
    create,
    updateEmail,
    radiusMiles,
    sendMessage,
    settings,
    emailDeliveryOn,
  ]);

  const handleDelete = useCallback(
    async (id: string) => {
      await remove(id);
      if (conversationId === id) {
        await newChat();
      }
    },
    [conversationId, newChat, remove],
  );

  return (
    <div className={styles.app}>
      <Sidebar
        conversations={conversations}
        activeId={conversationId}
        loading={loadingConversations}
        view={view}
        onViewChange={setView}
        onNewChat={newChat}
        onSelect={loadConversation}
        onDelete={handleDelete}
      />

      <main className={styles.main}>
        {view === "settings" ? (
          <>
            <header className={styles.header}>
              <h1>Settings</h1>
            </header>
            <SettingsPanel onSave={applySettings} externalError={settingsError} />
          </>
        ) : (
          <>
            <header className={styles.header}>
              <h1>Consumer Market Analysis</h1>
              <div className={styles.headerActions}>
                {emailDeliveryOn && hasEmail && (
                  <EmailChip
                    email={settings.email.trim()}
                    onEdit={() => setView("settings")}
                    disabled={isLoading}
                  />
                )}
                <label className={styles.radius}>
                  Radius
                  <select
                    value={radiusMiles}
                    onChange={(e) => setRadiusMiles(Number(e.target.value))}
                    disabled={isLoading}
                  >
                    <option value={3}>3 mi</option>
                    <option value={5}>5 mi</option>
                    <option value={10}>10 mi</option>
                  </select>
                </label>
              </div>
            </header>

            <div className={styles.messages}>
              {loadingHistory && (
                <p className={styles.loadingHistory}>Loading conversation…</p>
              )}
              {!loadingHistory && messages.length === 0 && (
                <Welcome
                  onExample={(text) => setInput(text)}
                  emailDeliveryEnabled={emailDeliveryOn}
                  hasEmail={hasEmail}
                  onOpenSettings={() => setView("settings")}
                />
              )}
              {!loadingHistory && messages.length > 0 && (
                <MessageList messages={messages} isLoading={isLoading} />
              )}
            </div>

            <Composer
              input={input}
              isLoading={isLoading}
              onInputChange={setInput}
              onSubmit={handleSubmit}
              onStop={stop}
            />
          </>
        )}
      </main>
    </div>
  );
}
