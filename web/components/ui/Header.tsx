import Link from "next/link";

export default function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/80 backdrop-blur-md border-b border-white/10">
      <nav className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 text-lg font-semibold tracking-tight text-white">
          <img src="/logo.png" alt="" className="w-7 h-7 rounded" />
          Grand Old Books
        </Link>
      </nav>
    </header>
  );
}
