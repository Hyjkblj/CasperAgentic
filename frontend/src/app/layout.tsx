import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "YieldAgent — Casper DeFi Dashboard",
  description: "Autonomous yield optimization agent for Casper Network",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex">
        {/* Sidebar */}
        <aside className="w-64 border-r bg-muted/30 p-4 hidden md:block">
          <div className="font-bold text-lg mb-6">YieldAgent</div>
          <nav className="space-y-2">
            <a href="/" className="block px-3 py-2 rounded-md hover:bg-muted text-sm font-medium">
              Dashboard
            </a>
            <a href="/pools" className="block px-3 py-2 rounded-md hover:bg-muted text-sm text-muted-foreground">
              Pools
            </a>
            <a href="/oracle" className="block px-3 py-2 rounded-md hover:bg-muted text-sm text-muted-foreground">
              Oracle
            </a>
            <a href="/agent" className="block px-3 py-2 rounded-md hover:bg-muted text-sm text-muted-foreground">
              Agent
            </a>
          </nav>
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
