import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'MCPS Web',
  description: 'MCPS Web Application',
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-[var(--background)] text-[var(--foreground)] transition-colors duration-300">
        <main className="min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
