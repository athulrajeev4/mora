import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/lib/providers/query-provider";
import { MuiThemeProvider } from "@/lib/providers/mui-theme-provider";
import { Navbar } from "@/components/layout/navbar";
import { Toaster } from "sonner";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Mora - Voice AI Testing Platform",
  description: "End-to-end testing and evaluation platform for voice AI agents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={inter.className}>
        <MuiThemeProvider>
          <QueryProvider>
            <div className="min-h-screen bg-slate-50">
              <Navbar />
              <main className="mx-auto max-w-[1200px] px-6 py-10 sm:px-8 lg:px-10">
                {children}
              </main>
            </div>
            <Toaster position="top-right" richColors />
          </QueryProvider>
        </MuiThemeProvider>
      </body>
    </html>
  );
}
