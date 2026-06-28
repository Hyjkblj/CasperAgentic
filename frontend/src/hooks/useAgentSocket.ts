"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export interface AgentMessage {
  type: "cycle_start" | "decision" | "rebalance" | "oracle" | "error";
  timestamp: number;
  message: string;
  data?: Record<string, unknown>;
}

export function useAgentSocket() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_AGENT_WS || "ws://localhost:8080";
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as AgentMessage;
        setMessages((prev) => [...prev.slice(-100), msg]);
      } catch {
        // Ignore invalid messages
      }
    };

    return () => ws.close();
  }, []);

  const clearMessages = useCallback(() => setMessages([]), []);

  return { messages, connected, clearMessages };
}
