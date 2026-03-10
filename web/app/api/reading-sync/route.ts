import { auth } from "@clerk/nextjs/server";
import { NextResponse, type NextRequest } from "next/server";
import { getUserData, setUserData, type CloudUserData } from "@/lib/firestore";

export async function GET() {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const data = await getUserData(userId);
    return NextResponse.json(
      data ?? { progress: {}, languages: {}, updatedAt: "" }
    );
  } catch (e) {
    console.error("reading-sync GET error:", e);
    return NextResponse.json(
      { error: "Failed to fetch" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const body = await request.json();
    const { progress, languages, readerPrefs } = body as Pick<
      CloudUserData,
      "progress" | "languages" | "readerPrefs"
    >;

    if (!progress || typeof progress !== "object") {
      return NextResponse.json(
        { error: "Invalid body" },
        { status: 400 }
      );
    }

    await setUserData(userId, {
      progress,
      languages: languages ?? {},
      readerPrefs,
      updatedAt: new Date().toISOString(),
    });

    return NextResponse.json({ ok: true });
  } catch (e) {
    console.error("reading-sync POST error:", e);
    return NextResponse.json(
      { error: "Failed to save" },
      { status: 500 }
    );
  }
}
