/**
 * Simple state management for the application.
 */

import type { SaveData } from './parser/types';

export interface AppState {
  // File state
  fileName: string | null;
  header: Uint8Array | null;
  rawData: Uint8Array | null;  // Uncompressed binary for potential patching
  saveData: SaveData | null;
  
  // UI state
  isLoading: boolean;
  error: string | null;
  editMode: boolean;
  hasChanges: boolean;
  activeTab: 'stats' | 'equipment' | 'inventory' | 'feats';
}

// Initial state
const initialState: AppState = {
  fileName: null,
  header: null,
  rawData: null,
  saveData: null,
  isLoading: false,
  error: null,
  editMode: false,
  hasChanges: false,
  activeTab: 'stats',
};

// Current state
let state: AppState = { ...initialState };

// Subscribers for state changes
type Subscriber = (state: AppState) => void;
const subscribers: Set<Subscriber> = new Set();

/**
 * Get current state.
 */
export function getState(): AppState {
  return state;
}

/**
 * Update state and notify subscribers.
 */
export function setState(updates: Partial<AppState>): void {
  state = { ...state, ...updates };
  notifySubscribers();
}

/**
 * Reset state to initial values.
 */
export function resetState(): void {
  state = { ...initialState };
  notifySubscribers();
}

/**
 * Subscribe to state changes.
 */
export function subscribe(callback: Subscriber): () => void {
  subscribers.add(callback);
  return () => subscribers.delete(callback);
}

/**
 * Notify all subscribers of state change.
 */
function notifySubscribers(): void {
  for (const callback of subscribers) {
    callback(state);
  }
}

// Actions

/**
 * Start loading a file.
 */
export function startLoading(): void {
  setState({ isLoading: true, error: null });
}

/**
 * File loaded successfully.
 */
export function fileLoaded(fileName: string, saveData: SaveData, header: Uint8Array, rawData: Uint8Array): void {
  setState({
    fileName,
    saveData,
    header,
    rawData,
    isLoading: false,
    error: null,
    hasChanges: false,
  });
}

/**
 * File loading failed.
 */
export function loadError(error: string): void {
  setState({
    isLoading: false,
    error,
  });
}

/**
 * Toggle edit mode.
 */
export function toggleEditMode(enabled: boolean): void {
  setState({ editMode: enabled });
}

/**
 * Mark that changes have been made.
 */
export function markChanged(): void {
  setState({ hasChanges: true });
}

/**
 * Switch active tab.
 */
export function switchTab(tab: AppState['activeTab']): void {
  setState({ activeTab: tab });
}

/**
 * Update a skill value.
 */
export function updateSkillValue(index: number, newBase: number): void {
  const { saveData } = state;
  if (!saveData) return;
  
  const skill = saveData.skills[index];
  if (!skill) return;
  
  // Calculate new effective (preserve bonus)
  const bonus = skill.effective - skill.base;
  const newEffective = Math.max(0, newBase + bonus);
  
  // Update in place
  skill.base = newBase;
  skill.effective = newEffective;
  
  setState({ saveData: { ...saveData }, hasChanges: true });
}

/**
 * Update an attribute value.
 */
export function updateAttributeValue(index: number, newBase: number): void {
  const { saveData } = state;
  if (!saveData) return;
  
  const attr = saveData.attributes[index];
  if (!attr) return;
  
  // Calculate new effective (preserve bonus)
  const bonus = attr.effective - attr.base;
  const newEffective = Math.max(1, newBase + bonus);
  
  // Update in place
  attr.base = newBase;
  attr.effective = newEffective;
  
  setState({ saveData: { ...saveData }, hasChanges: true });
}
