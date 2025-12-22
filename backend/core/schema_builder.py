from typing import Dict, Any, Type, Optional
from pydantic import BaseModel, create_model

class ObjectRegistration:
    """
    Builder for defining game system objects that can generate both
    Pydantic models (backend validation) and JSON schemas (frontend forms).
    """
    
    def __init__(self, system: str = None):
        self.system = system  # e.g., "d&d5.0", "d&d5.2"
        self.fields = {}  # field_name -> dict with field info
        self._model_cache = None
        self._form_cache = None
    
    def add_field(self, name: str, type_instance, base_field: bool = False, 
                  required: bool = False, **kwargs):
        """Add a field definition"""
        self.fields[name] = {
            'type': type_instance,
            'base_field': base_field,
            'required': required,
            'kwargs': kwargs
        }
        # Clear caches when fields change
        self._model_cache = None
        self._form_cache = None
        return self
    
    def model(self) -> Type[BaseModel]:
        """Generate a Pydantic model for validation"""
        if self._model_cache:
            return self._model_cache
        
        # Build field definitions for Pydantic
        pydantic_fields = {}
        for field_name, field_def in self.fields.items():
            py_type, field_obj = field_def['type'].to_pydantic_field()
            
            # If not required, ensure it's optional in Pydantic
            if not field_def['required']:
                if not str(py_type).startswith('typing.Optional'):
                    py_type = Optional[py_type]
                
                # In Pydantic v2, we ensure the Field object has default=None if it doesn't already
                from pydantic_core import PydanticUndefined
                if hasattr(field_obj, 'default') and field_obj.default == PydanticUndefined:
                    field_obj.default = None
            
            pydantic_fields[field_name] = (py_type, field_obj)
        
        # Create dynamic Pydantic model
        self._model_cache = create_model(
            f'{self.system.replace(".", "_") if self.system else "Generic"}Model',
            **pydantic_fields
        )
        return self._model_cache
    
    def form(self) -> Dict[str, Any]:
        """Generate JSON schema for frontend form generation"""
        if self._form_cache:
            return self._form_cache
        
        form_fields = []
        for field_name, field_def in self.fields.items():
            form_field = field_def['type'].to_form_field()
            form_field['name'] = field_name
            form_field['required'] = field_def['required']
            form_field['base_field'] = field_def['base_field']
            form_fields.append(form_field)
        
        self._form_cache = {
            'system': self.system,
            'fields': form_fields
        }
        return self._form_cache
    
    # Convenience methods for hierarchical patterns
    def add_parent_field(self, label: str = "Parent Entry"):
        """Add a parent link field for hierarchical structures"""
        from core.field_types import parent_link
        return self.add_field("parent_guid", parent_link(label), base_field=True, required=False)
    
    def add_category_field(self):
        """Add an entry category field (container/definition/item)"""
        from core.field_types import entry_category
        return self.add_field("entry_category", entry_category(), base_field=True, required=False)
    
    def add_markdown_field(self, name: str = "description", max_len: int = 10000, 
                          placeholder: str = "", required: bool = False):
        """Add a markdown field for rich text descriptions"""
        from core.field_types import markdown
        return self.add_field(name, markdown(max_len, placeholder), base_field=True, required=required)
