"""Versioned rollout switches with explicit environment pause/override."""
import json
import os
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent/'config/discovery.json'
KEYS = {'BORIS_DISCOVERY_ENABLED':'discovery_enabled',
        'BORIS_DYNAMIC_INVENTORY':'dynamic_inventory_enabled'}

def enabled(name):
    if name not in KEYS:
        raise ValueError('invalid_operational_switch')
    value=os.getenv(name,'').strip().lower()
    if value:
        if value not in ('0','false','1','true'):
            code='invalid_dynamic_inventory_gate' if name=='BORIS_DYNAMIC_INVENTORY' else 'invalid_discovery_gate'
            raise ValueError(code)
        return value in ('1','true')
    config=json.loads(CONFIG.read_text())
    if (config.get('schema_version')!=1 or
        any(type(config.get(key)) is not bool for key in KEYS.values())):
        raise ValueError('invalid_operational_configuration')
    return config[KEYS[name]]
