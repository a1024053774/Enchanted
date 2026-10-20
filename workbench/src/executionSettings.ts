export const executionRoles = ['worker', 'reviewer', 'monitor', 'ideation', 'executor'] as const;
export type ExecutionRole = typeof executionRoles[number];
export type ExecutionSelection = { model: string; effort: string; fast: boolean };
export type ExecutionOverrides = Partial<ExecutionSelection>;
const codexFactory = Object.freeze({ model: 'gpt-6.1-sol', effort: 'high', fast: false });
const claudeFactory = Object.freeze({ model: 'claude-haiku-5-5', effort: 'low', fast: false });
export const factoryExecution: Readonly<Record<ExecutionRole, Readonly<ExecutionSelection>>> = Object.freeze({
  worker: codexFactory, reviewer: codexFactory, monitor: codexFactory,
  ideation: claudeFactory, executor: claudeFactory,
});

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
