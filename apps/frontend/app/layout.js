import "./public-shell.css";
import "./project-views.css";

export const metadata = {
  title: "Acadence — Start with the right report structure",
  description:
    "Explore a template-first approach to academic reports, with a guided AI Mentor workflow.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="acadence-app">
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}