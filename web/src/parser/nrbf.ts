/**
 * MS-NRBF (NET Remoting Binary Format) Parser
 * 
 * Based on: https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-nrbf/
 * 
 * This parser reads .NET BinaryFormatter serialized data and converts it
 * to a JavaScript object structure similar to UFE's JSON output.
 */

import type { 
  NrbfRecord, 
  NrbfClass, 
  SaveData, 
  CharacterInfo,
  Attribute,
  Skill,
  Feat,
  EquipmentSummary,
  EquipmentItem,
  InventoryItem,
  CurrencyInfo,
  WeaponStats,
  ArmorStats,
} from './types';

import {
  ATTRIBUTE_NAMES,
  getSkillNames,
  getFeatDisplayName,
  getItemCategory,
  SKILL_CATEGORIES,
} from './types';

import { getItemDisplayName } from './itemNames';

// Record type constants from MS-NRBF spec
const RecordType = {
  SerializedStreamHeader: 0,
  ClassWithId: 1,
  SystemClassWithMembers: 2,
  ClassWithMembers: 3,
  SystemClassWithMembersAndTypes: 4,
  ClassWithMembersAndTypes: 5,
  BinaryObjectString: 6,
  BinaryArray: 7,
  MemberPrimitiveTyped: 8,
  MemberReference: 9,
  ObjectNull: 10,
  MessageEnd: 11,
  BinaryLibrary: 12,
  ObjectNullMultiple256: 13,
  ObjectNullMultiple: 14,
  ArraySinglePrimitive: 15,
  ArraySingleObject: 16,
  ArraySingleString: 17,
} as const;

// Primitive type constants
const PrimitiveType = {
  Boolean: 1,
  Byte: 2,
  Char: 3,
  Decimal: 5,
  Double: 6,
  Int16: 7,
  Int32: 8,
  Int64: 9,
  SByte: 10,
  Single: 11,
  TimeSpan: 12,
  DateTime: 13,
  UInt16: 14,
  UInt32: 15,
  UInt64: 16,
  Null: 17,
  String: 18,
} as const;

// Binary type constants
const BinaryType = {
  Primitive: 0,
  String: 1,
  Object: 2,
  SystemClass: 3,
  Class: 4,
  ObjectArray: 5,
  StringArray: 6,
  PrimitiveArray: 7,
} as const;

/**
 * Value with byte offset tracking for binary patching
 */
export interface TrackedValue {
  value: number;
  offset: number;
}

/**
 * Binary reader helper class with offset tracking
 */
class BinaryReader {
  private view: DataView;
  private pos: number = 0;
  private textDecoder = new TextDecoder('utf-8');
  
  constructor(buffer: ArrayBuffer | Uint8Array) {
    if (buffer instanceof Uint8Array) {
      this.view = new DataView(buffer.buffer, buffer.byteOffset, buffer.byteLength);
    } else {
      this.view = new DataView(buffer);
    }
  }
  
  get position(): number {
    return this.pos;
  }
  
  get length(): number {
    return this.view.byteLength;
  }
  
  get remaining(): number {
    return this.length - this.pos;
  }
  
  readByte(): number {
    const value = this.view.getUint8(this.pos);
    this.pos += 1;
    return value;
  }
  
  readBytes(count: number): Uint8Array {
    const bytes = new Uint8Array(this.view.buffer, this.view.byteOffset + this.pos, count);
    this.pos += count;
    return bytes;
  }
  
  readInt16(): number {
    const value = this.view.getInt16(this.pos, true);
    this.pos += 2;
    return value;
  }
  
  readUInt16(): number {
    const value = this.view.getUint16(this.pos, true);
    this.pos += 2;
    return value;
  }
  
  readInt32(): number {
    const value = this.view.getInt32(this.pos, true);
    this.pos += 4;
    return value;
  }
  
  // Read Int32 with offset tracking
  readInt32Tracked(): TrackedValue {
    const offset = this.pos;
    const value = this.view.getInt32(this.pos, true);
    this.pos += 4;
    return { value, offset };
  }
  
  readUInt32(): number {
    const value = this.view.getUint32(this.pos, true);
    this.pos += 4;
    return value;
  }
  
  readInt64(): bigint {
    const low = this.view.getUint32(this.pos, true);
    const high = this.view.getInt32(this.pos + 4, true);
    this.pos += 8;
    return BigInt(high) * BigInt(0x100000000) + BigInt(low);
  }
  
  readUInt64(): bigint {
    const low = this.view.getUint32(this.pos, true);
    const high = this.view.getUint32(this.pos + 4, true);
    this.pos += 8;
    return BigInt(high) * BigInt(0x100000000) + BigInt(low);
  }
  
  readFloat(): number {
    const value = this.view.getFloat32(this.pos, true);
    this.pos += 4;
    return value;
  }
  
  readDouble(): number {
    const value = this.view.getFloat64(this.pos, true);
    this.pos += 8;
    return value;
  }
  
  readBoolean(): boolean {
    return this.readByte() !== 0;
  }
  
  // Read 7-bit encoded integer (used for string lengths)
  read7BitEncodedInt(): number {
    let result = 0;
    let shift = 0;
    let byte: number;
    
    do {
      byte = this.readByte();
      result |= (byte & 0x7f) << shift;
      shift += 7;
    } while (byte & 0x80);
    
    return result;
  }
  
  // Read length-prefixed string
  readString(): string {
    const length = this.read7BitEncodedInt();
    if (length === 0) return '';
    
    const bytes = this.readBytes(length);
    return this.textDecoder.decode(bytes);
  }
  
  // Peek at next byte without advancing
  peekByte(): number {
    return this.view.getUint8(this.pos);
  }
  
  skip(count: number): void {
    this.pos += count;
  }
}

/**
 * NRBF Parser class
 */
export class NrbfParser {
  private reader: BinaryReader;
  private objects: Map<number, unknown> = new Map();
  private classInfos: Map<number, ClassInfo> = new Map();
  private libraries: Map<number, string> = new Map();
  private records: NrbfRecord[] = [];
  
  constructor(data: Uint8Array) {
    this.reader = new BinaryReader(data);
  }
  
  /**
   * Parse the NRBF data and return records.
   */
  parse(): NrbfRecord[] {
    this.records = [];
    this.objects.clear();
    this.classInfos.clear();
    this.libraries.clear();
    
    while (this.reader.remaining > 0) {
      const recordType = this.reader.readByte();
      
      if (recordType === RecordType.MessageEnd) {
        break;
      }
      
      this.parseRecord(recordType);
    }
    
    return this.records;
  }
  
  private parseRecord(recordType: number): void {
    switch (recordType) {
      case RecordType.SerializedStreamHeader:
        this.parseSerializedStreamHeader();
        break;
      case RecordType.ClassWithId:
        this.parseClassWithId();
        break;
      case RecordType.ClassWithMembersAndTypes:
        this.parseClassWithMembersAndTypes();
        break;
      case RecordType.SystemClassWithMembersAndTypes:
        this.parseSystemClassWithMembersAndTypes();
        break;
      case RecordType.ClassWithMembers:
        this.parseClassWithMembers();
        break;
      case RecordType.SystemClassWithMembers:
        this.parseSystemClassWithMembers();
        break;
      case RecordType.BinaryObjectString:
        this.parseBinaryObjectString();
        break;
      case RecordType.BinaryArray:
        this.parseBinaryArray();
        break;
      case RecordType.MemberReference:
        this.parseMemberReference();
        break;
      case RecordType.BinaryLibrary:
        this.parseBinaryLibrary();
        break;
      case RecordType.ObjectNull:
        // Null object, nothing to read
        break;
      case RecordType.ObjectNullMultiple256:
        this.reader.readByte(); // count
        break;
      case RecordType.ObjectNullMultiple:
        this.reader.readInt32(); // count
        break;
      case RecordType.ArraySinglePrimitive:
        this.parseArraySinglePrimitive();
        break;
      case RecordType.ArraySingleObject:
        this.parseArraySingleObject();
        break;
      case RecordType.ArraySingleString:
        this.parseArraySingleString();
        break;
      case RecordType.MemberPrimitiveTyped:
        this.parseMemberPrimitiveTyped();
        break;
      default:
        throw new Error(`Unknown record type: ${recordType} at position ${this.reader.position - 1}`);
    }
  }
  
  private parseSerializedStreamHeader(): void {
    const rootId = this.reader.readInt32();
    const headerId = this.reader.readInt32();
    const majorVersion = this.reader.readInt32();
    const minorVersion = this.reader.readInt32();
    
    // Store as metadata
    this.objects.set(0, { rootId, headerId, majorVersion, minorVersion });
  }
  
  private parseBinaryLibrary(): void {
    const libraryId = this.reader.readInt32();
    const libraryName = this.reader.readString();
    this.libraries.set(libraryId, libraryName);
  }
  
  private parseBinaryObjectString(): void {
    const objectId = this.reader.readInt32();
    const value = this.reader.readString();
    this.objects.set(objectId, { value, obj_string_id: objectId });
  }
  
  private parseClassWithMembersAndTypes(): void {
    const classInfo = this.readClassInfo();
    const memberTypeInfo = this.readMemberTypeInfo(classInfo.memberCount);
    const libraryId = this.reader.readInt32();
    
    classInfo.memberTypes = memberTypeInfo;
    classInfo.libraryId = libraryId;
    this.classInfos.set(classInfo.objectId, classInfo);
    
    const members = this.readMembers(classInfo);
    const record = this.createClassRecord(classInfo, members);
    this.records.push(record);
    this.objects.set(classInfo.objectId, record);
  }
  
  private parseSystemClassWithMembersAndTypes(): void {
    const classInfo = this.readClassInfo();
    const memberTypeInfo = this.readMemberTypeInfo(classInfo.memberCount);
    
    classInfo.memberTypes = memberTypeInfo;
    classInfo.isSystem = true;
    this.classInfos.set(classInfo.objectId, classInfo);
    
    const members = this.readMembers(classInfo);
    const record = this.createClassRecord(classInfo, members);
    this.records.push(record);
    this.objects.set(classInfo.objectId, record);
  }
  
  private parseClassWithMembers(): void {
    const classInfo = this.readClassInfo();
    const libraryId = this.reader.readInt32();
    
    classInfo.libraryId = libraryId;
    this.classInfos.set(classInfo.objectId, classInfo);
    
    // Need to infer types from a previous class with same name
    // For now, skip member reading
    const record = this.createClassRecord(classInfo, {});
    this.records.push(record);
    this.objects.set(classInfo.objectId, record);
  }
  
  private parseSystemClassWithMembers(): void {
    const classInfo = this.readClassInfo();
    classInfo.isSystem = true;
    this.classInfos.set(classInfo.objectId, classInfo);
    
    const record = this.createClassRecord(classInfo, {});
    this.records.push(record);
    this.objects.set(classInfo.objectId, record);
  }
  
  private parseClassWithId(): void {
    const objectId = this.reader.readInt32();
    const metadataId = this.reader.readInt32();
    
    const refClassInfo = this.classInfos.get(metadataId);
    if (!refClassInfo) {
      throw new Error(`ClassWithId references unknown class: ${metadataId}`);
    }
    
    const classInfo: ClassInfo = {
      ...refClassInfo,
      objectId,
    };
    this.classInfos.set(objectId, classInfo);
    
    const members = this.readMembers(classInfo);
    const record = this.createClassRecord(classInfo, members);
    this.records.push(record);
    this.objects.set(objectId, record);
  }
  
  private readClassInfo(): ClassInfo {
    const objectId = this.reader.readInt32();
    const name = this.reader.readString();
    const memberCount = this.reader.readInt32();
    
    const memberNames: string[] = [];
    for (let i = 0; i < memberCount; i++) {
      memberNames.push(this.reader.readString());
    }
    
    return {
      objectId,
      name,
      memberCount,
      memberNames,
      memberTypes: [],
      isSystem: false,
    };
  }
  
  private readMemberTypeInfo(memberCount: number): MemberTypeInfo[] {
    const binaryTypes: number[] = [];
    for (let i = 0; i < memberCount; i++) {
      binaryTypes.push(this.reader.readByte());
    }
    
    const additionalInfos: (number | string | null)[] = [];
    for (let i = 0; i < memberCount; i++) {
      additionalInfos.push(this.readAdditionalTypeInfo(binaryTypes[i]));
    }
    
    return binaryTypes.map((bt, i) => ({
      binaryType: bt,
      additionalInfo: additionalInfos[i],
    }));
  }
  
  private readAdditionalTypeInfo(binaryType: number): number | string | null {
    switch (binaryType) {
      case BinaryType.Primitive:
      case BinaryType.PrimitiveArray:
        return this.reader.readByte(); // PrimitiveTypeEnum
      case BinaryType.SystemClass:
        return this.reader.readString(); // Class name
      case BinaryType.Class:
        const className = this.reader.readString();
        const libraryId = this.reader.readInt32();
        return className; // Return class name, ignore library for now
      default:
        return null;
    }
  }
  
  private readMembers(classInfo: ClassInfo): Record<string, unknown> {
    const members: Record<string, unknown> = {};
    
    // Check if this class has S4:V or S4:MV members (stat value containers)
    const hasStatMembers = classInfo.memberNames.some(n => n === 'S4:V' || n === 'S4:MV');
    
    for (let i = 0; i < classInfo.memberCount; i++) {
      const memberName = classInfo.memberNames[i];
      const typeInfo = classInfo.memberTypes?.[i];
      
      // Track offsets for S4:V and S4:MV members
      const trackOffset = hasStatMembers && (memberName === 'S4:V' || memberName === 'S4:MV');
      
      if (typeInfo) {
        members[memberName] = this.readMemberValue(typeInfo, trackOffset);
      } else {
        // Without type info, try to read inline record
        members[memberName] = this.readInlineValue();
      }
    }
    
    return members;
  }
  
  private readMemberValue(typeInfo: MemberTypeInfo, trackOffsets: boolean = false): unknown {
    switch (typeInfo.binaryType) {
      case BinaryType.Primitive:
        return this.readPrimitive(typeInfo.additionalInfo as number, trackOffsets);
      case BinaryType.String:
        return this.readInlineValue();
      case BinaryType.Object:
      case BinaryType.SystemClass:
      case BinaryType.Class:
        return this.readInlineValue();
      case BinaryType.ObjectArray:
      case BinaryType.StringArray:
      case BinaryType.PrimitiveArray:
        return this.readInlineValue();
      default:
        return null;
    }
  }
  
  private readInlineValue(): unknown {
    const recordType = this.reader.readByte();
    
    switch (recordType) {
      case RecordType.MemberReference: {
        const idRef = this.reader.readInt32();
        return { reference: idRef };
      }
      case RecordType.ObjectNull:
        return null;
      case RecordType.BinaryObjectString: {
        const objectId = this.reader.readInt32();
        const value = this.reader.readString();
        this.objects.set(objectId, { value, obj_string_id: objectId });
        return { value, obj_string_id: objectId };
      }
      case RecordType.MemberPrimitiveTyped: {
        const primitiveType = this.reader.readByte();
        return this.readPrimitive(primitiveType);
      }
      case RecordType.ClassWithMembersAndTypes:
      case RecordType.SystemClassWithMembersAndTypes:
      case RecordType.ClassWithMembers:
      case RecordType.SystemClassWithMembers:
      case RecordType.ClassWithId:
      case RecordType.BinaryArray:
      case RecordType.ArraySinglePrimitive:
      case RecordType.ArraySingleObject:
      case RecordType.ArraySingleString: {
        // Parse the nested record and return reference to it
        this.parseRecord(recordType);
        const lastRecord = this.records[this.records.length - 1];
        const cls = lastRecord?.class || lastRecord?.class_id;
        if (cls?.id) {
          return { class_id: cls };
        }
        return lastRecord;
      }
      case RecordType.ObjectNullMultiple256: {
        this.reader.readByte();
        return null;
      }
      case RecordType.ObjectNullMultiple: {
        this.reader.readInt32();
        return null;
      }
      default:
        throw new Error(`Unexpected record type in member value: ${recordType}`);
    }
  }
  
  private readPrimitive(primitiveType: number, trackOffset: boolean = false): unknown {
    switch (primitiveType) {
      case PrimitiveType.Boolean:
        return this.reader.readBoolean();
      case PrimitiveType.Byte:
        return this.reader.readByte();
      case PrimitiveType.SByte:
        return this.reader.readByte() - 128;
      case PrimitiveType.Char:
        return String.fromCharCode(this.reader.readUInt16());
      case PrimitiveType.Int16:
        return this.reader.readInt16();
      case PrimitiveType.UInt16:
        return this.reader.readUInt16();
      case PrimitiveType.Int32:
        if (trackOffset) {
          return this.reader.readInt32Tracked();
        }
        return this.reader.readInt32();
      case PrimitiveType.UInt32:
        return this.reader.readUInt32();
      case PrimitiveType.Int64:
        return Number(this.reader.readInt64());
      case PrimitiveType.UInt64:
        return Number(this.reader.readUInt64());
      case PrimitiveType.Single:
        return this.reader.readFloat();
      case PrimitiveType.Double:
        return this.reader.readDouble();
      case PrimitiveType.String:
        return this.reader.readString();
      case PrimitiveType.DateTime:
        return Number(this.reader.readInt64()); // Ticks
      case PrimitiveType.TimeSpan:
        return Number(this.reader.readInt64()); // Ticks
      case PrimitiveType.Decimal:
        // Decimal is complex, read as string for now
        return this.reader.readString();
      default:
        throw new Error(`Unknown primitive type: ${primitiveType}`);
    }
  }
  
  private parseMemberReference(): void {
    const idRef = this.reader.readInt32();
    // Just a reference, handled inline
  }
  
  private parseMemberPrimitiveTyped(): void {
    const primitiveType = this.reader.readByte();
    this.readPrimitive(primitiveType);
  }
  
  private parseBinaryArray(): void {
    const objectId = this.reader.readInt32();
    const arrayType = this.reader.readByte();
    const rank = this.reader.readInt32();
    
    const lengths: number[] = [];
    for (let i = 0; i < rank; i++) {
      lengths.push(this.reader.readInt32());
    }
    
    // Skip lower bounds for non-zero-based arrays
    if (arrayType === 3 || arrayType === 4 || arrayType === 5) {
      for (let i = 0; i < rank; i++) {
        this.reader.readInt32();
      }
    }
    
    const typeInfo = this.reader.readByte();
    const additionalInfo = this.readAdditionalTypeInfo(typeInfo);
    
    const totalLength = lengths.reduce((a, b) => a * b, 1);
    const elements: unknown[] = [];
    
    for (let i = 0; i < totalLength; i++) {
      if (typeInfo === BinaryType.Primitive) {
        elements.push(this.readPrimitive(additionalInfo as number));
      } else {
        elements.push(this.readInlineValue());
      }
    }
    
    const record: NrbfRecord = { array_id: objectId, elements };
    this.records.push(record);
    this.objects.set(objectId, record);
  }
  
  private parseArraySinglePrimitive(): void {
    const objectId = this.reader.readInt32();
    const length = this.reader.readInt32();
    const primitiveType = this.reader.readByte();
    
    const elements: unknown[] = [];
    for (let i = 0; i < length; i++) {
      elements.push(this.readPrimitive(primitiveType));
    }
    
    const record: NrbfRecord = { array_id: objectId, elements };
    this.records.push(record);
    this.objects.set(objectId, record);
  }
  
  private parseArraySingleObject(): void {
    const objectId = this.reader.readInt32();
    const length = this.reader.readInt32();
    
    const elements: unknown[] = [];
    for (let i = 0; i < length; i++) {
      elements.push(this.readInlineValue());
    }
    
    const record: NrbfRecord = { array_id: objectId, elements };
    this.records.push(record);
    this.objects.set(objectId, record);
  }
  
  private parseArraySingleString(): void {
    const objectId = this.reader.readInt32();
    const length = this.reader.readInt32();
    
    const elements: unknown[] = [];
    for (let i = 0; i < length; i++) {
      elements.push(this.readInlineValue());
    }
    
    const record: NrbfRecord = { array_id: objectId, elements };
    this.records.push(record);
    this.objects.set(objectId, record);
  }
  
  private createClassRecord(classInfo: ClassInfo, members: Record<string, unknown>): NrbfRecord {
    return {
      class: {
        name: classInfo.name,
        id: classInfo.objectId,
        members,
      },
    };
  }
}

// Helper types
interface ClassInfo {
  objectId: number;
  name: string;
  memberCount: number;
  memberNames: string[];
  memberTypes?: MemberTypeInfo[];
  libraryId?: number;
  isSystem?: boolean;
}

interface MemberTypeInfo {
  binaryType: number;
  additionalInfo: number | string | null;
}

/**
 * Parse NRBF data into a SaveData structure.
 */
export function parseNrbf(data: Uint8Array): NrbfRecord[] {
  const parser = new NrbfParser(data);
  return parser.parse();
}

/**
 * Build a reference map from parsed records.
 */
export function buildRefMap(records: NrbfRecord[]): Map<number, NrbfClass> {
  const refMap = new Map<number, NrbfClass>();
  
  for (const record of records) {
    const cls = record.class || record.class_id;
    if (cls?.id !== undefined) {
      refMap.set(cls.id, cls);
    }
    if (record.array_id !== undefined) {
      refMap.set(record.array_id, record as unknown as NrbfClass);
    }
  }
  
  return refMap;
}

/**
 * Get a member value from an object, resolving references.
 */
export function getMember(
  obj: NrbfClass | undefined, 
  key: string, 
  refMap: Map<number, NrbfClass>
): unknown {
  if (!obj?.members) return undefined;
  
  const value = obj.members[key];
  
  // Handle reference
  if (value && typeof value === 'object' && 'reference' in value) {
    return refMap.get((value as { reference: number }).reference);
  }
  
  // Handle string value
  if (value && typeof value === 'object' && 'value' in value && !('offset' in value)) {
    return (value as { value: unknown }).value;
  }
  
  // Handle TrackedValue (Int32 with offset)
  if (value && typeof value === 'object' && 'value' in value && 'offset' in value) {
    return (value as TrackedValue).value;
  }
  
  // Handle nested class
  if (value && typeof value === 'object' && 'class_id' in value) {
    const classId = (value as { class_id: NrbfClass }).class_id;
    if (classId.members) {
      // Check for enum value
      if ('value__' in classId.members) {
        return classId.members['value__'];
      }
    }
    return classId;
  }
  
  return value;
}

/**
 * Get a member value without unwrapping TrackedValue - used for offset extraction.
 */
export function getMemberRaw(
  obj: NrbfClass | undefined, 
  key: string, 
  refMap: Map<number, NrbfClass>
): unknown {
  if (!obj?.members) return undefined;
  
  // Direct member access - this is where S4:V/S4:MV will be
  const value = obj.members[key];
  
  // If the value is already a TrackedValue or number, return it directly
  if (value !== undefined) {
    // Check if it's a TrackedValue
    if (value && typeof value === 'object' && 'value' in value && 'offset' in value) {
      return value;
    }
    // Check if it's a plain number
    if (typeof value === 'number') {
      return value;
    }
  }
  
  // Handle reference
  if (value && typeof value === 'object' && 'reference' in value) {
    const resolved = refMap.get((value as { reference: number }).reference);
    // If resolved object has members, return the raw value from there
    if (resolved?.members && key in resolved.members) {
      return resolved.members[key];
    }
    return resolved;
  }
  
  // Handle nested class - look for the value inside
  if (value && typeof value === 'object' && 'class_id' in value) {
    const classId = (value as { class_id: NrbfClass }).class_id;
    if (classId.members && key in classId.members) {
      return classId.members[key];
    }
    return classId;
  }
  
  return value;
}

/**
 * Extract value and offset from a TrackedValue or plain number.
 */
function extractTrackedValue(raw: unknown, defaultValue: number): { value: number; offset?: number } {
  if (raw && typeof raw === 'object' && 'value' in raw && 'offset' in raw) {
    const tracked = raw as TrackedValue;
    return { value: tracked.value, offset: tracked.offset };
  }
  if (typeof raw === 'number') {
    return { value: raw };
  }
  return { value: defaultValue };
}

/**
 * Convert parsed NRBF records to SaveData structure.
 */
export function recordsToSaveData(records: NrbfRecord[]): SaveData {
  const refMap = buildRefMap(records);
  
  // Find root TG object
  const root = records.find(r => r.class?.name === 'TG')?.class;
  if (!root) {
    throw new Error('Could not find root TG object');
  }
  
  // Find player (P2)
  const playerRef = getMember(root, 'TG:PC', refMap) as NrbfClass | undefined;
  if (!playerRef) {
    throw new Error('Could not find player object');
  }
  
  // Extract character info
  const character = extractCharacterInfo(playerRef, refMap);
  
  // Extract attributes
  const attributes = extractAttributes(playerRef, refMap);
  
  // Extract skills
  const skills = extractSkills(playerRef, refMap, character.hasDLC);
  
  // Extract feats
  const feats = extractFeats(playerRef, refMap);
  
  // Extract equipment
  const equipment = extractEquipment(records, refMap);
  
  // Extract inventory
  const inventory = extractInventory(records, refMap);
  
  // Extract currency
  const currency = extractCurrency(inventory);
  
  return {
    raw: records,
    refMap,
    character,
    attributes,
    skills,
    feats,
    equipment,
    inventory,
    currency,
  };
}

function extractCharacterInfo(player: NrbfClass, refMap: Map<number, NrbfClass>): CharacterInfo {
  const name = getMember(player, 'C1:N', refMap) as string || 'Unknown';
  const level = getMember(player, 'C1:L', refMap) as number || 1;
  
  // Check for DLC by looking at skill count
  const skillsContainer = getMember(player, 'C1:S', refMap) as NrbfClass | undefined;
  const skillCount = skillsContainer ? getMember(skillsContainer, 'S3:S:Count', refMap) as number || 0 : 0;
  const hasDLC = skillCount >= 24;
  
  return { name, level, hasDLC };
}

function extractAttributes(player: NrbfClass, refMap: Map<number, NrbfClass>): Attribute[] {
  const attrsContainer = getMember(player, 'C1:BA', refMap) as NrbfClass | undefined;
  if (!attrsContainer) return [];
  
  const count = getMember(attrsContainer, 'BA3:BA:Count', refMap) as number || 0;
  const attributes: Attribute[] = [];
  
  for (let i = 0; i < count; i++) {
    const attr = getMember(attrsContainer, `BA3:BA:${i}`, refMap) as NrbfClass | undefined;
    if (attr) {
      const name = getMember(attr, 'BA2:N', refMap) as string || ATTRIBUTE_NAMES[i] || `Attr ${i}`;
      const baseRaw = getMemberRaw(attr, 'S4:V', refMap);
      const effectiveRaw = getMemberRaw(attr, 'S4:MV', refMap);
      
      // Extract value and offset from TrackedValue or plain number
      const { value: base, offset: baseOffset } = extractTrackedValue(baseRaw, 0);
      const { value: effective, offset: effectiveOffset } = extractTrackedValue(effectiveRaw, base);
      
      attributes.push({ name, base, effective, index: i, baseOffset, effectiveOffset });
    }
  }
  
  return attributes;
}

function extractSkills(player: NrbfClass, refMap: Map<number, NrbfClass>, hasDLC: boolean): Skill[] {
  const skillsContainer = getMember(player, 'C1:S', refMap) as NrbfClass | undefined;
  if (!skillsContainer) return [];
  
  const count = getMember(skillsContainer, 'S3:S:Count', refMap) as number || 0;
  const skillNames = getSkillNames(count);
  const skills: Skill[] = [];
  
  for (let i = 0; i < count; i++) {
    const skill = getMember(skillsContainer, `S3:S:${i}`, refMap) as NrbfClass | undefined;
    if (skill) {
      const baseRaw = getMemberRaw(skill, 'S4:V', refMap);
      const effectiveRaw = getMemberRaw(skill, 'S4:MV', refMap);
      
      // Extract value and offset from TrackedValue or plain number
      const { value: base, offset: baseOffset } = extractTrackedValue(baseRaw, 0);
      const { value: effective, offset: effectiveOffset } = extractTrackedValue(effectiveRaw, base);
      const category = SKILL_CATEGORIES[i] || 'Other';
      
      skills.push({
        name: skillNames[i] || `Skill ${i}`,
        base,
        effective,
        category,
        index: i,
        baseOffset,
        effectiveOffset,
      });
    }
  }
  
  return skills;
}

function extractFeats(player: NrbfClass, refMap: Map<number, NrbfClass>): Feat[] {
  const featsContainer = getMember(player, 'C1:F', refMap) as NrbfClass | undefined;
  if (!featsContainer) return [];
  
  const count = getMember(featsContainer, 'F:F:Count', refMap) as number || 0;
  const feats: Feat[] = [];
  
  for (let i = 0; i < count; i++) {
    const feat = getMember(featsContainer, `F:F:${i}`, refMap) as NrbfClass | undefined;
    if (feat) {
      const internal = getMember(feat, 'FR:FTN', refMap) as string || '';
      const name = getFeatDisplayName(internal);
      feats.push({ name, internal });
    }
  }
  
  return feats;
}

function extractEquipment(records: NrbfRecord[], refMap: Map<number, NrbfClass>): EquipmentSummary {
  const characterGear: EquipmentItem[] = [];
  const utilitySlots: EquipmentItem[] = [];
  const hotbar: EquipmentItem[] = [];
  
  // Find items with I:N (named items)
  for (const record of records) {
    const cls = record.class;
    if (!cls?.members) continue;
    
    const nameField = cls.members['I:N'];
    if (!nameField || typeof nameField !== 'object') continue;
    
    const name = (nameField as { value?: string }).value;
    if (!name || name.length < 3) continue;
    if (name.toLowerCase().startsWith('this ') || name.toLowerCase().startsWith('these ')) continue;
    
    const item = parseEquipmentItem(cls, refMap);
    if (item) {
      characterGear.push(item);
    }
  }
  
  return { characterGear, utilitySlots, hotbar };
}

function parseEquipmentItem(cls: NrbfClass, refMap: Map<number, NrbfClass>): EquipmentItem | null {
  const members = cls.members || {};
  
  const nameField = members['I:N'];
  const name = nameField && typeof nameField === 'object' ? (nameField as { value?: string }).value : undefined;
  if (!name) return null;
  
  const nameLower = name.toLowerCase();
  
  // Classify category
  let category = 'Other';
  if (members['WI:AP'] !== undefined) {
    category = 'Weapons';
  } else if (nameLower.includes('glove')) {
    category = 'Gloves';
  } else if (nameLower.includes('boot') || nameLower.includes('tabi') || nameLower.includes('shoe')) {
    category = 'Boots';
  } else if (nameLower.includes('balaclava') || nameLower.includes('helmet') || nameLower.includes('goggles') || nameLower.includes('mask') || nameLower.includes('hood')) {
    category = 'Head';
  } else if (nameLower.includes('shield') || nameLower.includes('emitter')) {
    category = 'Shield';
  } else if (nameLower.includes('overcoat') || nameLower.includes('armor') || nameLower.includes('vest') || nameLower.includes('jacket')) {
    category = 'Armor';
  }
  
  if (category === 'Other') return null;
  
  const item: EquipmentItem = {
    name,
    category,
    id: cls.id,
    value: members['I:CV'] as number | undefined,
    weight: members['I:W'] as number | undefined,
    level: members['I:L'] as number | undefined,
    maxBattery: members['I:MB'] as number | undefined,
  };
  
  // Weapon stats
  if (members['WI:AP'] !== undefined) {
    const weapon: WeaponStats = {
      apCost: members['WI:AP'] as number,
      critChance: members['WI:CSC'] as number,
      critDamage: members['WI:CDB'] as number,
      speed: members['WI:S'] as number,
    };
    
    // Damage range
    const damageField = members['WI:D:0'];
    if (damageField && typeof damageField === 'object') {
      const dmgClass = (damageField as { class_id?: NrbfClass }).class_id;
      if (dmgClass?.members) {
        weapon.damageMin = dmgClass.members['L'] as number;
        weapon.damageMax = dmgClass.members['U'] as number;
      }
    }
    
    item.weapon = weapon;
  }
  
  // Armor stats
  const drCount = members['AI1:DR:Count'] as number | undefined;
  if (drCount !== undefined) {
    const armor: ArmorStats = {
      damageResistances: [],
      evasionPenalty: members['AI1:E'] as number,
      stealthCompatible: members['ASI:SC'] as boolean,
    };
    
    for (let i = 0; i < drCount; i++) {
      const drField = members[`AI1:DR:${i}`];
      if (drField && typeof drField === 'object') {
        const drClass = (drField as { class_id?: NrbfClass }).class_id;
        if (drClass?.members) {
          armor.damageResistances.push({
            value: drClass.members['V'] as number || 0,
            resistance: drClass.members['R'] as number || 0,
          });
        }
      }
    }
    
    item.armor = armor;
  }
  
  return item;
}

function extractInventory(records: NrbfRecord[], refMap: Map<number, NrbfClass>): InventoryItem[] {
  // First, build a map of LIDP/IIDP IDs to their stack counts from II records
  const instanceCounts = new Map<number, number>();
  
  for (const record of records) {
    const cls = record.class;
    if (!cls?.members) continue;
    
    // II records have II:S (stack count) and II:DP (data provider reference)
    if (cls.members['II:S'] !== undefined && cls.members['II:DP'] !== undefined) {
      const dpRef = cls.members['II:DP'];
      if (dpRef && typeof dpRef === 'object' && 'reference' in dpRef) {
        const dpId = (dpRef as { reference: number }).reference;
        const count = cls.members['II:S'] as number || 1;
        instanceCounts.set(dpId, count);
      }
    }
  }
  
  
  // Now collect inventory items with their counts
  const itemsByPath = new Map<string, { path: string; category: string; name: string; counts: number[] }>();
  
  // Find LIDP records (inventory items with paths)
  for (const record of records) {
    const cls = record.class;
    if (!cls?.name?.startsWith('LIDP')) continue;
    if (!cls.members) continue;
    
    const pathField = cls.members['LIDP:P'];
    if (!pathField || typeof pathField !== 'object') continue;
    
    const path = (pathField as { value?: string }).value;
    if (!path || !path.includes('\\')) continue;
    
    const parts = path.split('\\');
    const category = getItemCategory(parts[0]);
    const rawName = parts[parts.length - 1];
    const displayName = getItemDisplayName(rawName);
    
    // Get count from II record if available
    const objectId = cls.id;
    const count = instanceCounts.get(objectId) || 1;
    
    const pathKey = path.toLowerCase();
    const existing = itemsByPath.get(pathKey);
    if (existing) {
      existing.counts.push(count);
    } else {
      itemsByPath.set(pathKey, {
        path,
        category,
        name: displayName,
        counts: [count],
      });
    }
  }
  
  // Convert to array with merged counts
  const items: InventoryItem[] = [];
  for (const item of itemsByPath.values()) {
    const totalCount = item.counts.reduce((a, b) => a + b, 0);
    items.push({
      path: item.path,
      name: item.name,
      category: item.category,
      count: totalCount,
      stacks: item.counts.length > 1 ? item.counts.length : undefined,
      stackCounts: item.counts.length > 1 ? item.counts : undefined,
    });
  }
  
  return items;
}

function extractCurrency(inventory: InventoryItem[]): CurrencyInfo {
  const currency: CurrencyInfo = {};
  
  for (const item of inventory) {
    const pathLower = item.path.toLowerCase();
    if (pathLower.includes('stygiancoin')) {
      currency.stygianCoins = (currency.stygianCoins || 0) + item.count;
    } else if (pathLower.includes('sgscredits')) {
      currency.sgsCredits = (currency.sgsCredits || 0) + item.count;
    }
  }
  
  return currency;
}

