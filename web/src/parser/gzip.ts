/**
 * Gzip compression/decompression for Underrail save files.
 * 
 * Save file structure:
 * - 24-byte header
 * - Gzip-compressed NRBF data
 */

import pako from 'pako';

// Header size for packed save files
const HEADER_SIZE = 24;

// Magic bytes for gzip
const GZIP_MAGIC = [0x1f, 0x8b];

/**
 * Check if data is a packed (gzip-compressed) save file.
 */
export function isPacked(data: Uint8Array): boolean {
  if (data.length < HEADER_SIZE + 2) {
    return false;
  }
  
  // Check for gzip magic bytes after header
  return data[HEADER_SIZE] === GZIP_MAGIC[0] && 
         data[HEADER_SIZE + 1] === GZIP_MAGIC[1];
}

/**
 * Extract header from packed save file.
 */
export function extractHeader(data: Uint8Array): Uint8Array {
  return data.slice(0, HEADER_SIZE);
}

/**
 * Decompress a packed save file.
 * Returns the uncompressed NRBF data.
 */
export function decompress(data: Uint8Array): Uint8Array {
  if (!isPacked(data)) {
    // Already unpacked, return as-is
    return data;
  }
  
  // Extract compressed portion (after header)
  const compressed = data.slice(HEADER_SIZE);
  
  try {
    // Decompress with pako
    return pako.inflate(compressed);
  } catch (error) {
    throw new Error(`Failed to decompress save file: ${error}`);
  }
}

/**
 * Compress data and prepend header to create a packed save file.
 */
export function compress(data: Uint8Array, header: Uint8Array): Uint8Array {
  // Compress with pako
  const compressed = pako.deflate(data, { 
    level: 9,
    windowBits: 15 + 16  // gzip format
  });
  
  // Combine header + compressed data
  const result = new Uint8Array(header.length + compressed.length);
  result.set(header, 0);
  result.set(compressed, header.length);
  
  return result;
}

/**
 * Read a file as an ArrayBuffer.
 */
export function readFile(file: File): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as ArrayBuffer);
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsArrayBuffer(file);
  });
}
