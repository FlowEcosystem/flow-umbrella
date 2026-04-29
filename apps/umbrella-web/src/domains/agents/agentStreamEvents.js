// Module-level reactive state — written by useGlobalStream, read by useAgentsPage.
export const lastAgentUpdate   = ref(null)   // full AgentRead from SSE
export const agentsNeedRefresh = ref(false)  // set true when any agent goes offline
