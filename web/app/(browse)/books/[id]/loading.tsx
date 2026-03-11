export default function BookLoading() {
  return (
    <div className="pb-12 animate-pulse">
      {/* Hero banner skeleton */}
      <div className="relative w-full h-[200px] md:h-[350px] -mt-4 bg-white/[0.03]">
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(to bottom, rgba(10,10,11,0) 0%, rgba(10,10,11,0.15) 40%, rgba(10,10,11,0.7) 70%, rgba(10,10,11,1) 100%)",
          }}
        />
      </div>

      {/* Book header skeleton — matches real layout */}
      <div className="max-w-4xl mx-auto px-6 flex flex-col md:flex-row gap-10 -mt-32 relative z-10">
        {/* Cover skeleton */}
        <div className="w-64 flex-shrink-0 mx-auto md:mx-0">
          <div className="aspect-[2/3] rounded-lg bg-white/[0.06]" />
        </div>

        {/* Info skeleton */}
        <div className="flex-1 pt-4 md:pt-20 space-y-4">
          {/* Genre pills */}
          <div className="flex gap-2">
            <div className="h-5 w-20 rounded-full bg-white/[0.06]" />
            <div className="h-5 w-16 rounded-full bg-white/[0.06]" />
          </div>
          {/* Title */}
          <div className="h-8 w-3/4 rounded bg-white/[0.06]" />
          {/* Subtitle */}
          <div className="h-5 w-1/2 rounded bg-white/[0.06]" />
          {/* Author */}
          <div className="flex items-center gap-3 mt-2">
            <div className="w-10 h-10 rounded-full bg-white/[0.06]" />
            <div className="space-y-1.5">
              <div className="h-4 w-32 rounded bg-white/[0.06]" />
              <div className="h-3 w-20 rounded bg-white/[0.06]" />
            </div>
          </div>
          {/* Meta line */}
          <div className="h-3 w-48 rounded bg-white/[0.06] mt-2" />
          {/* Read button */}
          <div className="h-12 w-44 rounded-lg bg-white/[0.06] mt-4" />
        </div>
      </div>

      {/* Summary skeleton */}
      <div className="max-w-4xl mx-auto px-6 mt-12 space-y-3">
        <div className="h-4 w-full rounded bg-white/[0.04]" />
        <div className="h-4 w-full rounded bg-white/[0.04]" />
        <div className="h-4 w-5/6 rounded bg-white/[0.04]" />
        <div className="h-4 w-3/4 rounded bg-white/[0.04]" />
      </div>
    </div>
  );
}
