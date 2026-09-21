import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { ThemeProvider } from "@/components/theme-provider";
import { branding } from "@/lib/branding";

export const metadata: Metadata = {
  title: `${branding.name} — AI University Operating System`,
  description: branding.tagline,
  openGraph: {
    title: `${branding.name} — AI University Operating System`,
    description: branding.tagline,
    type: "website",
  },
  twitter: { card: "summary_large_image" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
