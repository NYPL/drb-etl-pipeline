export async function initMocks() {
  if (typeof window === "undefined") {
    const { server } = await import("./server");
    server.listen({
      onUnhandledRequest: "bypass",
    });
  } else if (typeof window !== "undefined") {
    const { worker } = await import("./browser");
    worker.start({
      onUnhandledRequest: "bypass",
    });
  }
}

export {};
