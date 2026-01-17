/**
 * Parser module exports
 */

export * from './types';
export * from './gzip';
export * from './nrbf';
export * from './itemNames';

import { readFile, decompress, extractHeader, compress, isPacked } from './gzip';
import { parseNrbf, recordsToSaveData } from './nrbf';
import type { SaveData } from './types';

/**
 * Parse a save file and return structured data.
 */
export async function parseSaveFile(file: File): Promise<{ saveData: SaveData; header: Uint8Array }> {
  // Read file
  const buffer = await readFile(file);
  const data = new Uint8Array(buffer);
  
  // Extract header (needed for re-saving)
  const header = isPacked(data) ? extractHeader(data) : new Uint8Array(24);
  
  // Decompress
  const uncompressed = decompress(data);
  
  // Parse NRBF
  const records = parseNrbf(uncompressed);
  
  // Convert to SaveData
  const saveData = recordsToSaveData(records);
  
  return { saveData, header };
}

/**
 * Serialize SaveData back to a save file.
 * Note: This is a placeholder - full implementation requires NRBF writer.
 */
export function serializeSaveFile(saveData: SaveData, header: Uint8Array): Uint8Array {
  // TODO: Implement NRBF writer
  // For now, this is a placeholder that would need the actual serialization logic
  throw new Error('Save file serialization not yet implemented');
}
