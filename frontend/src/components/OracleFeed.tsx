"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface OracleEntry {
  type: string;
  value: number;
  confidence: number;
  source: string;
  age: number;
}

interface OracleFeedProps {
  data: OracleEntry[];
}

export function OracleFeed({ data }: OracleFeedProps) {
  const formatAge = (seconds: number) => {
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 90) return <Badge variant="default">High</Badge>;
    if (confidence >= 70) return <Badge variant="secondary">Medium</Badge>;
    return <Badge variant="destructive">Low</Badge>;
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Data Type</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead>Source</TableHead>
          <TableHead>Age</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((row) => (
          <TableRow key={row.type}>
            <TableCell className="font-mono">{row.type}</TableCell>
            <TableCell className="font-bold">
              {(row.value / 100).toFixed(2)}%
            </TableCell>
            <TableCell>{getConfidenceBadge(row.confidence)}</TableCell>
            <TableCell className="text-muted-foreground">
              {row.source}
            </TableCell>
            <TableCell className="text-muted-foreground">
              {formatAge(row.age)}
            </TableCell>
          </TableRow>
        ))}
        {data.length === 0 && (
          <TableRow>
            <TableCell colSpan={5} className="text-center text-muted-foreground">
              No oracle data available
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
