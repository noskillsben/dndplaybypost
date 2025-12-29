from asteval import Interpreter
import math

class BakingEngine:
    def _create_interpreter(self):
        aeval = Interpreter()
        aeval.symtable['ceil'] = math.ceil
        aeval.symtable['floor'] = math.floor
        aeval.symtable['min'] = min
        aeval.symtable['max'] = max
        aeval.symtable['abs'] = abs
        return aeval

    def bake(self, actor_data: dict, logic_definitions: dict) -> dict:
        """
        Bakes raw_data into derived_data using logic definitions.
        """
        # Create a fresh interpreter for this bake session
        interpreter = self._create_interpreter()
        
        # 1. Initialize context with raw values converted to objects for dot access
        context = self._to_object(actor_data)
        
        # Load context into interpreter symbol table
        interpreter.symtable.update(context.__dict__)
        
        derived_data = {}
        
        # 2. Collect Modifiers from Inventory/Features
        modifiers = self.collect_modifiers(actor_data)
        
        # 3. Resolve Dependencies
        sorted_keys = self.resolve_dependencies(logic_definitions)
        
        for target_path in sorted_keys:
            formula = logic_definitions[target_path]
            
            # A. Calculate Base Value
            try:
                # Formula evaluation uses the interpreter which has 'context' in its symtable
                raw_result = interpreter(formula)
            except Exception as e:
                print(f"NameError: {formula}\n{e}")
                raw_result = 0 
            
            # B. Apply Modifiers (Priority System)
            if target_path in modifiers:
                final_value, applied_mods = self.apply_modifiers(raw_result, modifiers[target_path])
                
                # Update derived_data (dict)
                self._set_deep(derived_data, target_path, {
                    "value": final_value,
                    "base": raw_result,
                    "modifiers": applied_mods
                })
                # Update context (object) with the FINAL evaluated value for dependent formulas
                self._set_deep_object(context, target_path, final_value)
                
                # Update interpreter symbol table with new/updated context value?
                # Since 'context' object is in symtable, and we updated 'context' in place using _set_deep_object,
                # attributes on 'context' object are updated.
                # BUT: we passed context.__dict__ to symtable.update().
                # If context is a SimpleNamespace-like object...
                # context.__dict__ copies reference to values? No.
                # update() copies keys/values.
                # So changing 'context' object attributes DOES NOT update interpreter.symtable entries if they were shallow copied.
                # Wait, 'context' itself is NOT in symtable as 'context'.
                # We unpacked it: `symtable.update(context.__dict__)`.
                # So if context has 'stats', symtable has 'stats' pointing to the same ContextObj.
                # _set_deep_object modifies the ContextObj.
                # So yes, it SHOULD reflect.
            else:
                self._set_deep(derived_data, target_path, raw_result)
                self._set_deep_object(context, target_path, raw_result)
                # No need to re-update symtable as long as we modified the object referred to by the key in symtable.
                
        return derived_data

    def collect_modifiers(self, actor_data: dict) -> dict:
        modifiers = {}
        def add_mod(mod, source_name):
            target = mod.get('target')
            if not target: return
            if target not in modifiers: modifiers[target] = []
            modifiers[target].append({
                'source': source_name,
                'value': mod.get('value', 0),
                'type': mod.get('type', 'additive'),
                'priority': mod.get('priority', 10)
            })

        for item in actor_data.get('inventory', []):
            if item.get('equipped', False):
                for mod in item.get('modifiers', []):
                    add_mod(mod, item.get('name', 'Unknown Item'))
        
        for feature in actor_data.get('features', []):
             for mod in feature.get('modifiers', []):
                    add_mod(mod, feature.get('name', 'Unknown Feature'))
                    
        return modifiers

    def apply_modifiers(self, base_value, mods):
        sorted_mods = sorted(mods, key=lambda x: x['priority'])
        current_value = base_value
        applied = []
        for mod in sorted_mods:
            m_type = mod['type']
            m_val = int(mod['value']) if isinstance(mod['value'], (int, float)) else mod['value']
            
            if m_type == 'set':
                current_value = m_val
            elif m_type == 'additive':
                current_value += m_val
            elif m_type == 'multiplier':
                current_value *= m_val
            applied.append(mod)
        return current_value, applied

    def resolve_dependencies(self, logic_definitions: dict) -> list:
        keys = list(logic_definitions.keys())
        adj = {k: set() for k in keys}
        for k in keys:
            formula = logic_definitions[k]
            for potential_dep in keys:
                if k == potential_dep: continue
                if potential_dep in formula:
                    adj[k].add(potential_dep)
        
        visited = set()
        order = []
        
        def visit(node):
            if node in visited: return
            visited.add(node)
            for dep in adj[node]:
                visit(dep)
            order.append(node)
            
        for k in keys:
            visit(k)
        return order

    def _to_object(self, data):
        """Recursively converts dict to a simple object enabling dot access."""
        if isinstance(data, dict):
            obj = type('ContextObj', (), {})()
            for k, v in data.items():
                setattr(obj, k, self._to_object(v))
            return obj
        elif isinstance(data, list):
            return [self._to_object(i) for i in data]
        else:
            return data

    def _set_deep(self, d, keys, value):
        if isinstance(keys, str): keys = keys.split('.')
        latest = d
        for k in keys[:-1]:
            latest = latest.setdefault(k, {})
        latest[keys[-1]] = value
        
    def _set_deep_object(self, obj, keys, value):
        if isinstance(keys, str): keys = keys.split('.')
        latest = obj
        for k in keys[:-1]:
            if not hasattr(latest, k):
                setattr(latest, k, type('ContextObj', (), {})())
            latest = getattr(latest, k)
        setattr(latest, keys[-1], value)
        """
        Bakes raw_data into derived_data using logic definitions.
        """
        # 1. Initialize context with raw values converted to objects for dot access
        context = self._to_object(actor_data)
        derived_data = {}
        
        # 2. Collect Modifiers from Inventory/Features
        modifiers = self.collect_modifiers(actor_data)
        
        # 3. Resolve Dependencies
        sorted_keys = self.resolve_dependencies(logic_definitions)
        
        for target_path in sorted_keys:
            formula = logic_definitions[target_path]
            
            # A. Calculate Base Value
            try:
                raw_result = self.evaluate_formula(formula, context)
            except Exception as e:
                print(f"NameError: {formula}\n{e}")
                raw_result = 0 # Default fallback?
            
            # B. Apply Modifiers (Priority System)
            if target_path in modifiers:
                final_value, applied_mods = self.apply_modifiers(raw_result, modifiers[target_path])
                
                # Update derived_data (dict)
                self._set_deep(derived_data, target_path, {
                    "value": final_value,
                    "base": raw_result,
                    "modifiers": applied_mods
                })
                # Update context (object) with the FINAL evaluated value for dependent formulas
                self._set_deep_object(context, target_path, final_value)
            else:
                self._set_deep(derived_data, target_path, raw_result)
                self._set_deep_object(context, target_path, raw_result)
                
        return derived_data

    def collect_modifiers(self, actor_data: dict) -> dict:
        modifiers = {}
        def add_mod(mod, source_name):
            target = mod.get('target')
            if not target: return
            if target not in modifiers: modifiers[target] = []
            modifiers[target].append({
                'source': source_name,
                'value': mod.get('value', 0),
                'type': mod.get('type', 'additive'),
                'priority': mod.get('priority', 10)
            })

        for item in actor_data.get('inventory', []):
            if item.get('equipped', False):
                for mod in item.get('modifiers', []):
                    add_mod(mod, item.get('name', 'Unknown Item'))
        
        for feature in actor_data.get('features', []):
             for mod in feature.get('modifiers', []):
                    add_mod(mod, feature.get('name', 'Unknown Feature'))
                    
        return modifiers

    def apply_modifiers(self, base_value, mods):
        sorted_mods = sorted(mods, key=lambda x: x['priority'])
        current_value = base_value
        applied = []
        for mod in sorted_mods:
            m_type = mod['type']
            m_val = int(mod['value']) if isinstance(mod['value'], (int, float)) else mod['value']
            
            if m_type == 'set':
                current_value = m_val
            elif m_type == 'additive':
                current_value += m_val
            elif m_type == 'multiplier':
                current_value *= m_val
            applied.append(mod)
        return current_value, applied

    def evaluate_formula(self, formula: str, context: object):
        # Pass the context object as the symbol table? 
        # No, astval symtable expects a dict.
        # But we want dot access inside the formula.
        # If formula is "stats.strength.base", python looks up "stats", then ".strength", then ".base".
        # So "stats" must be in symtable.
        # We can pass the top-level keys of context to symtable.
        
        # context is a SimpleNamespace-like object.
        # We convert it to a dict of top-level keys?
        # Yes.
        
        return self.aeval(formula, usersyms=context.__dict__)

    def resolve_dependencies(self, logic_definitions: dict) -> list:
        keys = list(logic_definitions.keys())
        adj = {k: set() for k in keys}
        for k in keys:
            formula = logic_definitions[k]
            for potential_dep in keys:
                if k == potential_dep: continue
                if potential_dep in formula:
                    adj[k].add(potential_dep)
        
        visited = set()
        order = []
        
        def visit(node):
            if node in visited: return
            visited.add(node)
            for dep in adj[node]:
                visit(dep)
            order.append(node)
            
        for k in keys:
            visit(k)
        return order

    def _to_object(self, data):
        """Recursively converts dict to a simple object enabling dot access."""
        if isinstance(data, dict):
            obj = type('ContextObj', (), {})()
            for k, v in data.items():
                setattr(obj, k, self._to_object(v))
            return obj
        elif isinstance(data, list):
            return [self._to_object(i) for i in data]
        else:
            return data

    def _set_deep(self, d, keys, value):
        if isinstance(keys, str): keys = keys.split('.')
        latest = d
        for k in keys[:-1]:
            latest = latest.setdefault(k, {})
        latest[keys[-1]] = value
        
    def _set_deep_object(self, obj, keys, value):
        if isinstance(keys, str): keys = keys.split('.')
        latest = obj
        for k in keys[:-1]:
            if not hasattr(latest, k):
                setattr(latest, k, type('ContextObj', (), {})())
            latest = getattr(latest, k)
        setattr(latest, keys[-1], value)
