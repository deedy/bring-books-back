import Footer from "@/components/ui/Footer";
import OfflineHeader from "@/components/ui/OfflineHeader";

export default function OfflineShellLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <OfflineHeader />
      <main className="pt-12 min-h-screen">{children}</main>
      <Footer />
    </>
  );
}
