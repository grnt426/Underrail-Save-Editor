#!/usr/bin/env npx ts-node
/**
 * Node.js CLI for Underrail Save Editor
 * Used for automated testing with Python.
 * 
 * Usage:
 *   npx ts-node cli.ts parse <input.dat> [--json]
 *   npx ts-node cli.ts patch <input.dat> <output.dat> --skill <index> <base> [<effective>]
 *   npx ts-node cli.ts patch <input.dat> <output.dat> --attr <index> <base> [<effective>]
 */

import * as fs from 'fs';
import { parseRawData, patchSkills, patchAttributes, createSaveFile } from './src/parser/index';

interface PatchOperation {
  type: 'skill' | 'attr';
  index: number;
  base: number;
  effective?: number;
}

function printUsage(): void {
  console.log(`
Underrail Save Editor CLI

Usage:
  npx ts-node cli.ts parse <input.dat> [--json]
    Parse a save file and print summary (or JSON with --json)

  npx ts-node cli.ts patch <input.dat> <output.dat> [options]
    Patch a save file with changes

Options for patch:
  --skill <index> <base> [effective]   Set skill value
  --attr <index> <base> [effective]    Set attribute value

Examples:
  npx ts-node cli.ts parse saves/global.dat
  npx ts-node cli.ts parse saves/global.dat --json > output.json
  npx ts-node cli.ts patch saves/global.dat patched.dat --skill 0 100
  npx ts-node cli.ts patch saves/global.dat patched.dat --skill 0 100 150 --attr 0 10
`);
}

function parseCommand(args: string[]): void {
  if (args.length < 1) {
    console.error('Error: Missing input file');
    printUsage();
    process.exit(1);
  }

  const inputPath = args[0];
  const jsonOutput = args.includes('--json');

  if (!fs.existsSync(inputPath)) {
    console.error(`Error: File not found: ${inputPath}`);
    process.exit(1);
  }

  const data = new Uint8Array(fs.readFileSync(inputPath));
  const { saveData } = parseRawData(data);

  if (jsonOutput) {
    // Output JSON-serializable version (without Map and raw records)
    const output = {
      character: saveData.character,
      attributes: saveData.attributes,
      skills: saveData.skills,
      feats: saveData.feats,
      equipment: saveData.equipment,
      inventory: saveData.inventory,
      currency: saveData.currency,
    };
    console.log(JSON.stringify(output, null, 2));
  } else {
    // Print summary
    console.log(`Character: ${saveData.character.name}`);
    console.log(`Level: ${saveData.character.level}`);
    console.log(`DLC: ${saveData.character.hasDLC ? 'Yes' : 'No'}`);
    console.log('');
    console.log('Attributes:');
    for (const attr of saveData.attributes) {
      const offsetInfo = attr.baseOffset !== undefined ? ` [offset: ${attr.baseOffset}]` : '';
      console.log(`  ${attr.name}: ${attr.base} (${attr.effective})${offsetInfo}`);
    }
    console.log('');
    console.log('Skills:');
    for (const skill of saveData.skills) {
      const offsetInfo = skill.baseOffset !== undefined ? ` [offset: ${skill.baseOffset}]` : '';
      console.log(`  ${skill.name}: ${skill.base} (${skill.effective})${offsetInfo}`);
    }
  }
}

function patchCommand(args: string[]): void {
  if (args.length < 2) {
    console.error('Error: Missing input or output file');
    printUsage();
    process.exit(1);
  }

  const inputPath = args[0];
  const outputPath = args[1];
  const patchArgs = args.slice(2);

  if (!fs.existsSync(inputPath)) {
    console.error(`Error: File not found: ${inputPath}`);
    process.exit(1);
  }

  // Parse patch operations
  const operations: PatchOperation[] = [];
  let i = 0;
  while (i < patchArgs.length) {
    const arg = patchArgs[i];
    if (arg === '--skill' || arg === '--attr') {
      const type = arg === '--skill' ? 'skill' : 'attr';
      const index = parseInt(patchArgs[i + 1], 10);
      const base = parseInt(patchArgs[i + 2], 10);
      let effective: number | undefined;
      
      // Check if next arg is another option or effective value
      if (patchArgs[i + 3] && !patchArgs[i + 3].startsWith('--')) {
        effective = parseInt(patchArgs[i + 3], 10);
        i += 4;
      } else {
        i += 3;
      }

      if (isNaN(index) || isNaN(base)) {
        console.error(`Error: Invalid ${type} parameters`);
        process.exit(1);
      }

      operations.push({ type, index, base, effective });
    } else {
      console.error(`Error: Unknown option: ${arg}`);
      printUsage();
      process.exit(1);
    }
  }

  if (operations.length === 0) {
    console.error('Error: No patch operations specified');
    printUsage();
    process.exit(1);
  }

  // Read and parse input file
  const data = new Uint8Array(fs.readFileSync(inputPath));
  const { saveData, header, rawData } = parseRawData(data);

  // Apply patches
  let patchedData = rawData;

  const skillChanges = new Map<number, { base?: number; effective?: number }>();
  const attrChanges = new Map<number, { base?: number; effective?: number }>();

  for (const op of operations) {
    if (op.type === 'skill') {
      skillChanges.set(op.index, { 
        base: op.base, 
        effective: op.effective ?? op.base  // Default effective to base if not specified
      });
    } else {
      attrChanges.set(op.index, { 
        base: op.base, 
        effective: op.effective ?? op.base 
      });
    }
  }

  if (skillChanges.size > 0) {
    patchedData = patchSkills(patchedData, saveData.skills, skillChanges);
  }
  if (attrChanges.size > 0) {
    patchedData = patchAttributes(patchedData, saveData.attributes, attrChanges);
  }

  // Create output file
  const outputData = createSaveFile(patchedData, header);
  fs.writeFileSync(outputPath, outputData);

  console.log(`Patched save written to: ${outputPath}`);
  console.log(`Applied ${operations.length} change(s)`);

  // Print verification
  for (const op of operations) {
    if (op.type === 'skill') {
      const skill = saveData.skills[op.index];
      console.log(`  Skill ${op.index} (${skill?.name}): ${skill?.base} -> ${op.base}`);
    } else {
      const attr = saveData.attributes[op.index];
      console.log(`  Attr ${op.index} (${attr?.name}): ${attr?.base} -> ${op.base}`);
    }
  }
}

// Main entry point
const args = process.argv.slice(2);

if (args.length === 0) {
  printUsage();
  process.exit(0);
}

const command = args[0];
const commandArgs = args.slice(1);

switch (command) {
  case 'parse':
    parseCommand(commandArgs);
    break;
  case 'patch':
    patchCommand(commandArgs);
    break;
  case 'help':
  case '--help':
  case '-h':
    printUsage();
    break;
  default:
    console.error(`Unknown command: ${command}`);
    printUsage();
    process.exit(1);
}
