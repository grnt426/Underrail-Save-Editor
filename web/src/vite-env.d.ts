/// <reference types="vite/client" />

// Type declarations for pako
declare module 'pako' {
  export function inflate(data: Uint8Array, options?: { windowBits?: number }): Uint8Array;
  export function deflate(data: Uint8Array, options?: { level?: number; windowBits?: number }): Uint8Array;
}

// Type declarations for html-to-image
declare module 'html-to-image' {
  export function toPng(node: HTMLElement, options?: object): Promise<string>;
  export function toJpeg(node: HTMLElement, options?: object): Promise<string>;
  export function toBlob(node: HTMLElement, options?: object): Promise<Blob | null>;
  export function toCanvas(node: HTMLElement, options?: object): Promise<HTMLCanvasElement>;
}
