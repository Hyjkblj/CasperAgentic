"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface OracleEntry {
  type: string;
  value: number;
  confidence: number;
  source: string;
  age: number;
}

interface SourceRep {
  name: string;
  submissions: number;
  accuracy: number;
  score: number;
}

// Mock data
const MOCK_ORACLE: OracleEntry[] = [
  { type: "us_treasury_10y", value: 425, confidence: 95, source: "federal_res", age: 45 },
  { type: "t_bill_3m", value: 520, confidence: 88, source: "treasury_api", age: 120 },
  { type: "t_bill_6m", value: 505, confidence: 91, source: "treasury_api", age: 200 },
  { type: "corp_bond_aaa", value: 480, confidence: 82, source: "bond_index", age: 600 },
];

const MOCK_REPUTATION: SourceRep[] = [
  { name: "federal_res", submissions: 120, accuracy: 96.7, score: 9670 },
  { name: "treasury_api", submissions: 85, accuracy: 92.9, score: 9294 },
  { name: "bond_index", submissions: 50, accuracy: 88.0, score: 8800 },
];

// Simulated yield curve data
const YIELD_CURVE_DATA = [
  { maturity: "1M", yield: 5.25 },
  { maturity: "3M", yield: 5.20 },
  { maturity: "6M", yield: 5.05 },
  { maturity: "1Y", yield: 4.80 },
  { maturity: "2Y", yield: 4.50 },
  { maturity: "5Y", yield: 4.30 },
  { maturity: "10Y", yield: 4.25 },
  { maturity: "30Y", yield: 4.40 },
];

export default function OraclePage() {
  const [oracle, setOracle] = useState<OracleEntry[]>(MOCK_ORACLE);
  const [reputation, setReputation] = useState<SourceRep[]>(MOCK_REPUTATION);

  useEffect(() => {
    // In production: fetch from API
    setOracle(MOCK_ORACLE);
    setReputation(MOCK_REPUTATION);
  }, []);

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
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">RWA Oracle</h1>

      {/* Yield Curve */}
      <Card>
        <CardHeader>
          <CardTitle>Yield Curve</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={YIELD_CURVE_DATA}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="maturity" />
                <YAxis
                  label={{ value: "Yield %", angle: -90, position: "insideLeft" }}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="yield"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: "#3b82f6" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Data */}
        <Card>
          <CardHeader>
            <CardTitle>Current Oracle Data</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Age</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {oracle.map((row) => (
                  <TableRow key={row.type}>
                    <TableCell className="font-mono text-sm">
                      {row.type}
                    </TableCell>
                    <TableCell className="font-bold">
                      {(row.value / 100).toFixed(2)}%
                    </TableCell>
                    <TableCell>{getConfidenceBadge(row.confidence)}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatAge(row.age)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Source Reputation */}
        <Card>
          <CardHeader>
            <CardTitle>Source Reputation</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Source</TableHead>
                  <TableHead>Submissions</TableHead>
                  <TableHead>Accuracy</TableHead>
                  <TableHead>Score</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reputation.map((rep) => (
                  <TableRow key={rep.name}>
                    <TableCell className="font-mono text-sm">
                      {rep.name}
                    </TableCell>
                    <TableCell>{rep.submissions}</TableCell>
                    <TableCell>{rep.accuracy.toFixed(1)}%</TableCell>
                    <TableCell>
                      <Badge variant={rep.score >= 9000 ? "default" : "secondary"}>
                        {(rep.score / 100).toFixed(0)}%
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
