export const CAPABILITY_ROLES = {
  'self:read':    new Set(['viewer', 'admin', 'superadmin']),
  'self:update':  new Set(['viewer', 'admin', 'superadmin']),
  'admins:read':  new Set(['superadmin']),
  'admins:write': new Set(['superadmin']),
}

export function roleHasCapability(role, capability) {
  const allowed = CAPABILITY_ROLES[capability]
  if (!allowed) throw new Error(`Unknown capability: ${capability}`)
  return allowed.has(role)
}
