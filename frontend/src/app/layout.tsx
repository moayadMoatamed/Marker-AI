import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Marker AI — Logo Generation",
  description: "Conceptual logo generation system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
