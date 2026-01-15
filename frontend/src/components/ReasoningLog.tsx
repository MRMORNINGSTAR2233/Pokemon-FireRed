'use client';

import { useRef, useEffect } from 'react';

interface LogEntry {
    agent: string;
    action: string;
    details: string;
    timestamp?: string;
}

interface ReasoningLogProps {
    logs: LogEntry[];
}

const getLogClass = (action: string): string => {
    if (action.includes('error') || action.includes('fail')) return 'error';
    if (action.includes('think') || action.includes('plan')) return 'thinking';
    if (action.includes('success') || action.includes('won')) return 'success';
    return 'action';
};

const getAgentIcon = (agent: string): string => {
    if (agent.includes('Planning')) return '🎯';
    if (agent.includes('Navigation')) return '🚶';
    if (agent.includes('Battle')) return '⚔️';
    if (agent.includes('Memory')) return '🧠';
    if (agent.includes('Critique')) return '📊';
    if (agent.includes('System')) return '⚙️';
    return '🤖';
};

export default function ReasoningLog({ logs }: ReasoningLogProps) {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="card" style={{
            padding: 'var(--spacing-lg)',
            display: 'flex',
            flexDirection: 'column',
            maxHeight: '300px',
        }}>
            <h2 style={{
                fontSize: '1rem',
                fontWeight: 600,
                marginBottom: 'var(--spacing-md)',
                color: 'var(--color-text-primary)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-sm)',
            }}>
                <span>📝</span> Agent Reasoning
            </h2>

            <div
                ref={scrollRef}
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--spacing-xs)',
                }}
            >
                {logs.length > 0 ? (
                    logs.map((log, index) => (
                        <div
                            key={index}
                            className={`log-entry ${getLogClass(log.action)} fade-in`}
                        >
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 'var(--spacing-xs)',
                                marginBottom: 'var(--spacing-xs)',
                            }}>
                                <span>{getAgentIcon(log.agent)}</span>
                                <span style={{
                                    fontWeight: 600,
                                    color: 'var(--color-primary-light)',
                                    fontSize: '0.7rem',
                                }}>
                                    {log.agent}
                                </span>
                                <span style={{ color: 'var(--color-text-muted)' }}>•</span>
                                <span style={{
                                    color: 'var(--color-text-muted)',
                                    fontSize: '0.65rem',
                                }}>
                                    {log.timestamp || new Date().toLocaleTimeString()}
                                </span>
                            </div>
                            <div style={{
                                color: 'var(--color-text-secondary)',
                                paddingLeft: 'var(--spacing-lg)',
                            }}>
                                {log.details}
                            </div>
                        </div>
                    ))
                ) : (
                    <div style={{
                        padding: 'var(--spacing-xl)',
                        textAlign: 'center',
                        color: 'var(--color-text-muted)',
                        fontSize: '0.875rem',
                    }}>
                        No activity yet. Start the AI player to see reasoning logs.
                    </div>
                )}
            </div>
        </div>
    );
}
