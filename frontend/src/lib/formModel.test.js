import { describe, it, expect } from 'vitest';
import {
    parseLinkQuery,
    isValidDiceExpression,
    defaultValueFor,
    defaultTableRow,
    cleanValue,
    validateField,
    validateForm,
    cleanFormData
} from './formModel.js';

describe('parseLinkQuery', () => {
    it('mirrors backend query forms', () => {
        expect(parseLinkQuery('parent:x-y-z')).toEqual({ parent_guid: 'x-y-z' });
        expect(parseLinkQuery('type:skill', 'd&d5.0')).toEqual({
            system: 'd&d5.0',
            entry_type: 'skill'
        });
        expect(parseLinkQuery('tag:martial')).toEqual({ tag: 'martial' });
        expect(parseLinkQuery('prefix:d&d5.0-rule-')).toEqual({
            guid_prefix: 'd&d5.0-rule-'
        });
        expect(parseLinkQuery('d&d5.0-rule-*')).toEqual({
            guid_prefix: 'd&d5.0-rule-'
        });
        expect(parseLinkQuery('')).toEqual({});
    });
});

describe('isValidDiceExpression', () => {
    it('accepts backend-valid expressions', () => {
        expect(isValidDiceExpression('d20')).toBe(true);
        expect(isValidDiceExpression('2d6+3')).toBe(true);
        expect(isValidDiceExpression('1d8 + 2d4 - 1')).toBe(true);
    });
    it('rejects backend-invalid expressions', () => {
        expect(isValidDiceExpression('5')).toBe(false);
        expect(isValidDiceExpression('1+2')).toBe(false);
        expect(isValidDiceExpression('2d0')).toBe(false);
        expect(isValidDiceExpression('0d6')).toBe(false);
        expect(isValidDiceExpression('banana')).toBe(false);
        expect(isValidDiceExpression('')).toBe(false);
    });
});

describe('defaultValueFor', () => {
    it('gives sensible empties per type', () => {
        expect(defaultValueFor({ type: 'text' })).toBe('');
        expect(defaultValueFor({ type: 'number' })).toBe(null);
        expect(defaultValueFor({ type: 'checkbox' })).toBe(false);
        expect(defaultValueFor({ type: 'compendium_link_list' })).toEqual([]);
        expect(defaultValueFor({ type: 'grant' })).toEqual([]);
        expect(defaultValueFor({ type: 'list', item: { type: 'text' } })).toEqual([]);
    });

    it('seeds minItems list entries and minRows table rows', () => {
        expect(
            defaultValueFor({ type: 'list', item: { type: 'text' }, minItems: 2 })
        ).toEqual(['', '']);
        const table = {
            type: 'table',
            minRows: 1,
            columns: [
                { name: 'level', type: 'number' },
                { name: 'feature', type: 'text' }
            ]
        };
        expect(defaultValueFor(table)).toEqual([{ level: null, feature: '' }]);
        expect(defaultTableRow(table)).toEqual({ level: null, feature: '' });
    });

    it('seeds choice with the schema query', () => {
        expect(defaultValueFor({ type: 'choice', query: 'type:skill' })).toEqual({
            choose: 1,
            query: 'type:skill',
            options: []
        });
    });
});

describe('cleanValue', () => {
    it('coerces numbers and nulls empty optionals', () => {
        expect(cleanValue({ type: 'number' }, '5')).toBe(5);
        expect(cleanValue({ type: 'number' }, '')).toBe(null);
        expect(cleanValue({ type: 'text' }, '')).toBe(null);
        expect(cleanValue({ type: 'select' }, '')).toBe(null);
        expect(cleanValue({ type: 'compendium_link' }, '')).toBe(null);
        expect(cleanValue({ type: 'dice_expression' }, ' 2d6+3 ')).toBe('2d6+3');
    });

    it('recurses into lists and tables', () => {
        expect(
            cleanValue({ type: 'list', item: { type: 'number' } }, ['1', '2'])
        ).toEqual([1, 2]);
        const table = {
            type: 'table',
            columns: [
                { name: 'level', type: 'number' },
                { name: 'feature', type: 'text' }
            ]
        };
        expect(cleanValue(table, [{ level: '3', feature: 'Rage' }])).toEqual([
            { level: 3, feature: 'Rage' }
        ]);
    });

    it('builds a ChoiceSpec and nulls untouched optional choices', () => {
        expect(
            cleanValue(
                { type: 'choice' },
                { choose: '2', query: 'type:skill', options: [] }
            )
        ).toEqual({ choose: 2, query: 'type:skill' });
        expect(
            cleanValue({ type: 'choice' }, { choose: 1, query: '', options: [] })
        ).toBe(null);
        expect(
            cleanValue(
                { type: 'choice' },
                { choose: 1, query: '', options: ['a-b-c'] }
            )
        ).toEqual({ choose: 1, options: ['a-b-c'] });
    });
});

describe('validateField', () => {
    it('requires required fields', () => {
        expect(validateField({ type: 'text', required: true }, '')).toBe(
            'This field is required'
        );
        expect(validateField({ type: 'text', required: false }, '')).toBe(null);
        expect(validateField({ type: 'grant', required: true }, [])).toBe(
            'This field is required'
        );
    });

    it('checks numeric bounds', () => {
        expect(validateField({ type: 'number', min: 1, max: 9 }, '0')).toMatch(
            /at least 1/
        );
        expect(validateField({ type: 'number', min: 1, max: 9 }, '10')).toMatch(
            /at most 9/
        );
        expect(validateField({ type: 'number', min: 1, max: 9 }, '5')).toBe(null);
    });

    it('checks dice expressions', () => {
        expect(validateField({ type: 'dice_expression' }, '1d8')).toBe(null);
        expect(validateField({ type: 'dice_expression' }, 'nope')).toMatch(
            /Invalid dice expression/
        );
    });

    it('checks list bounds and item validity', () => {
        const field = { type: 'list', item: { type: 'number', min: 1 }, minItems: 1 };
        expect(validateField({ ...field, required: true }, [])).toBe(
            'This field is required'
        );
        expect(validateField(field, ['0'])).toMatch(/Item 1:/);
        expect(validateField(field, ['2'])).toBe(null);
    });

    it('checks table bounds and required cells', () => {
        const table = {
            type: 'table',
            minRows: 1,
            columns: [
                { name: 'level', type: 'number', min: 1, max: 20 },
                { name: 'feature', type: 'text' }
            ]
        };
        expect(validateField(table, [{ level: '1', feature: '' }])).toMatch(
            /Row 1, feature/
        );
        expect(validateField(table, [{ level: '99', feature: 'Rage' }])).toMatch(
            /Row 1, level/
        );
        expect(validateField(table, [{ level: '3', feature: 'Rage' }])).toBe(null);
    });

    it('checks choice coherence', () => {
        const field = { type: 'choice', required: true };
        expect(validateField(field, { choose: 0, query: 'type:skill' })).toMatch(
            /at least 1/
        );
        expect(
            validateField(field, { choose: 2, options: ['only-one'], query: '' })
        ).toMatch(/at least as many options/);
        expect(
            validateField(field, { choose: 2, query: 'type:skill', options: [] })
        ).toBe(null);
    });

    it('checks grant bounds', () => {
        const field = { type: 'grant', minItems: 2 };
        expect(validateField(field, ['a'])).toMatch(/at least 2/);
        expect(validateField(field, ['a', 'b'])).toBe(null);
    });
});

describe('validateForm / cleanFormData', () => {
    const fields = [
        { name: 'name', type: 'text', required: true },
        { name: 'hit_die', type: 'dice_expression', required: true },
        { name: 'weight', type: 'number', required: false }
    ];

    it('collects only failing fields', () => {
        const errors = validateForm(fields, {
            name: 'Barbarian',
            hit_die: 'bad',
            weight: ''
        });
        expect(Object.keys(errors)).toEqual(['hit_die']);
    });

    it('cleans the whole payload', () => {
        expect(
            cleanFormData(fields, { name: 'Axe', hit_die: ' 1d12 ', weight: '3.5' })
        ).toEqual({ name: 'Axe', hit_die: '1d12', weight: 3.5 });
    });
});
