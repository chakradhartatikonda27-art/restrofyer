import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RestoSaaS — Enterprise Restaurant CRM & ERP",
  description: "Complete multi-tenant SaaS for restaurants, multi-branch operations, POS, KDS, inventory, and analytics.",
};

const FOUC_SCRIPT = `try{var m=document.querySelector('meta[name="color-scheme"]');if(m){m.content=localStorage.getItem("color-scheme")||"light dark";}}catch(e){}`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="color-scheme" content="light dark" suppressHydrationWarning />
        <script dangerouslySetInnerHTML={{ __html: FOUC_SCRIPT }} />
      </head>
      <body className="min-h-screen font-sans bg-canvas text-ink-2 antialiased">{children}</body>
    </html>
  );
}
