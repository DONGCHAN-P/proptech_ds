import RULES from './note-replacements.json';
/** Old v7 intervals are provenance only. New voice timing must be measured separately. */
export function resolveNoteReplacement(unitId:string){const r=(RULES.by_unit as Record<string,{replacement_id:string;replacement_visual:string;message_specific_execution:string}>)[unitId];if(!r?.replacement_id)throw Error(`V8 visual mapping missing for ${unitId}; text-only note fallback is disabled`);return r;}
export function assertAllOriginalNotesMapped(){if(RULES.source_interval_count!==37||RULES.mapped_interval_count!==37)throw Error('V8 original note coverage must be 37/37');for(const [unit,r]of Object.entries(RULES.by_unit))if(!r.replacement_id)throw Error('Missing concrete visual mapping: '+unit);return true;}
