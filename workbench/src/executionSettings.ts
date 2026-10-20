export const executionRoles = ['worker', 'reviewer', 'monitor', 'ideation', 'executor'] as const;
export type ExecutionRole = typeof executionRoles[number];
export type ExecutionSelection = { model: string; effort: string; fast: boolean };
export type ExecutionOverrides = Partial<ExecutionSelection>;
export const factoryExecution: Readonly<ExecutionSelection> = Object.freeze({ model: 'gpt-6.1-sol', effort: 'high', fast: false });

// Check transport shape only. The native CLI owns supported model/effort values.
export function executionOverrides(value: unknown): ExecutionOverrides {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('invalid_execution_settings');
  const result: ExecutionOverrides = {};
  for (const [key, item] of Object.entries(value)) {
    if (key === 'fast' && typeof item === 'boolean') result.fast = item;
    else if ((key === 'model' || key === 'effort') && typeof item === 'string' && item.trim() && !/[\0\r\n]/.test(item)) result[key] = item;
    else throw new Error('invalid_execution_settings');
  }
  return result;
}
export function executionRole(value: unknown): ExecutionRole {
  if (!executionRoles.includes(value as ExecutionRole)) throw new Error('invalid_execution_role');
  return value as ExecutionRole;
}
