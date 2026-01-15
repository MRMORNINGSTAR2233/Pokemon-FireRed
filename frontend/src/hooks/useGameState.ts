'use client';

import { useState, useCallback } from 'react';

interface Pokemon {
    nickname: string;
    level: number;
    current_hp: number;
    max_hp: number;
    hp_percentage: number;
    is_fainted: boolean;
}

interface Party {
    party_count: number;
    pokemon: Pokemon[];
    total_hp_percentage: number;
}

interface Position {
    x: number;
    y: number;
    map_bank: number;
    map_number: number;
}

interface GameState {
    party: Party;
    position: Position;
    badges: number;
    badge_count: number;
    money: number;
    in_battle: boolean;
}

interface Agent {
    name: string;
    role: string;
    status: 'active' | 'idle' | 'busy';
    icon: string;
}

interface LogEntry {
    agent: string;
    action: string;
    details: string;
    timestamp: string;
}

const DEFAULT_AGENTS: Agent[] = [
    { name: 'Planning Agent', role: 'Strategic Planner', status: 'idle', icon: '🎯' },
    { name: 'Navigation Agent', role: 'Overworld Navigator', status: 'idle', icon: '🚶' },
    { name: 'Battle Agent', role: 'Combat Strategist', status: 'idle', icon: '⚔️' },
    { name: 'Memory Agent', role: 'Memory Manager', status: 'idle', icon: '🧠' },
    { name: 'Critique Agent', role: 'Task Evaluator', status: 'idle', icon: '📊' },
];

export function useGameState() {
    const [gameState, setGameState] = useState<GameState | null>(null);
    const [agents, setAgents] = useState<Agent[]>(DEFAULT_AGENTS);
    const [logs, setLogs] = useState<LogEntry[]>([]);

    const updateGameState = useCallback((newState: GameState) => {
        setGameState(newState);
    }, []);

    const updateAgentStatus = useCallback((agentName: string, status: 'active' | 'idle' | 'busy') => {
        setAgents((prev) =>
            prev.map((agent) =>
                agent.name === agentName ? { ...agent, status } : agent
            )
        );
    }, []);

    const addLog = useCallback((entry: Omit<LogEntry, 'timestamp'>) => {
        setLogs((prev) => [
            ...prev.slice(-50), // Keep last 50 entries
            { ...entry, timestamp: new Date().toLocaleTimeString() },
        ]);
    }, []);

    const clearLogs = useCallback(() => {
        setLogs([]);
    }, []);

    return {
        gameState,
        updateGameState,
        agents,
        updateAgentStatus,
        logs,
        addLog,
        clearLogs,
    };
}
