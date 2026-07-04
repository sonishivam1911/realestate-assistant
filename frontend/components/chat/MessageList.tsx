import type { UIMessage } from "ai";
import { ChatMessage } from "./ChatMessage";
import styles from "./MessageList.module.css";

type Props = {
  messages: UIMessage[];
  isLoading: boolean;
};

export function MessageList({ messages, isLoading }: Props) {
  return (
    <div className={styles.list}>
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}
      {isLoading && (
        <div className={styles.typing}>
          Fan-out: comps · market pulse · macro…
        </div>
      )}
    </div>
  );
}
