// Pure helpers behind DynamicForm v2: initial values, submission cleaning and
// client-side validation for the form schemas served by /api/schemas/*.
// Mirrors backend behavior in core/field_types.py.

// Mirrors backend core/field_types.py parse_link_query
export function parseLinkQuery(query, system) {
    if (!query) return {};
    if (query.startsWith('parent:')) return { parent_guid: query.substring(7) };
    if (query.startsWith('type:')) return { system, entry_type: query.substring(5) };
    if (query.startsWith('tag:')) return { tag: query.substring(4) };
    if (query.startsWith('prefix:')) return { guid_prefix: query.substring(7) };
    // Legacy glob form: "d&d5.0-rule-*"
    return { guid_prefix: query.replace(/\*$/, '') };
}

// Mirrors backend _DICE_EXPR_RE + "at least one die term" rule
const DICE_EXPR_RE = /^\s*(\d*[dD]\d+|\d+)(\s*[+-]\s*(\d*[dD]\d+|\d+))*\s*$/;
const DICE_TERM_RE = /\d*[dD]\d+/g;

export function isValidDiceExpression(value) {
    if (typeof value !== 'string' || !DICE_EXPR_RE.test(value)) return false;
    const terms = value.match(DICE_TERM_RE) || [];
    if (!terms.length) return false;
    for (const term of terms) {
        const [count, faces] = term.toLowerCase().split('d');
        if (count && parseInt(count, 10) < 1) return false;
        if (parseInt(faces, 10) < 1) return false;
    }
    return true;
}

export function defaultValueFor(field) {
    switch (field.type) {
        case 'number':
            return null;
        case 'checkbox':
            return false;
        case 'compendium_link_list':
        case 'grant':
            return [];
        case 'list': {
            const n = field.minItems || 0;
            return Array.from({ length: n }, () => defaultValueFor(field.item));
        }
        case 'table': {
            const n = field.minRows || 0;
            return Array.from({ length: n }, () => defaultTableRow(field));
        }
        case 'choice':
            return { choose: 1, query: field.query || '', options: [] };
        case 'select':
        case 'compendium_link':
        case 'parent_link':
        case 'text':
        case 'textarea':
        case 'markdown':
        case 'dice_expression':
        default:
            return '';
    }
}

export function defaultTableRow(field) {
    const row = {};
    for (const col of field.columns || []) {
        row[col.name] = defaultValueFor(col);
    }
    return row;
}

function isEmpty(value) {
    return (
        value === null ||
        value === undefined ||
        value === '' ||
        (Array.isArray(value) && value.length === 0)
    );
}

// Value as edited -> value as submitted. Empty optional values become null;
// numbers are coerced; lists/tables recurse.
export function cleanValue(field, value) {
    switch (field.type) {
        case 'number': {
            if (value === null || value === undefined || value === '') return null;
            const n = Number(value);
            return Number.isNaN(n) ? null : n;
        }
        case 'checkbox':
            return !!value;
        case 'select':
        case 'compendium_link':
        case 'parent_link':
            return value === '' ? null : value;
        case 'text':
        case 'textarea':
        case 'markdown':
            return value === '' ? null : value;
        case 'dice_expression': {
            const s = String(value ?? '').trim();
            return s === '' ? null : s;
        }
        case 'compendium_link_list':
        case 'grant':
            return Array.isArray(value) ? value : [];
        case 'list':
            return (value || []).map((item) => cleanValue(field.item, item));
        case 'table':
            return (value || []).map((row) => {
                const out = {};
                for (const col of field.columns || []) {
                    out[col.name] = cleanValue(col, row ? row[col.name] : null);
                }
                return out;
            });
        case 'choice': {
            const v = value || {};
            const query = String(v.query ?? '').trim();
            const options = Array.isArray(v.options) ? v.options : [];
            const choose = Number(v.choose);
            if (!query && !options.length && !field.required) return null;
            const spec = { choose: Number.isNaN(choose) ? null : choose };
            if (options.length) spec.options = options;
            if (query) spec.query = query;
            return spec;
        }
        default:
            return value;
    }
}

// Returns an error string for one field's edited value, or null.
export function validateField(field, value) {
    const cleaned = cleanValue(field, value);

    if (isEmpty(cleaned)) {
        if (field.required) return 'This field is required';
        return null;
    }

    switch (field.type) {
        case 'number': {
            if (field.min !== undefined && cleaned < field.min)
                return `Must be at least ${field.min}`;
            if (field.max !== undefined && cleaned > field.max)
                return `Must be at most ${field.max}`;
            return null;
        }
        case 'dice_expression':
            return isValidDiceExpression(cleaned)
                ? null
                : `Invalid dice expression (e.g. "2d6+3")`;
        case 'list': {
            if (field.minItems !== undefined && cleaned.length < field.minItems)
                return `Needs at least ${field.minItems} item${field.minItems === 1 ? '' : 's'}`;
            if (field.maxItems !== undefined && cleaned.length > field.maxItems)
                return `Allows at most ${field.maxItems} item${field.maxItems === 1 ? '' : 's'}`;
            for (let i = 0; i < cleaned.length; i++) {
                const itemError = validateField(
                    { ...field.item, required: true },
                    (value || [])[i]
                );
                if (itemError) return `Item ${i + 1}: ${itemError}`;
            }
            return null;
        }
        case 'table': {
            if (field.minRows !== undefined && cleaned.length < field.minRows)
                return `Needs at least ${field.minRows} row${field.minRows === 1 ? '' : 's'}`;
            if (field.maxRows !== undefined && cleaned.length > field.maxRows)
                return `Allows at most ${field.maxRows} row${field.maxRows === 1 ? '' : 's'}`;
            for (let i = 0; i < cleaned.length; i++) {
                for (const col of field.columns || []) {
                    const colRequired = !['compendium_link', 'parent_link'].includes(col.type);
                    const cellError = validateField(
                        { ...col, required: colRequired },
                        (value || [])[i]?.[col.name]
                    );
                    if (cellError) return `Row ${i + 1}, ${col.name}: ${cellError}`;
                }
            }
            return null;
        }
        case 'grant': {
            if (field.minItems !== undefined && cleaned.length < field.minItems)
                return `Needs at least ${field.minItems} item${field.minItems === 1 ? '' : 's'}`;
            if (field.maxItems !== undefined && cleaned.length > field.maxItems)
                return `Allows at most ${field.maxItems} item${field.maxItems === 1 ? '' : 's'}`;
            return null;
        }
        case 'choice': {
            if (!cleaned.choose || cleaned.choose < 1)
                return 'Choose must be at least 1';
            if (!cleaned.query && !cleaned.options)
                return 'Provide a query or pick options';
            if (cleaned.options && cleaned.options.length < cleaned.choose)
                return 'Pick at least as many options as "choose"';
            return null;
        }
        default:
            return null;
    }
}

// Validate all fields; returns {fieldName: error} for failures only.
export function validateForm(fields, data) {
    const errors = {};
    for (const field of fields) {
        const error = validateField(field, data[field.name]);
        if (error) errors[field.name] = error;
    }
    return errors;
}

// Build the submission payload for the whole form.
export function cleanFormData(fields, data) {
    const out = {};
    for (const field of fields) {
        out[field.name] = cleanValue(field, data[field.name]);
    }
    return out;
}
