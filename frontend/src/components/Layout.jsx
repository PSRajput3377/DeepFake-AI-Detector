import Navbar from "./Navbar.jsx";
import Footer from "./Footer.jsx";
import AnimatedBackground from "./AnimatedBackground.jsx";

export default function Layout({ children }) {
  return (
    <div className="relative min-h-screen flex flex-col overflow-x-hidden">
      <AnimatedBackground />
      <Navbar />
      <main className="relative flex-1">{children}</main>
      <Footer />
    </div>
  );
}
