"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

interface LogEntry {
  type: string;
  timestamp: number;
  message: string;
}

interface AgentLogProps {
  messages: LogEntry[];
}

export function AgentLog({ messages }: AgentLogProps) {
  return (
    <ScrollArea className="h-80">
      <div className="space-y-2">
        {messages.map((msg, i) => (
          <LogItem key={i} entry={msg} />
        ))}
        {messages.length === 0 && (
          <p className="text-muted-foreground text-sm">
            Waiting for agent activity...
          </p>
        )}
      </div>
    </ScrollArea>
  );
}

function LogItem({ entry }: { entry: LogEntry }) {
  const getBadge = () => {
    switch (entry.type) {
      case "rebalance":
        return <Badge variant="default">REBALANCE</Badge>;
      case "hold":
        return <Badge variant="secondary">HOLD</Badge>;
      case "oracle":
        return <Badge variant="outline">ORACLE</Badge>;
      case "error":
        return <Badge variant="destructive">ERROR</Badge>;
      default:
        return <Badge variant="outline">INFO</Badge>;
    }
  };

  const time = new Date(entry.timestamp * 1000).toLocaleTimeString();

  return (
    <div className="flex items-start gap-2 text-sm">
      <span className="text-muted-foreground text-xs w-14 shrink-0">
        {time}
      </span>
      {getBadge()}
      <span className="text-muted-foreground font-mono text-xs">
        {entry.message}
      </span>
    </div>
  );
}
