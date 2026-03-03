export const TIERS = [
  { key: 'basic', label: 'Basic' },
  { key: 'standard', label: 'Standard' },
  { key: 'enterprise', label: 'Enterprise' },
]

export const MODULE_NAV = [
  { id: 'basic.detect', tier: 'basic', label: 'Detect', path: 'basic/detect' },
  { id: 'basic.scoring', tier: 'basic', label: 'Scoring', path: 'basic/scoring' },
  { id: 'basic.workflow', tier: 'basic', label: 'Workflow', path: 'basic/workflow' },

  { id: 'standard.ml_detect', tier: 'standard', label: 'ML Detect', path: 'standard/ml-detect' },
  { id: 'standard.explainer', tier: 'standard', label: 'Explainer', path: 'standard/explainer' },
  { id: 'standard.ai_schema', tier: 'standard', label: 'AI Schema', path: 'standard/ai-schema' },
  { id: 'standard.soar_api', tier: 'standard', label: 'SOAR API', path: 'standard/soar-api' },

  { id: 'enterprise.advanced_soar', tier: 'enterprise', label: 'Advanced SOAR', path: 'enterprise/advanced-soar' },
  { id: 'enterprise.deploy', tier: 'enterprise', label: 'Deploy', path: 'enterprise/deploy' },
  { id: 'enterprise.distribute', tier: 'enterprise', label: 'Distribute', path: 'enterprise/distribute' },
  { id: 'enterprise.grep_pipeline', tier: 'enterprise', label: 'Grep Pipeline', path: 'enterprise/grep-pipeline' },

  { id: 'standard.parser_builder', tier: 'standard', label: 'Parser Builder', path: 'standard/parser-builder' },
]