'use client';

interface Agent {
    name: string;
    role: string;
    status: 'active' | 'idle' | 'busy';
    icon: string;
}

interface AgentPanelProps {
    agents: Agent[];
    isActive: boolean;
}

const DEFAULT_AGENTS: Agent[] = [
    { name: 'Planning Agent', role: 'Strategic Planner', status: 'idle', icon: '🎯' },
    { name: 'Navigation Agent', role: 'Overworld Navigator', status: 'idle', icon: '🚶' },
    { name: 'Battle Agent', role: 'Combat Strategist', status: 'idle', icon: '⚔️' },
    { name: 'Memory Agent', role: 'Memory Manager', status: 'idle', icon: '🧠' },
    { name: 'Critique Agent', role: 'Task Evaluator', status: 'idle', icon: '📊' },
];

export default function AgentPanel({ agents = DEFAULT_AGENTS, isActive }: AgentPanelProps) {
    const displayAgents = agents.length > 0 ? agents : DEFAULT_AGENTS;

    return (
        <div className="card" style={{ padding: 'var(--spacing-lg)' }}>
            <h2 style={{
                fontSize: '1rem',
                fontWeight: 600,
                marginBottom: 'var(--spacing-md)',
                color: 'var(--color-text-primary)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-sm)',
            }}>
                <span>🤖</span> AI Agents
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
                {displayAgents.map((agent, index) => (
                    <div
                        key={agent.name}
                        className={`agent-card ${isActive ? 'active' : ''}`}
                        style={{
                            animation: `slideIn 0.3s ease forwards ${index * 0.1}s`,
                            opacity: 0,
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                            <span style={{ fontSize: '1.25rem' }}>{agent.icon}</span>
                            <div style={{ flex: 1 }}>
                                <div style={{
                                    fontSize: '0.875rem',
                                    fontWeight: 600,
                                    color: 'var(--color-text-primary)',
                                }}>
                                    {agent.name}
                                </div>
                                <div style={{
                                    fontSize: '0.75rem',
                                    color: 'var(--color-text-secondary)',
                                }}>
                                    {agent.role}
                                </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-xs)' }}>
                                <span
                                    className="status-dot"
                                    style={{
                                        background: isActive ? 'var(--color-success)' : 'var(--color-text-muted)',
                                    }}
                                />
                                <span style={{
                                    fontSize: '0.625rem',
                                    color: 'var(--color-text-muted)',
                                    textTransform: 'uppercase',
                                }}>
                                    {isActive ? 'Active' : 'Idle'}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
