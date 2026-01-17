/**
 * Parser module exports
 */

export * from './types';
export * from './gzip';
export * from './nrbf';
export * from './itemNames';

import { readFile, decompress, extractHeader, compress, isPacked } from './gzip';
import { parseNrbf, recordsToSaveData } from './nrbf';
import type { SaveData, Skill, Attribute } from './types';

/**
 * Parse a save file and return structured data.
 */
export async function parseSaveFile(file: File): Promise<{ saveData: SaveData; header: Uint8Array; rawData: Uint8Array }> {
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
  
  return { saveData, header, rawData: uncompressed };
}

/**
 * Parse raw binary data (for Node.js CLI use)
 */
export function parseRawData(data: Uint8Array): { saveData: SaveData; header: Uint8Array; rawData: Uint8Array } {
  const header = isPacked(data) ? extractHeader(data) : new Uint8Array(24);
  const uncompressed = decompress(data);
  const records = parseNrbf(uncompressed);
  const saveData = recordsToSaveData(records);
  return { saveData, header, rawData: uncompressed };
}

/**
 * Write a 32-bit signed integer to a Uint8Array at the given offset.
 */
function writeInt32(data: Uint8Array, offset: number, value: number): void {
  const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
  view.setInt32(offset, value, true); // little-endian
}

/**
 * Apply skill changes to raw binary data.
 * Returns a new Uint8Array with the changes applied.
 */
export function patchSkills(
  rawData: Uint8Array, 
  skills: Skill[], 
  changes: Map<number, { base?: number; effective?: number }>
): Uint8Array {
  // Create a copy to avoid mutating the original
  const patched = new Uint8Array(rawData);
  
  for (const [index, change] of changes) {
    const skill = skills[index];
    if (!skill) continue;
    
    if (change.base !== undefined && skill.baseOffset !== undefined) {
      writeInt32(patched, skill.baseOffset, change.base);
    }
    if (change.effective !== undefined && skill.effectiveOffset !== undefined) {
      writeInt32(patched, skill.effectiveOffset, change.effective);
    }
  }
  
  return patched;
}

/**
 * Apply attribute changes to raw binary data.
 * Returns a new Uint8Array with the changes applied.
 */
export function patchAttributes(
  rawData: Uint8Array, 
  attributes: Attribute[], 
  changes: Map<number, { base?: number; effective?: number }>
): Uint8Array {
  // Create a copy to avoid mutating the original
  const patched = new Uint8Array(rawData);
  
  for (const [index, change] of changes) {
    const attr = attributes[index];
    if (!attr) continue;
    
    if (change.base !== undefined && attr.baseOffset !== undefined) {
      writeInt32(patched, attr.baseOffset, change.base);
    }
    if (change.effective !== undefined && attr.effectiveOffset !== undefined) {
      writeInt32(patched, attr.effectiveOffset, change.effective);
    }
  }
  
  return patched;
}

/**
 * Create a save file from patched raw data.
 */
export function createSaveFile(rawData: Uint8Array, header: Uint8Array): Uint8Array {
  return compress(rawData, header);
}
