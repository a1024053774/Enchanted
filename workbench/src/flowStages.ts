export const flowStages = [
  { id: 'implementation', label: '认领与实现' }, { id: 'delivery', label: '交付' },
  { id: 'checks', label: '机械检查' }, { id: 'review', label: '独立审查' }, { id: 'integration', label: '集成' },
] as const;
export type FlowStage = typeof flowStages[number]['id'];
