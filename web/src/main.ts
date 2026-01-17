/**
 * Main entry point for Underrail Save Editor
 */

import { parseSaveFile } from './parser';
import {
  getState,
  subscribe,
  startLoading,
  fileLoaded,
  loadError,
  resetState,
  toggleEditMode,
  switchTab,
  updateSkillValue,
  updateAttributeValue,
  type AppState,
} from './state';
import type { SaveData, Skill, Attribute, EquipmentItem, Feat, InventoryItem } from './parser/types';

// DOM Elements
const dropZone = document.getElementById('drop-zone')!;
const filePickerBtn = document.getElementById('file-picker-btn')!;
const fileInput = document.getElementById('file-input') as HTMLInputElement;
const loadingSection = document.getElementById('loading')!;
const errorSection = document.getElementById('error')!;
const errorMessage = document.getElementById('error-message')!;
const errorDismiss = document.getElementById('error-dismiss')!;
const characterView = document.getElementById('character-view')!;
const editModeToggle = document.getElementById('edit-mode-toggle') as HTMLInputElement;
const charName = document.getElementById('char-name')!;
const charLevel = document.getElementById('char-level')!;
const attributesList = document.getElementById('attributes-list')!;
const skillsList = document.getElementById('skills-list')!;
const equipmentList = document.getElementById('equipment-list')!;
const utilityList = document.getElementById('utility-list')!;
const inventoryList = document.getElementById('inventory-list')!;
const featsList = document.getElementById('feats-list')!;
const downloadBtn = document.getElementById('download-btn')!;
const exportCardBtn = document.getElementById('export-card-btn')!;
const loadNewBtn = document.getElementById('load-new-btn')!;
const tabLinks = document.querySelectorAll('.tabs a');
const tabPanels = document.querySelectorAll('.tab-panel');

// Initialize
function init(): void {
  setupDropZone();
  setupFilePicker();
  setupTabs();
  setupEditMode();
  setupActions();
  
  // Subscribe to state changes
  subscribe(render);
}

// Drop zone setup
function setupDropZone(): void {
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });
  
  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });
  
  dropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer?.files;
    if (files?.length) {
      await handleFile(files[0]);
    }
  });
  
  dropZone.addEventListener('click', () => {
    fileInput.click();
  });
}

// File picker setup
function setupFilePicker(): void {
  filePickerBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });
  
  fileInput.addEventListener('change', async () => {
    const files = fileInput.files;
    if (files?.length) {
      await handleFile(files[0]);
    }
  });
}

// Tab setup
function setupTabs(): void {
  tabLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const tab = (link as HTMLElement).dataset.tab as AppState['activeTab'];
      if (tab) {
        switchTab(tab);
      }
    });
  });
}

// Edit mode setup
function setupEditMode(): void {
  editModeToggle.addEventListener('change', () => {
    toggleEditMode(editModeToggle.checked);
  });
}

// Actions setup
function setupActions(): void {
  errorDismiss.addEventListener('click', () => {
    resetState();
  });
  
  loadNewBtn.addEventListener('click', () => {
    resetState();
  });
  
  downloadBtn.addEventListener('click', () => {
    // TODO: Implement download
    alert('Download functionality coming soon!');
  });
  
  exportCardBtn.addEventListener('click', () => {
    // TODO: Implement character card export
    alert('Character card export coming soon!');
  });
}

// Handle file selection
async function handleFile(file: File): Promise<void> {
  startLoading();
  
  try {
    console.log('Parsing file:', file.name, 'Size:', file.size);
    const { saveData, header } = await parseSaveFile(file);
    console.log('Parsed save data:', saveData);
    fileLoaded(file.name, saveData, header);
  } catch (error) {
    console.error('Failed to parse save file:', error);
    if (error instanceof Error) {
      loadError(`${error.message}\n\nStack: ${error.stack?.split('\n').slice(0, 3).join('\n')}`);
    } else {
      loadError('Unknown error parsing save file');
    }
  }
}

// Render based on state
function render(state: AppState): void {
  // Show/hide sections
  dropZone.hidden = state.isLoading || !!state.saveData;
  loadingSection.hidden = !state.isLoading;
  errorSection.hidden = !state.error;
  characterView.hidden = !state.saveData || state.isLoading || !!state.error;
  
  // Error message
  if (state.error) {
    errorMessage.innerHTML = state.error.replace(/\n/g, '<br>');
  }
  
  // Character view
  if (state.saveData) {
    renderCharacter(state.saveData, state.editMode);
  }
  
  // Tabs
  tabLinks.forEach(link => {
    const tab = (link as HTMLElement).dataset.tab;
    link.classList.toggle('active', tab === state.activeTab);
  });
  
  tabPanels.forEach(panel => {
    const panelId = panel.id.replace('tab-', '');
    panel.hidden = panelId !== state.activeTab;
  });
  
  // Download button
  downloadBtn.disabled = !state.hasChanges;
}

// Render character data
function renderCharacter(data: SaveData, editMode: boolean): void {
  try {
    charName.textContent = data.character?.name || 'Unknown';
    charLevel.textContent = (data.character?.level || 1).toString();
    
    renderAttributes(data.attributes || [], editMode);
    renderSkills(data.skills || [], editMode);
    renderEquipment(data.equipment || { characterGear: [], utilitySlots: [], hotbar: [] });
    renderInventory(data.inventory || []);
    renderFeats(data.feats || []);
  } catch (error) {
    console.error('Error rendering character:', error);
    throw error;
  }
}

// Render attributes
function renderAttributes(attributes: Attribute[], editMode: boolean): void {
  attributesList.innerHTML = attributes.map((attr, index) => `
    <div class="stat-row">
      <span class="stat-name">${attr.name}</span>
      <span class="stat-value">
        ${editMode ? `
          <input type="number" class="editable" value="${attr.base}" 
                 min="1" max="99" data-attr-index="${index}">
        ` : `
          <span class="stat-base">${attr.base}</span>
        `}
        ${attr.effective !== attr.base ? `
          <span class="stat-effective">(${attr.effective})</span>
        ` : ''}
      </span>
    </div>
  `).join('');
  
  // Add event listeners for editable inputs
  if (editMode) {
    attributesList.querySelectorAll('input[data-attr-index]').forEach(input => {
      input.addEventListener('change', (e) => {
        const target = e.target as HTMLInputElement;
        const index = parseInt(target.dataset.attrIndex!, 10);
        const value = parseInt(target.value, 10);
        if (!isNaN(value)) {
          updateAttributeValue(index, value);
        }
      });
    });
  }
}

// Render skills grouped by category
function renderSkills(skills: Skill[], editMode: boolean): void {
  const grouped = groupBy(skills, s => s.category);
  const categories = ['Offense', 'Defense', 'Subterfuge', 'Technology', 'Psi', 'Social'];
  
  skillsList.innerHTML = categories.map(category => {
    const categorySkills = grouped[category] || [];
    if (categorySkills.length === 0) return '';
    
    return `
      <div class="skill-category">
        <h4>${category}</h4>
        ${categorySkills.map(skill => `
          <div class="skill-row">
            <span class="skill-name">${skill.name}</span>
            <span class="skill-value">
              ${editMode ? `
                <input type="number" class="editable" value="${skill.base}" 
                       min="0" max="999" data-skill-index="${skill.index}">
              ` : `
                <span class="skill-base">${skill.base}</span>
              `}
              ${skill.effective !== skill.base ? `
                <span class="skill-effective">(${skill.effective})</span>
              ` : ''}
            </span>
          </div>
        `).join('')}
      </div>
    `;
  }).join('');
  
  // Add event listeners for editable inputs
  if (editMode) {
    skillsList.querySelectorAll('input[data-skill-index]').forEach(input => {
      input.addEventListener('change', (e) => {
        const target = e.target as HTMLInputElement;
        const index = parseInt(target.dataset.skillIndex!, 10);
        const value = parseInt(target.value, 10);
        if (!isNaN(value)) {
          updateSkillValue(index, value);
        }
      });
    });
  }
}

// Render equipment
function renderEquipment(equipment: SaveData['equipment']): void {
  equipmentList.innerHTML = equipment.characterGear.map(item => 
    renderEquipmentItem(item)
  ).join('') || '<p>No equipment found</p>';
  
  utilityList.innerHTML = equipment.utilitySlots.map(item => `
    <div class="equipment-item">
      <div class="equipment-item-header">
        <span class="equipment-item-name">${item.name}</span>
        ${item.count && item.count > 1 ? `<span>x${item.count}</span>` : ''}
      </div>
    </div>
  `).join('') || '<p>No utility items</p>';
}

// Render single equipment item
function renderEquipmentItem(item: EquipmentItem): string {
  const stats: string[] = [];
  
  // Weapon stats
  if (item.weapon) {
    const w = item.weapon;
    if (w.damageMin != null && w.damageMax != null) {
      stats.push(`Damage: ${w.damageMin}-${w.damageMax}`);
    }
    if (w.apCost != null) {
      stats.push(`AP: ${w.apCost}`);
    }
    if (w.critChance != null) {
      stats.push(`Crit: ${Math.round(w.critChance * 100)}%`);
    }
    if (w.critDamage != null && w.critDamage !== 1) {
      const bonus = (w.critDamage - 1) * 100;
      stats.push(`Crit Dmg: ${bonus >= 0 ? '+' : ''}${Math.round(bonus)}%`);
    }
  }
  
  // Armor stats
  if (item.armor) {
    for (const dr of item.armor.damageResistances || []) {
      if ((dr.value ?? 0) > 0 || (dr.resistance ?? 0) > 0) {
        stats.push(`DR: ${dr.value ?? 0} (${Math.round((dr.resistance ?? 0) * 100)}%)`);
      }
    }
    if (item.armor.evasionPenalty != null && item.armor.evasionPenalty > 0) {
      stats.push(`Evasion: -${Math.round(item.armor.evasionPenalty * 100)}%`);
    }
  }
  
  // Durability/Energy
  const runtimeStats: string[] = [];
  if (item.currentDurability != null && item.currentDurability > 0) {
    runtimeStats.push(`Durability: ${Math.floor(item.currentDurability)}`);
  }
  if (item.currentBattery != null && item.currentBattery > 0) {
    if (item.maxBattery) {
      runtimeStats.push(`Energy: ${Math.floor(item.currentBattery)}/${item.maxBattery}`);
    } else {
      runtimeStats.push(`Energy: ${Math.floor(item.currentBattery)}`);
    }
  }
  
  // Basic stats
  const basicStats: string[] = [];
  if (item.level != null) {
    basicStats.push(`Lvl: ${item.level}`);
  }
  if (item.value != null) {
    basicStats.push(`Value: ${item.value.toLocaleString()}`);
  }
  if (item.weight != null) {
    basicStats.push(`Weight: ${item.weight.toFixed(1)}`);
  }
  
  return `
    <div class="equipment-item">
      <div class="equipment-item-header">
        <span class="equipment-item-name">${item.name}</span>
        <span class="equipment-item-category">${item.category}</span>
      </div>
      ${stats.length > 0 ? `
        <div class="equipment-item-stats">
          ${stats.map(s => `<span>${s}</span>`).join('')}
        </div>
      ` : ''}
      ${runtimeStats.length > 0 ? `
        <div class="equipment-item-stats">
          ${runtimeStats.map(s => `<span>${s}</span>`).join('')}
        </div>
      ` : ''}
      ${basicStats.length > 0 ? `
        <div class="equipment-item-stats">
          ${basicStats.map(s => `<span>${s}</span>`).join('')}
        </div>
      ` : ''}
    </div>
  `;
}

// Render inventory
function renderInventory(items: InventoryItem[]): void {
  const grouped = groupBy(items, i => i.category);
  const categories = Object.keys(grouped).sort();
  
  inventoryList.innerHTML = categories.map(category => `
    <div class="inventory-category">
      <h4>${category}</h4>
      ${grouped[category].map(item => `
        <div class="inventory-item">
          <span>${item.name}</span>
          <span class="inventory-item-count">x${item.count}</span>
        </div>
      `).join('')}
    </div>
  `).join('') || '<p>No inventory items</p>';
}

// Render feats
function renderFeats(feats: Feat[]): void {
  featsList.innerHTML = feats.map(feat => `
    <span class="feat-item">${feat.name}</span>
  `).join('') || '<p>No feats found</p>';
}

// Utility: group array by key
function groupBy<T>(array: T[], keyFn: (item: T) => string): Record<string, T[]> {
  return array.reduce((groups, item) => {
    const key = keyFn(item);
    (groups[key] = groups[key] || []).push(item);
    return groups;
  }, {} as Record<string, T[]>);
}

// Start the app
init();
