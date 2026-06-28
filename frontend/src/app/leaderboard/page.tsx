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
import { Button } from "@/components/ui/button";
import { Trophy, Medal, Award, Users } from "lucide-react";

interface LeaderboardEntry {
  rank: number;
  address: string;
  name: string;
  reputation: number;
  winRate: number;
  totalRebalances: number;
  totalYield: number;
  followers: number;
  status: string;
}

// Mock data
const MOCK_LEADERBOARD: LeaderboardEntry[] = [
  {
    rank: 1,
    address: "01a1b2...c3d4",
    name: "YieldMax-v2",
    reputation: 9200,
    winRate: 8800,
    totalRebalances: 245,
    totalYield: 5200_000_000_000,
    followers: 12,
    status: "active",
  },
  {
    rank: 2,
    address: "01e5f6...g7h8",
    name: "ConservativeBot",
    reputation: 8500,
    winRate: 8200,
    totalRebalances: 180,
    totalYield: 3800_000_000_000,
    followers: 8,
    status: "active",
  },
  {
    rank: 3,
    address: "01i9j0...k1l2",
    name: "YieldOptimizer-v1",
    reputation: 6200,
    winRate: 7500,
    totalRebalances: 80,
    totalYield: 1250_000_000_000,
    followers: 3,
    status: "active",
  },
  {
    rank: 4,
    address: "01m3n4...o5p6",
    name: "AggroYield",
    reputation: 5800,
    winRate: 6800,
    totalRebalances: 150,
    totalYield: 2100_000_000_000,
    followers: 5,
    status: "active",
  },
  {
    rank: 5,
    address: "01q7r8...s9t0",
    name: "SafeHarbor",
    reputation: 5200,
    winRate: 7100,
    totalRebalances: 95,
    totalYield: 980_000_000_000,
    followers: 2,
    status: "active",
  },
  {
    rank: 6,
    address: "01u1v2...w3x4",
    name: "TestAgent",
    reputation: 4000,
    winRate: 5000,
    totalRebalances: 10,
    totalYield: 50_000_000_000,
    followers: 0,
    status: "inactive",
  },
];

export default function LeaderboardPage() {
  const [agents, setAgents] = useState<LeaderboardEntry[]>(MOCK_LEADERBOARD);

  useEffect(() => {
    // In production: fetch from AgentRegistry contract
    setAgents(MOCK_LEADERBOARD);
  }, []);

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Trophy className="h-5 w-5 text-yellow-500" />;
      case 2:
        return <Medal className="h-5 w-5 text-gray-400" />;
      case 3:
        return <Award className="h-5 w-5 text-amber-600" />;
      default:
        return <span className="text-muted-foreground w-5 text-center">{rank}</span>;
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Agent Leaderboard</h1>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Users className="h-4 w-4" />
          {agents.filter((a) => a.status === "active").length} active agents
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Top Agents by Reputation</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">Rank</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>Reputation</TableHead>
                <TableHead>Win Rate</TableHead>
                <TableHead>Rebalances</TableHead>
                <TableHead>Yield Generated</TableHead>
                <TableHead>Followers</TableHead>
                <TableHead className="w-24">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {agents.map((agent) => (
                <TableRow
                  key={agent.address}
                  className={agent.rank <= 3 ? "bg-muted/30" : ""}
                >
                  <TableCell>{getRankIcon(agent.rank)}</TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{agent.name}</div>
                      <div className="text-xs text-muted-foreground font-mono">
                        {agent.address}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={agent.reputation >= 8000 ? "default" : "secondary"}
                    >
                      {(agent.reputation / 100).toFixed(0)}%
                    </Badge>
                  </TableCell>
                  <TableCell>{(agent.winRate / 100).toFixed(1)}%</TableCell>
                  <TableCell>{agent.totalRebalances}</TableCell>
                  <TableCell>
                    {(agent.totalYield / 1e9).toFixed(0)} CSPR
                  </TableCell>
                  <TableCell>{agent.followers}</TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={agent.status !== "active"}
                    >
                      Follow
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
