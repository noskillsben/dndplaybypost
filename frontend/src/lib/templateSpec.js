// Helpers for the entry-type template editor: convert between the editable
// in-UI model (strings in inputs, comma-separated options) and the field-spec
// JSON the backend stores (see backend/core/template_store.py).

export const FIELD_TYPES = {
    short_text: {
        label: 'Short text',
        params: [
            { name: 'max_len', kind: 'int', label: 'Max length' },
            { name: 'placeholder', kind: 'text', label: 'Placeholder' }
        ]
    },
    long_text: {
        label: 'Long text',
        params: [
            { name: 'max_len', kind: 'int', label: 'Max length' },
            { name: 'placeholder', kind: 'text', label: 'Placeholder' }
        ]
    },
    markdown: {
        label: 'Markdown',
        params: [
            { name: 'max_len', kind: 'int', label: 'Max length' },
            { name: 'placeholder', kind: 'text', label: 'Placeholder' }
        ]
    },
    integer: {
        label: 'Integer',
        params: [
            { name: 'min_val', kind: 'int', label: 'Min' },
            { name: 'max_val', kind: 'int', label: 'Max' }
        ]
    },
    decimal: {
        label: 'Decimal',
        params: [
            { name: 'min_val', kind: 'number', label: 'Min' },
            { name: 'max_val', kind: 'number', label: 'Max' },
            { name: 'step', kind: 'number', label: 'Step' }
        ]
    },
    boolean: {
        label: 'Checkbox',
        params: [{ name: 'label', kind: 'text', label: 'Label' }]
    },
    select: {
        label: 'Select (fixed options)',
        params: [
            { name: 'options', kind: 'options', label: 'Options (comma-separated)' },
            { name: 'label', kind: 'text', label: 'Label' }
        ]
    },
    compendium_link: {
        label: 'Compendium link',
        params: [
            { name: 'query', kind: 'text', label: 'Query (e.g. type:skill)' },
            { name: 'label', kind: 'text', label: 'Label' }
        ]
    },
    compendium_link_list: {
        label: 'Compendium link list',
        params: [
            { name: 'query', kind: 'text', label: 'Query (e.g. type:skill)' },
            { name: 'label', kind: 'text', label: 'Label' }
        ]
    },
    parent_link: {
        label: 'Parent link',
        params: [{ name: 'label', kind: 'text', label: 'Label' }]
    },
    entry_category: {
        label: 'Entry category',
        params: []
    },
    dice_expression: {
        label: 'Dice expression',
        params: [{ name: 'placeholder', kind: 'text', label: 'Placeholder' }]
    },
    list_of: {
        label: 'List of...',
        params: [
            { name: 'item', kind: 'item', label: 'Item type' },
            { name: 'min_items', kind: 'int', label: 'Min items' },
            { name: 'max_items', kind: 'int', label: 'Max items' },
            { name: 'label', kind: 'text', label: 'Label' }
        ]
    },
    table: {
        label: 'Table (typed columns)',
        params: [
            { name: 'columns', kind: 'columns', label: 'Columns' },
            { name: 'min_rows', kind: 'int', label: 'Min rows' },
            { name: 'max_rows', kind: 'int', label: 'Max rows' },
            { name: 'label', kind: 'text', label: 'Label' }
        ]
    },
    choice: {
        label: 'Choice (pick N from...)',
        params: [
            { name: 'query', kind: 'text', label: 'Option query (e.g. type:skill)' },
            { name: 'label', kind: 'text', label: 'Label' }
        ]
    },
    grant: {
        label: 'Grant (guid list)',
        params: [
            { name: 'query', kind: 'text', label: 'Picker query (e.g. type:trait)' },
            { name: 'label', kind: 'text', label: 'Label' },
            { name: 'min_items', kind: 'int', label: 'Min items' },
            { name: 'max_items', kind: 'int', label: 'Max items' }
        ]
    }
};

export function emptyFieldSpec(type = 'short_text') {
    return { name: '', type, required: false, base_field: false, params: {} };
}

export function nameFieldSpec() {
    return {
        name: 'name',
        type: 'short_text',
        required: true,
        base_field: true,
        params: { max_len: 200 }
    };
}

// Editable model -> API field spec. Drops empty params, coerces numbers,
// splits comma-separated options, recurses into list items / table columns.
export function cleanFieldSpec(model, { withName = true, withFlags = true } = {}) {
    const meta = FIELD_TYPES[model.type];
    if (!meta) {
        throw new Error(`Unknown field type: ${model.type}`);
    }
    const params = {};
    const raw = model.params || {};
    for (const param of meta.params) {
        const value = raw[param.name];
        if (param.kind === 'item') {
            if (value) {
                params.item = cleanFieldSpec(value, { withName: false, withFlags: false });
            }
        } else if (param.kind === 'columns') {
            const columns = (value || []).filter((c) => c && (c.name || '').trim());
            if (columns.length) {
                params.columns = columns.map((c) =>
                    cleanFieldSpec(c, { withName: true, withFlags: false })
                );
            }
        } else if (param.kind === 'options') {
            const list = Array.isArray(value)
                ? value
                : String(value ?? '')
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean);
            if (list.length) params.options = list;
        } else if (param.kind === 'int' || param.kind === 'number') {
            if (value !== null && value !== undefined && value !== '') {
                const n = Number(value);
                if (!Number.isNaN(n)) {
                    params[param.name] = param.kind === 'int' ? Math.trunc(n) : n;
                }
            }
        } else {
            const s = String(value ?? '').trim();
            if (s) params[param.name] = s;
        }
    }

    const spec = { type: model.type };
    if (withName) spec.name = (model.name || '').trim();
    if (withFlags) {
        spec.required = !!model.required;
        spec.base_field = !!model.base_field;
    }
    if (Object.keys(params).length) spec.params = params;
    return spec;
}

// API field spec -> editable model (options become a comma-separated string,
// nested item/columns recurse).
export function editableFieldSpec(spec) {
    const model = {
        name: spec.name || '',
        type: spec.type,
        required: !!spec.required,
        base_field: !!spec.base_field,
        params: {}
    };
    const meta = FIELD_TYPES[spec.type] || { params: [] };
    const raw = spec.params || {};
    for (const param of meta.params) {
        const value = raw[param.name];
        if (value === undefined || value === null) continue;
        if (param.kind === 'item') {
            model.params.item = editableFieldSpec(value);
        } else if (param.kind === 'columns') {
            model.params.columns = value.map(editableFieldSpec);
        } else if (param.kind === 'options') {
            model.params.options = Array.isArray(value) ? value.join(', ') : String(value);
        } else {
            model.params[param.name] = value;
        }
    }
    return model;
}
