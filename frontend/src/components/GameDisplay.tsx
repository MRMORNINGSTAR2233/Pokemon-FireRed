'use client';

import { useState, useEffect, useCallback } from 'react';

interface GameDisplayProps {
    isRunning: boolean;
}

export default function GameDisplay({ isRunning }: GameDisplayProps) {
    const [screenImage, setScreenImage] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const fetchScreen = useCallback(async () => {
        if (!isRunning) return;

        try {
            const response = await fetch('/api/game/screen');
            if (response.ok) {
                const data = await response.json();
                setScreenImage(`data:image/png;base64,${data.image}`);
            }
        } catch (err) {
            console.error('Failed to fetch screen:', err);
        }
    }, [isRunning]);

    useEffect(() => {
        if (isRunning) {
            fetchScreen();
            const interval = setInterval(fetchScreen, 500); // Update every 500ms
            return () => clearInterval(interval);
        } else {
            setScreenImage(null);
        }
    }, [isRunning, fetchScreen]);

    return (
        <div className="card" style={{ padding: 'var(--spacing-lg)' }}>
            <h2 style={{
                fontSize: '1rem',
                fontWeight: 600,
                marginBottom: 'var(--spacing-md)',
                color: 'var(--color-text-primary)'
            }}>
                Game Display
            </h2>

            <div className="game-screen">
                {screenImage ? (
                    <img src={screenImage} alt="Pokemon FireRed" />
                ) : (
                    <div style={{
                        width: '100%',
                        height: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexDirection: 'column',
                        gap: 'var(--spacing-md)',
                        color: 'var(--color-text-muted)',
                    }}>
                        <span style={{ fontSize: '3rem' }}>🎮</span>
                        <span style={{ fontSize: '0.875rem' }}>
                            {loading ? 'Connecting...' : 'Start the game to see display'}
                        </span>
                    </div>
                )}
            </div>

            <div style={{
                marginTop: 'var(--spacing-md)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                color: 'var(--color-text-secondary)',
                fontSize: '0.75rem',
            }}>
                <span>Pokemon FireRed</span>
                <span>GBA • 240×160</span>
            </div>
        </div>
    );
}
