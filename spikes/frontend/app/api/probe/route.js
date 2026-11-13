export const dynamic = "force-dynamic";

export function GET() {
  const encoder = new TextEncoder();
  let timer;
  const body = new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode("event: phase\ndata: template\n\n"));
      timer = setTimeout(() => {
        controller.enqueue(encoder.encode("event: phase\ndata: complete\n\n"));
        controller.close();
      }, 200);
    },
    cancel() {
      clearTimeout(timer);
    }
  });
  return new Response(body, { headers: {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-store",
    "Set-Cookie": "acadence_probe=sample; Path=/; HttpOnly; Secure; SameSite=Lax"
  } });
}
