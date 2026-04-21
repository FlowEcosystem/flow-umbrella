export const CAPABILITY_ROLES = {
  'self:read':    new Set(['viewer', 'admin', 'superadmin']),
  'self:update':  new Set(['viewer', 'admin', 'superadmin']),
  'admins:read':  new Set(['superadmin']),
  'admins:write': new Set(['superadmin']),
  'instance:read':  new Set(['viewer', 'admin', 'superadmin']),
  'instance:write': new Set(['superadmin']),
  'agents:read':  new Set(['viewer', 'admin', 'superadmin']),
  'agents:write': new Set(['admin', 'superadmin']),
  'groups:read':  new Set(['viewer', 'admin', 'superadmin']),
  'groups:write': new Set(['admin', 'superadmin']),
}

export function roleHasCapability(role, capability) {
  const allowed = CAPABILITY_ROLES[capability]
  if (!allowed) throw new Error(`Unknown capability: ${capability}`)
  return allowed.has(role)
}
