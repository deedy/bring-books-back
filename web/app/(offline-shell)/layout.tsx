import Footer from "@/components/ui/Footer";
import OfflineHeader from "@/components/ui/OfflineHeader";
import Providers from "@/components/Providers";

export default function OfflineShellLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Providers>
      <OfflineHeader />
      <main className="pt-12 min-h-screen">{children}</main>
      <Footer />
    </Providers>
  );
}
