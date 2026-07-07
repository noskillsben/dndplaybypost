import { describe, it, expect } from 'vitest';
import {
    FIELD_TYPES,
    emptyFieldSpec,
    nameFieldSpec,
    cleanFieldSpec,
    editableFieldSpec
} from './templateSpec.js';

describe('FIELD_TYPES', () => {
    it('covers all 16 backend field types', () => {
        expect(Object.keys(FIELD_TYPES)).toHaveLength(16);
        expect(FIELD_TYPES.short_text).toBeDefined();
        expect(FIELD_TYPES.grant).toBeDefined();
    });
});

describe('emptyFieldSpec', () => {
    it('defaults to short_text with empty params', () => {
        expect(emptyFieldSpec()).toEqual({
            name: '',
            type: 'short_text',
            required: false,
            base_field: false,
            params: {}
        });
    });
});

describe('nameFieldSpec', () => {
    it('matches the backend auto name field', () => {
        expect(nameFieldSpec()).toEqual({
            name: 'name',
            type: 'short_text',
            required: true,
            base_field: true,
            params: { max_len: 200 }
        });
    });
});

describe('cleanFieldSpec', () => {
    it('trims name and drops empty params', () => {
        const spec = cleanFieldSpec({
            name: '  hp  ',
            type: 'integer',
            required: true,
            base_field: false,
            params: { min_val: '', max_val: null }
        });
        expect(spec).toEqual({ type: 'integer', name: 'hp', required: true, base_field: false });
    });

    it('coerces int params from strings and truncates', () => {
        const spec = cleanFieldSpec({
            name: 'level',
            type: 'integer',
            params: { min_val: '1', max_val: '20.7' }
        });
        expect(spec.params).toEqual({ min_val: 1, max_val: 20 });
    });

    it('keeps decimal params as numbers', () => {
        const spec = cleanFieldSpec({
            name: 'weight',
            type: 'decimal',
            params: { min_val: '0.5', step: '0.25' }
        });
        expect(spec.params).toEqual({ min_val: 0.5, step: 0.25 });
    });

    it('drops NaN numeric params', () => {
        const spec = cleanFieldSpec({
            name: 'n',
            type: 'integer',
            params: { min_val: 'abc' }
        });
        expect(spec.params).toBeUndefined();
    });

    it('splits comma-separated options', () => {
        const spec = cleanFieldSpec({
            name: 'rarity',
            type: 'select',
            params: { options: ' common, rare ,legendary,, ' }
        });
        expect(spec.params.options).toEqual(['common', 'rare', 'legendary']);
    });

    it('accepts options already given as array', () => {
        const spec = cleanFieldSpec({
            name: 'rarity',
            type: 'select',
            params: { options: ['a', 'b'] }
        });
        expect(spec.params.options).toEqual(['a', 'b']);
    });

    it('recurses into list_of item without name/flags', () => {
        const spec = cleanFieldSpec({
            name: 'notes',
            type: 'list_of',
            required: false,
            params: {
                item: { name: 'ignored', type: 'short_text', required: true, params: { max_len: '50' } },
                max_items: '10'
            }
        });
        expect(spec.params.item).toEqual({ type: 'short_text', params: { max_len: 50 } });
        expect(spec.params.max_items).toBe(10);
    });

    it('recurses into table columns keeping names, dropping blank ones', () => {
        const spec = cleanFieldSpec({
            name: 'levels',
            type: 'table',
            params: {
                columns: [
                    { name: 'level', type: 'integer', required: true, params: { min_val: '1' } },
                    { name: '   ', type: 'short_text', params: {} }
                ],
                min_rows: '1'
            }
        });
        expect(spec.params.columns).toEqual([
            { type: 'integer', name: 'level', params: { min_val: 1 } }
        ]);
        expect(spec.params.min_rows).toBe(1);
    });

    it('omits name and flags when disabled', () => {
        const spec = cleanFieldSpec(
            { name: 'x', type: 'short_text', required: true, params: {} },
            { withName: false, withFlags: false }
        );
        expect(spec).toEqual({ type: 'short_text' });
    });

    it('throws on unknown field type', () => {
        expect(() => cleanFieldSpec({ name: 'x', type: 'bogus', params: {} })).toThrow(
            'Unknown field type: bogus'
        );
    });
});

describe('editableFieldSpec', () => {
    it('joins options into a comma-separated string', () => {
        const model = editableFieldSpec({
            name: 'rarity',
            type: 'select',
            required: true,
            params: { options: ['common', 'rare'] }
        });
        expect(model.params.options).toBe('common, rare');
        expect(model.required).toBe(true);
        expect(model.base_field).toBe(false);
    });

    it('recurses into item and columns', () => {
        const model = editableFieldSpec({
            name: 'levels',
            type: 'table',
            params: {
                columns: [{ name: 'level', type: 'integer', params: { min_val: 1 } }],
                min_rows: 1
            }
        });
        expect(model.params.columns[0].name).toBe('level');
        expect(model.params.columns[0].params.min_val).toBe(1);

        const list = editableFieldSpec({
            name: 'notes',
            type: 'list_of',
            params: { item: { type: 'short_text', params: { max_len: 50 } } }
        });
        expect(list.params.item.type).toBe('short_text');
        expect(list.params.item.params.max_len).toBe(50);
    });

    it('round-trips clean -> editable -> clean', () => {
        const original = {
            name: 'levels',
            type: 'table',
            required: true,
            base_field: false,
            params: {
                columns: [
                    { name: 'level', type: 'integer', params: { min_val: 1, max_val: 20 } },
                    { name: 'feature', type: 'short_text', params: { max_len: 100 } }
                ],
                min_rows: 1
            }
        };
        const roundTripped = cleanFieldSpec(editableFieldSpec(original));
        expect(roundTripped).toEqual(original);
    });
});
