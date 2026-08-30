/** Capture the current viewport as a PNG blob for task completion review. */

export async function captureViewportScreenshot(): Promise<Blob> {
  const html2canvas = (await import("html2canvas")).default;
  const canvas = await html2canvas(document.body, {
    useCORS: true,
    logging: false,
    scale: window.devicePixelRatio > 1 ? 1.5 : 1,
    windowWidth: document.documentElement.scrollWidth,
    windowHeight: document.documentElement.scrollHeight,
  });
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("Screenshot failed"))),
      "image/png",
      0.92
    );
  });
}
