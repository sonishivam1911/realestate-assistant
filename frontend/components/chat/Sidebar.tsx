import type { Conversation } from "@/types/chat";
import styles from "./Sidebar.module.css";

export type SidebarView = "chat" | "settings";

type Props = {
  conversations: Conversation[];
  activeId: string | null;
  loading: boolean;
  view: SidebarView;
  onViewChange: (view: SidebarView) => void;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
};

export function Sidebar({
  conversations,
  activeId,
  loading,
  view,
  onViewChange,
  onNewChat,
  onSelect,
  onDelete,
}: Props) {
  return (
    <aside className={styles.sidebar}>
      <button
        type="button"
        className={styles.newChat}
        onClick={() => {
          onViewChange("chat");
          onNewChat();
        }}
      >
        + New CMA
      </button>

      <div className={styles.list}>
        {loading && <p className={styles.hint}>Loading…</p>}
        {!loading && conversations.length === 0 && (
          <p className={styles.hint}>No conversations yet</p>
        )}
        {conversations.map((c) => (
          <div
            key={c.id}
            className={`${styles.item} ${c.id === activeId && view === "chat" ? styles.active : ""}`}
          >
            <button
              type="button"
              className={styles.itemBtn}
              onClick={() => {
                onViewChange("chat");
                onSelect(c.id);
              }}
              title={c.subject_address ?? c.title ?? "Untitled"}
            >
              {c.title || c.subject_address || "Untitled CMA"}
            </button>
            <button
              type="button"
              className={styles.deleteBtn}
              onClick={(e) => {
                e.stopPropagation();
                onDelete(c.id);
              }}
              aria-label="Delete conversation"
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <nav className={styles.nav}>
        <button
          type="button"
          className={`${styles.navBtn} ${view === "settings" ? styles.navActive : ""}`}
          onClick={() => onViewChange("settings")}
        >
          <span className={styles.navIcon} aria-hidden>
            ⚙
          </span>
          Settings
        </button>
      </nav>

      <p className={styles.footer}>
        DeepSeek V4 Flash + Exa
        <br />
        LangGraph fan-out
      </p>
    </aside>
  );
}
