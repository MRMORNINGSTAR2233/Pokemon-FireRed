'use client';

import { useState, useEffect, useCallback } from 'react';
import GameDisplay from '@/components/GameDisplay';
import AgentPanel from '@/components/AgentPanel';
import PartyStatus from '@/components/PartyStatus';
import ControlPanel from '@/components/ControlPanel';
import ReasoningLog from '@/components/ReasoningLog';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useGameState } from '@/hooks/useGameState';

export default function Home() {
    const [isRunning, setIsRunning] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { gameState, updateGameState, agents, logs, addLog } = useGameState();
    const { sendMessage, lastMessage, connectionStatus } = useWebSocket('ws://localhost:8000/ws/game');

    useEffect(() => {
        setIsConnected(connectionStatus === 'connected');
    }, [connectionStatus]);

    useEffect(() => {
        if (lastMessage) {
            if (lastMessage.type === 'game_state') {
                updateGameState(lastMessage.data as Parameters<typeof updateGameState>[0]);
            } else if (lastMessage.type === 'agent_action') {
                addLog(lastMessage.data as Parameters<typeof addLog>[0]);
            }
        }
    }, [lastMessage, updateGameState, addLog]);

    const handleStart = useCallback(async () => {
        try {
            setError(null);
            const response = await fetch('/api/game/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: 'groq/llama-3.3-70b-versatile' }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to start');
            }

            setIsRunning(true);
            addLog({ agent: 'System', action: 'started', details: 'AI Pokemon player started' });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to start game');
        }
    }, [addLog]);

    const handleStop = useCallback(async () => {
        try {
            await fetch('/api/game/stop', { method: 'POST' });
            setIsRunning(false);
            addLog({ agent: 'System', action: 'stopped', details: 'AI Pokemon player stopped' });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to stop game');
        }
    }, [addLog]);

    const handleIterate = useCallback(async () => {
        if (!isRunning) return;

        try {
            const response = await fetch('/api/game/iterate', { method: 'POST' });
            const result = await response.json();

            if (result.game_state) {
                updateGameState(result.game_state);
            }

            if (result.action_taken) {
                addLog({
                    agent: result.action_taken === 'battle' ? 'Battle Agent' : 'Planning Agent',
                    action: result.action_taken,
                    details: result.outcome || 'Action completed',
                });
            }
        } catch (err) {
            console.error('Iteration error:', err);
        }
    }, [isRunning, updateGameState, addLog]);

    return (
        <main className="min-h-screen p-6" style={{ background: 'var(--color-bg-primary)' }}>
            {/* Header */}
            <header style={{ marginBottom: 'var(--spacing-xl)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                        <h1 style={{
                            fontSize: '1.75rem',
                            fontWeight: 700,
                            background: 'linear-gradient(135deg, #6366f1, #ec4899)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                        }}>
                            🎮 AI Pokemon Player
                        </h1>
                        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                            Autonomous Pokemon FireRed player powered by CrewAI + Groq
                        </p>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
                            <span
                                className="status-dot"
                                style={{ background: isConnected ? 'var(--color-success)' : 'var(--color-danger)' }}
                            />
                            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                                {isConnected ? 'Connected' : 'Disconnected'}
                            </span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Error display */}
            {error && (
                <div style={{
                    padding: 'var(--spacing-md)',
                    marginBottom: 'var(--spacing-lg)',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid var(--color-danger)',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--color-danger)',
                }}>
                    ⚠️ {error}
                </div>
            )}

            {/* Main Layout */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 380px',
                gap: 'var(--spacing-xl)',
            }}>
                {/* Left Column - Game Display & Party */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
                    <GameDisplay isRunning={isRunning} />
                    <PartyStatus party={gameState?.party} />
                </div>

                {/* Right Column - Agents, Controls, Logs */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
                    <ControlPanel
                        isRunning={isRunning}
                        onStart={handleStart}
                        onStop={handleStop}
                        onIterate={handleIterate}
                        badges={gameState?.badges || 0}
                        money={gameState?.money || 0}
                    />
                    <AgentPanel agents={agents} isActive={isRunning} />
                    <ReasoningLog logs={logs} />
                </div>
            </div>
        </main>
    );
}
