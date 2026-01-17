/**
 * Type definitions for Underrail save file data.
 * Based on UFE JSON output structure and MS-NRBF format.
 */

// Raw NRBF record types
export interface NrbfRecord {
  class?: NrbfClass;
  class_id?: NrbfClass;
  array_id?: number;
  [key: string]: unknown;
}

export interface NrbfClass {
  name: string;
  id: number;
  ref_id?: number;
  members?: Record<string, unknown>;
}

export interface NrbfReference {
  reference: number;
}

export interface NrbfStringValue {
  obj_string_id: number;
  value: string;
}

// Parsed save data structure
export interface SaveData {
  raw: NrbfRecord[];
  refMap: Map<number, NrbfClass>;
  
  // Parsed data
  character: CharacterInfo;
  attributes: Attribute[];
  skills: Skill[];
  feats: Feat[];
  equipment: EquipmentSummary;
  inventory: InventoryItem[];
  currency: CurrencyInfo;
}

export interface CharacterInfo {
  name: string;
  level: number;
  gameVersion?: string;
  hasDLC: boolean;
}

export interface Attribute {
  name: string;
  base: number;
  effective: number;
  index: number;
}

export interface Skill {
  name: string;
  base: number;
  effective: number;
  category: SkillCategory;
  index: number;
}

export type SkillCategory = 
  | 'Offense' 
  | 'Defense' 
  | 'Subterfuge' 
  | 'Technology' 
  | 'Psi' 
  | 'Social';

export interface Feat {
  name: string;
  internal: string;
}

export interface EquipmentSummary {
  characterGear: EquipmentItem[];
  utilitySlots: EquipmentItem[];
  hotbar: EquipmentItem[];
}

export interface EquipmentItem {
  name: string;
  category: string;
  id?: number;
  
  // Basic stats
  value?: number;
  weight?: number;
  level?: number;
  
  // Runtime state
  currentDurability?: number;
  currentBattery?: number;
  maxBattery?: number;
  
  // Weapon stats
  weapon?: WeaponStats;
  
  // Armor stats
  armor?: ArmorStats;
  
  // For stackable items
  count?: number;
}

export interface WeaponStats {
  damageMin?: number;
  damageMax?: number;
  apCost?: number;
  critChance?: number;
  critDamage?: number;
  speed?: number;
  onHitEffects?: number;
}

export interface ArmorStats {
  damageResistances: DamageResistance[];
  evasionPenalty?: number;
  stealthCompatible?: boolean;
}

export interface DamageResistance {
  value: number;
  resistance: number;
  damageType?: number;
}

export interface InventoryItem {
  path: string;
  name: string;
  category: string;
  count: number;
  stacks?: number;
  stackCounts?: number[];
}

export interface CurrencyInfo {
  stygianCoins?: number;
  sgsCredits?: number;
}

// Skill names (base game - 23 skills)
export const SKILL_NAMES_BASE = [
  // Offense
  "Guns", "Heavy Guns", "Throwing", "Crossbows", "Melee",
  // Defense
  "Dodge", "Evasion",
  // Subterfuge
  "Stealth", "Hacking", "Lockpicking", "Pickpocketing", "Traps",
  // Technology
  "Mechanics", "Electronics", "Chemistry", "Biology", "Tailoring",
  // Psi
  "Thought Control", "Psychokinesis", "Metathermics",
  // Social
  "Persuasion", "Intimidation", "Mercantile",
] as const;

// Skill names with Expedition DLC (24 skills)
export const SKILL_NAMES_DLC = [
  // Offense
  "Guns", "Heavy Guns", "Throwing", "Crossbows", "Melee",
  // Defense
  "Dodge", "Evasion",
  // Subterfuge
  "Stealth", "Hacking", "Lockpicking", "Pickpocketing", "Traps",
  // Technology
  "Mechanics", "Electronics", "Chemistry", "Biology", "Tailoring",
  // Psi
  "Thought Control", "Psychokinesis", "Metathermics", "Temporal Manipulation",
  // Social
  "Persuasion", "Intimidation", "Mercantile",
] as const;

// Skill categories by index
export const SKILL_CATEGORIES: Record<number, SkillCategory> = {
  0: 'Offense', 1: 'Offense', 2: 'Offense', 3: 'Offense', 4: 'Offense',
  5: 'Defense', 6: 'Defense',
  7: 'Subterfuge', 8: 'Subterfuge', 9: 'Subterfuge', 10: 'Subterfuge', 11: 'Subterfuge',
  12: 'Technology', 13: 'Technology', 14: 'Technology', 15: 'Technology', 16: 'Technology',
  17: 'Psi', 18: 'Psi', 19: 'Psi', 20: 'Psi', // 20 is Temporal Manipulation in DLC
  21: 'Social', 22: 'Social', 23: 'Social',
};

// Attribute names
export const ATTRIBUTE_NAMES = [
  'Strength', 'Dexterity', 'Agility', 'Constitution', 
  'Perception', 'Will', 'Intelligence'
] as const;

// Feat display name mappings
export const FEAT_DISPLAY_NAMES: Record<string, string> = {
  'o': 'Opportunist',
  'pe': 'Psi Empathy',
  'heavypunch': 'Heavy Punch',
  'lightningpunches': 'Lightning Punches',
  'surestep': 'Sure Step',
  'quickpockets': 'Quick Pockets',
  'steadyaim': 'Steady Aim',
  'burstfire': 'Burst Fire',
  'fullautoburst': 'Full Auto Burst',
  'cheapshots': 'Cheap Shots',
  'evasivemaneuvers': 'Evasive Maneuvers',
  'freerunning': 'Free Running',
  'mentalsubversion': 'Mental Subversion',
  'nimble': 'Nimble',
  'quicktinkering': 'Quick Tinkering',
  'trapexpert': 'Trap Expert',
  'interloper': 'Interloper',
  'sprint': 'Sprint',
  'specialattacks': 'Specialization: Unarmed Combat',
};

// Item category mappings
export const ITEM_CATEGORIES: Record<string, string> = {
  'currency': 'Currency',
  'devices': 'Devices',
  'weapons': 'Weapons',
  'armor': 'Armor',
  'consumables': 'Consumables',
  'grenades': 'Grenades',
  'traps': 'Traps',
  'components': 'Components',
  'expendables': 'Expendables',
  'ammo': 'Ammo',
  'messages': 'Messages',
  'plot': 'Quest Items',
};

export function getSkillNames(count: number): readonly string[] {
  return count >= 24 ? SKILL_NAMES_DLC : SKILL_NAMES_BASE;
}

export function getFeatDisplayName(internal: string): string {
  return FEAT_DISPLAY_NAMES[internal] || 
    internal.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export function getItemCategory(rawCategory: string): string {
  return ITEM_CATEGORIES[rawCategory.toLowerCase()] || rawCategory;
}
