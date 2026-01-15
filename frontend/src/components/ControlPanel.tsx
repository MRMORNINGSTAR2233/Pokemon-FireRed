'use client';

interface ControlPanelProps {
    isRunning: boolean;
    onStart: () => void;
    onStop: () => void;
    onIterate: () => void;
    badges: number;
    money: number;
}

export default function ControlPanel({
    isRunning,
    onStart,
    onStop,
    onIterate,
    badges,
    money,
}: ControlPanelProps) {
    const badgeCount = typeof badges === 'number' ? (badges.toString(2).match(/1/g) || []).length : 0;

    return (
        <div className="card glow" style={{ padding: 'var(--spacing-lg)' }}>
            <h2 style={{
                fontSize: '1rem',
                fontWeight: 600,
                marginBottom: 'var(--spacing-md)',
                color: 'var(--color-text-primary)',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-sm)',
            }}>
                <span>🎛️</span> Control Panel
            </h2>

            {/* Status Display */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: 'var(--spacing-md)',
                marginBottom: 'var(--spacing-lg)',
            }}>
                <div style={{
                    padding: 'var(--spacing-md)',
                    background: 'var(--color-bg-tertiary)',
                    borderRadius: 'var(--radius-md)',
                    textAlign: 'center',
                }}>
                    <div style={{ fontSize: '1.5rem' }}>🏅</div>
                    <div style={{
                        fontSize: '1.25rem',
                        fontWeight: 700,
                        color: 'var(--color-text-primary)',
                    }}>
                        {badgeCount}/8
                    </div>
                    <div style={{ fontSize: '0.625rem', color: 'var(--color-text-secondary)' }}>
                        BADGES
                    </div>
                </div>

                <div style={{
                    padding: 'var(--spacing-md)',
                    background: 'var(--color-bg-tertiary)',
                    borderRadius: 'var(--radius-md)',
                    textAlign: 'center',
                }}>
                    <div style={{ fontSize: '1.5rem' }}>💰</div>
                    <div style={{
                        fontSize: '1.25rem',
                        fontWeight: 700,
                        color: 'var(--color-text-primary)',
                    }}>
                        ¥{money.toLocaleString()}
                    </div>
                    <div style={{ fontSize: '0.625rem', color: 'var(--color-text-secondary)' }}>
                        MONEY
                    </div>
                </div>
            </div>

            {/* Control Buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
                {!isRunning ? (
                    <button className="btn btn-success" onClick={onStart} style={{ width: '100%' }}>
                        ▶️ Start AI Player
                    </button>
                ) : (
                    <>
                        <button className="btn btn-danger" onClick={onStop} style={{ width: '100%' }}>
                            ⏹️ Stop
                        </button>
                        <button className="btn btn-primary" onClick={onIterate} style={{ width: '100%' }}>
                            ⏩ Run Iteration
                        </button>
                    </>
                )}
            </div>

            {/* Status Indicator */}
            <div style={{
                marginTop: 'var(--spacing-md)',
                padding: 'var(--spacing-sm)',
                background: isRunning
                    ? 'rgba(34, 197, 94, 0.1)'
                    : 'var(--color-bg-tertiary)',
                borderRadius: 'var(--radius-sm)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 'var(--spacing-sm)',
            }}>
                <span
                    className="status-dot"
                    style={{
                        background: isRunning ? 'var(--color-success)' : 'var(--color-text-muted)',
                    }}
                />
                <span style={{
                    fontSize: '0.75rem',
                    color: isRunning ? 'var(--color-success)' : 'var(--color-text-muted)',
                    fontWeight: 600,
                }}>
                    {isRunning ? 'AI Active' : 'Stopped'}
                </span>
            </div>
        </div>
    );
}
