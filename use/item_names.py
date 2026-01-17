#!/usr/bin/env python3
"""
Item display name mappings extracted from Underrail game files.

This module provides a lookup from internal item names (as stored in save files)
to their display names (as shown in-game).

Generated from: E:\\SteamLibrary\\steamapps\\common\\Underrail\\data\\rules\\items\\*.item
"""

# Mapping from internal name (lowercase) to display name
# Extracted from game .item files which contain both internal and display names
ITEM_DISPLAY_NAMES = {
    # === Currency ===
    'sc': 'Stygian Coin',
    'sgs': 'SGS Credits',
    'stygiancoin': 'Stygian Coin',
    'sgscredits': 'SGS Credits',
    
    # === Weapons ===
    'throwingknife': 'Throwing Knife',
    'shiv': 'Shiv',
    'jackknife': 'Jackknife',
    'brassknuckles': 'Brass Knuckles',
    'boxinggloves': 'Boxing Gloves',
    'steelcrowbar': 'Steel Crowbar',
    'rollingpin': 'Rolling Pin',
    'boningknife': 'Boning Knife',
    'powerfist': 'Power Fist',
    'balorshammer': "Balor's Hammer",
    'mindcracker': 'Mind Cracker',
    'wickedhook': 'Wicked Hook',
    'phasegun': 'Phase Gun',
    'reddragon': 'Red Dragon',
    'theclaw': 'The Claw',
    'tommygun': 'Tommy Gun',
    'shockshuriken': 'Shock Shuriken',
    
    # === Armor/Belts ===
    'waistpack': 'Waist Pack',
    'largewaistpack': 'Large Waist Pack',
    'utility': 'Utility Belt',
    'utilitybelt': 'Utility Belt',  # Both internal names map to same display name
    'lifting': 'Lifting Belt',
    'bulletstrap': 'Bullet Strap Belt',
    'shellstrapbelt': 'Shell Strap Belt',
    'commandobelt': 'Commando Belt',
    'catalyzingbelt': 'Catalyzing Belt',
    'shirtandpants': 'Shirt & Pants',
    'sturdyvest': 'Sturdy Vest',
    'blastsuit': 'Blast Suit',
    'biohazardsuit': 'Biohazard Suit',
    'biohazardvest': 'Biohazard Vest',
    'biohazardboots': 'Biohazard Boots',
    'nightvisiongoggles': 'Nightvision Goggles',
    'workersuit': 'Work Coverall',
    'mininghelmet': 'Mining Helmet',
    'launchergrenadebelt': 'Launcher Grenade Strap Belt',
    
    # === Consumables/Medical ===
    'psibooster': 'Psi Booster',
    'healthhypo': 'Health Hypo',
    'healthhypoenriched': 'Enriched Health Hypo',
    'advancedhealthhypo': 'Advanced Health Hypo',
    'advancedhealthhypoenriched': 'Enriched Advanced Health Hypo',
    'superhealthhypo': 'Super Health Hypo',
    'superhealthhypoenriched': 'Enriched Super Health Hypo',
    'adrenalineshot': 'Adrenaline Shot',
    'minddart': 'Mind Dart',
    'coagulationshot': 'Coagulation Shot',
    'healingsalve': 'Healing Salve',
    'spiritpotion': 'Spirit Potion',
    'vitalitypowder': 'Vitality Powder',
    'psireinvigorator': 'Psi Reinvigorator',
    'psionicaccelerator': 'Psionic Accelerator',
    'thirdeye': 'Third Eye',
    'antidote': 'Antidote',
    'bandage': 'Bandage',
    'morphineshot': 'Morphine Shot',
    
    # === Devices ===
    'fishingrod': 'Fishing Rod',
    'hotwiringkit': 'Hotwiring Kit',
    'electrictorch': 'Electric Torch',
    'compass': 'Compass',
    'flare': 'Flare',
    'lockpick': 'Lockpick',
    'lockpick2': 'Lockpick Mk II',
    'lockpick3': 'Lockpick Mk III',
    'haxxor2': 'Haxxor Mk II',
    'haxxor3': 'Haxxor Mk III',
    'mechanicalrepairkit1': 'Mechanical Repair Kit',
    'mechanicalrepairkit2': 'Advanced Mechanical Repair Kit',
    'electronicrepairkit1': 'Electronic Repair Kit',
    'electronicrepairkit2': 'Advanced Electronic Repair Kit',
    'patchingkit1': 'Patching Kit',
    'patchingkit2': 'Advanced Patching Kit',
    'aiscrambler': 'AI Scrambler',
    'camerajammer': 'Camera Jammer',
    'spyingendoscope': 'Spying Endoscope',
    'nightvisionspyingendoscope': 'Night Vision Spying Endoscope',
    'monolithtorch': 'Ethereal Torch',
    'jumpingstilts': 'Jumping Stilts',
    'omnitool': 'Omni-Tool',
    'jackhammer': 'Jackhammer',
    
    # === Traps ===
    'beartrap': 'Bear Trap',
    'burrowerpoisonbeartrap': 'Burrower Poison Bear Trap',
    'caveearpoisonbeartrap': 'Cave Ear Poison Bear Trap',
    'blackdragonpoisonbeartrap': 'Black Dragon Poison Bear Trap',
    'blindingpoisonbeartrap': 'Blinding Poison Bear Trap',
    'heartbreakpoisonbeartrap': 'Heartbreak Poison Bear Trap',
    'leperpoisonbeartrap': 'Leper Poison Bear Trap',
    'hoppertrap': 'Hopper Trap',
    'hemine1': 'HE Mine',
    'hemine2': 'HE Mine Mk II',
    'hemine3': 'HE Mine Mk III',
    'hemine4': 'HE Mine Mk IV',
    'hemine5': 'HE Mine Mk V',
    'empmine1': 'EMP Mine',
    'empmine2': 'EMP Mine Mk II',
    'empmine3': 'EMP Mine Mk III',
    'fragmine1': 'Frag Mine',
    'fragmine2': 'Frag Mine Mk II',
    'fragmine3': 'Frag Mine Mk III',
    'fragmine4': 'Frag Mine Mk IV',
    'fragmine5': 'Frag Mine Mk V',
    'plasmamine1': 'Plasma Mine',
    'plasmamine2': 'Plasma Mine Mk II',
    'plasmamine3': 'Plasma Mine Mk III',
    'acidblobtrap1': 'Acid Blob Trap',
    'acidblobtrap2': 'Acid Blob Trap Mk II',
    'acidblobtrap3': 'Acid Blob Trap Mk III',
    'incendiaryblobtrap1': 'Incendiary Blob Trap',
    'incendiaryblobtrap2': 'Incendiary Blob Trap Mk II',
    'incendiaryblobtrap3': 'Incendiary Blob Trap Mk III',
    'rustingblobtrap1': 'Rusting Acid Blob Trap',
    
    # === Grenades ===
    # Short names (used in save files)
    'frag1': 'Frag Grenade',
    'frag2': 'Frag Grenade Mk II',
    'frag3': 'Frag Grenade Mk III',
    'frag4': 'Frag Grenade Mk IV',
    'frag5': 'Frag Grenade Mk V',
    'he1': 'HE Grenade',
    'he2': 'HE Grenade Mk II',
    'he3': 'HE Grenade Mk III',
    'he4': 'HE Grenade Mk IV',
    'he5': 'HE Grenade Mk V',
    'emp1': 'EMP Grenade',
    'emp2': 'EMP Grenade Mk II',
    'emp3': 'EMP Grenade Mk III',
    'emp4': 'EMP Grenade Mk IV',
    'emp5': 'EMP Grenade Mk V',
    'flashbang': 'Flashbang',
    # Long names (alternate)
    'hegrenade1': 'HE Grenade',
    'hegrenade2': 'HE Grenade Mk II',
    'hegrenade3': 'HE Grenade Mk III',
    'hegrenade4': 'HE Grenade Mk IV',
    'hegrenade5': 'HE Grenade Mk V',
    'plasmagrande1': 'Plasma Grenade',
    'plasmagrande2': 'Plasma Grenade Mk II',
    'plasmagrande3': 'Plasma Grenade Mk III',
    'molotovcocktail': 'Molotov Cocktail',
    'napalmgrenade': 'Napalm Grenade',
    'magnesiumgrenade': 'Magnesium Grenade',
    'stingballgrenade': 'Stingball Grenade',
    'chemhazegrenade': 'Chemhaze Grenade',
    'toxicgasgrenade': 'Toxic Gas Grenade',
    'nailbomb': 'Nail Bomb',
    'vanishingpowder': 'Vanishing Powder Grenade',
    
    # === Components/Crafting ===
    'plasmacore': 'Plasma Core',
    'rubbersole': 'Rubber Sole',
    'metalscraps': 'Metal Scraps',
    'electronicscraps': 'Electronic Scraps',
    'fabricscraps': 'Fabric Scraps',
    'steel': 'Steel Plates',
    'supersteel': 'Super Steel Plates',
    'tungstensteel': 'Tungsten Steel Plates',
    'trichrome': 'TiChrome Bars',
    'laseremitter': 'Laser Emitter',
    'pneumatichammer': 'Pneumatic Hammer',
    'electroshockgenerator': 'Electroshock Generator',
    'emfstabilizer': 'Electromagnetic Field Stabilizer',
    'emfieldstabilizer': 'Electromagnetic Field Stabilizer',
    'highfrequencyshieldmodulator': 'High Frequency Shield Modulator',
    # Gun barrels (caliber components) - per game files and wiki
    'barrel5': '5mm Firearm Barrel',
    'barrel9': '9mm Firearm Barrel',
    'barrel44': '.44 Firearm Barrel',
    'barrel762': '7.62mm Firearm Barrel',
    'barrel86': '8.6mm Firearm Barrel',
    'barrel127': '12.7mm Firearm Barrel',
    'knifemold': 'Knife Mold',
    'daggermold': 'Dagger Mold',
    'serratedknifemold': 'Serrated Knife Mold',
    'knifehandle': 'Knife Handle',
    'machetehandle': 'Machete Handle',
    'spearshaft': 'Spear Shaft',
    'sledgehammerhandle': 'Sledgehammer Handle',
    'sharpeningstone': 'Sharpening Stone',
    'bondingagent': 'Bonding Agent',
    'opticalfiber': 'Optical Fiber',
    'shieldcapacitor': 'Shield Capacitor',
    'liquidnitrogen': 'Liquid Nitrogen',
    'whitephosphorus': 'White Phosphorus',
    'rocketpropellant': 'Rocket Propellant',
    
    # === Bio/Organic Components ===
    'adrenalgland': 'Adrenal Gland',
    'animalheart': 'Healthy Animal Heart',
    'rathoundleather': 'Rathound Leather',
    'ancientrathoundleather': 'Ancient Rathound Leather',
    'cavehopperleather': 'Cave Hopper Leather',
    'bisonleather': 'Bison Leather',
    'pigleather': 'Pig Leather',
    'siphonerleather': 'Siphoner Leather',
    'seawyrmscales': 'Sea Wyrm Scales',
    'psibeetlecarapace': 'Psi Beetle Carapace',
    'burrowertarsus': 'Burrower Tarsus Charm',
    'rathoundpaw': 'Rathound Paw Charm',
    'hopperfoot': 'Hopper Foot Charm',
    'warthogfoot': 'Warthog Foot Charm',
    'psibeetleclaw': 'Psi Beetle Claw Charm',
    'insectoidsaliva': 'Insectoid Saliva',
    'humanbrain': 'Human Brain',
    
    # === Plants/Mushrooms ===
    'caveear': 'Cave Ear',
    'mindshroom': 'Mindshroom',
    'reddreammushroom': 'Red Dream Mushroom',
    'spiritmushroom': 'Spirit Mushroom',
    'lakemushroom': 'Lake Mushroom',
    'lakepoppy': 'Lake Poppy',
    'greenwart': 'Green Wart',
    'cavetear': 'Cave Tear',
    'honeyspores': 'Honey Spores',
    
    # === Chemicals/Poisons ===
    'burrowerpoison': 'Burrower Poison',
    'caveearpoison': 'Cave Ear Poison',
    'spiritpoison': 'Spirit Poison',
    'blackdragonpoison': 'Black Dragon Poison',
    'blindingpoison': 'Blinding Poison',
    'heartbreakpoison': 'Heartbreak Poison',
    'leperpoison': 'Leper Poison',
    'toxicsludge': 'Toxic Sludge',
    'rusting': 'Rusting Acid',
    'gasoline': 'Gasoline',
    'midazolam': 'Midazolam',
    
    # === Food ===
    'cannedmeat': 'Canned Meat',
    'cannedfish': 'Canned Fish',
    'cannedmushrooms': 'Canned Mushrooms',
    'cannedstew': 'Canned Stew',
    'rathoundbarbeque': 'Rathound Barbecue',
    'burrowerburger': 'Burrower Burger',
    'cavehoppersteak': 'Cave Hopper Steak',
    'mushroombrew': 'Mushroom Brew',
    'mushroomsalad': 'Mushroom Salad',
    'hardcorechips': 'Hardcore Chips',
    'psibeetlebrainsoup': 'Psi Beetle Brain Soup',
    'whitedude': 'White Dude',
    'rootsoda': 'Root Soda',
    'underpie': 'Under Pie',
    'butterysteamedclams': 'Buttery Steamed Clams',
    'baconcheesesandwich': 'Bacon and Cheese Sandwich',
    
    # === Expendables/Energy ===
    'tnt': 'TNT Charge',
    'tntcharge': 'TNT Charge',
    'c4explosivecharge': 'C4 Explosive Charge',
    'miningexplosive': 'Mining Explosive',
    'stonebolas': 'Stone Bolas',
    'throwingnet': 'Throwing Net',
    'barbedthrowingnet': 'Barbed Throwing Net',
    'fusioncell': 'Fusion Cell',
    'greaterfusioncell': 'Greater Fusion Cell',
    'sclicell': 'Supercharged Lithium Cell',
    
    # === Ammunition/Bolts ===
    'boltquiver': 'Bolt Quiver',
    'incendiarybolt1': 'Incendiary Bolt',
    'incendiarybolt2': 'Incendiary Bolt Mk II',
    'incendiarybolt3': 'Incendiary Bolt Mk III',
    'mechanicalbolt1': 'Serrated Bolt',
    'mechanicalbolt2': 'Serrated Bolt Mk II',
    'mechanicalbolt3': 'Serrated Bolt Mk III',
    'shockbolt1': 'Shock Bolt',
    'shockbolt2': 'Shock Bolt Mk II',
    'shockbolt3': 'Shock Bolt Mk III',
    'chemicalbolt1': 'Chemical Bolt',
    'chemicalbolt2': 'Chemical Bolt Mk II',
    'chemicalbolt3': 'Chemical Bolt Mk III',
    'broadheadbolt1': 'Broadhead Bolt',
    'broadheadbolt2': 'Broadhead Bolt Mk II',
    'broadheadbolt3': 'Broadhead Bolt Mk III',
    
    # === SMG/Gun Frames ===
    'smgframe1': 'SMG Frame: Jaguar',
    'smgframe2': 'SMG Frame: Steel Cat',
    'smgframe3': 'SMG Frame: Jackrabbit',
    'smgframe4': 'SMG Frame: Impala',
    'pistolframe1': 'Pistol Frame: Hawker',
    'pistolframe2': 'Pistol Frame: Hammerer',
    'pistolframe3': 'Pistol Frame: Neo Luger',
    'pistolframe4': 'Pistol Frame: Falchion',
    
    # === Misc ===
    'biologicalwatch': 'Biological Watch',
    'ceramicwatch': 'Ceramic Watch',
    'goldring': 'Gold Ring',
    'damagednecklace': 'Damaged Necklace',
}


def get_display_name(internal_name: str) -> str | None:
    """
    Get the display name for an internal item name.
    
    Args:
        internal_name: The internal name (from save file), case-insensitive
        
    Returns:
        Display name if found, None otherwise
    """
    return ITEM_DISPLAY_NAMES.get(internal_name.lower())


def has_display_name(internal_name: str) -> bool:
    """Check if we have a display name mapping for this internal name."""
    return internal_name.lower() in ITEM_DISPLAY_NAMES
