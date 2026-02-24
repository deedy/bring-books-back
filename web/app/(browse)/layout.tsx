import Header from "@/components/ui/Header";
import Footer from "@/components/ui/Footer";

export default function BrowseLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Header />
      <main className="pt-16 min-h-screen">{children}</main>
      <Footer />
    </>
  );
}
