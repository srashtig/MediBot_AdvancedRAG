import "./globals.css";

export const metadata = {
  title: "MediBot",
  description: "MediAssist Health Network assistant"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

