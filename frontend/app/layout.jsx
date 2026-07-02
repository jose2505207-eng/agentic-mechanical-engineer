import "./globals.css";

export const metadata = {
  title: "Agentic Mechanical Engineer",
  description: "Type one sentence. Get an engineering package.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
