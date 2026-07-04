import type { UIMessage } from "ai";
import ReactMarkdown from "react-markdown";
import styles from "./ChatMessage.module.css";

type Props = {
  message: UIMessage;
};

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <article className={`${styles.message} ${isUser ? styles.user : styles.assistant}`}>
      <div className={styles.role}>{isUser ? "You" : "CMA Assistant"}</div>
      <div className={styles.parts}>
        {message.parts.map((part, i) => {
          if (part.type === "text") {
            return isUser ? (
              <p key={`${message.id}-${i}`} className={styles.userText}>
                {part.text}
              </p>
            ) : (
              <div key={`${message.id}-${i}`} className={styles.markdown}>
                <ReactMarkdown>{part.text}</ReactMarkdown>
              </div>
            );
          }
          if (part.type === "reasoning") {
            return (
              <details key={`${message.id}-${i}`} className={styles.reasoning}>
                <summary>Research steps</summary>
                <pre>{part.text}</pre>
              </details>
            );
          }
          return null;
        })}
      </div>
    </article>
  );
}
