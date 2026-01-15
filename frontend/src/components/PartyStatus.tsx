'use client';

interface Pokemon {
    nickname: string;
    level: number;
    current_hp: number;
    max_hp: number;
    hp_percentage: number;
    is_fainted: boolean;
    types?: string[];
}

interface Party {
    party_count: number;
    pokemon: Pokemon[];
    total_hp_percentage: number;
}

interface PartyStatusProps {
    party?: Party;
}

// Pokemon type to color mapping
const TYPE_COLORS: Record<string, string> = {
    Fire: 'var(--type-fire)',
    Water: 'var(--type-water)',
    Grass: 'var(--type-grass)',
    Electric: 'var(--type-electric)',
    Psychic: 'var(--type-psychic)',
    Rock: 'var(--type-rock)',
    Ground: 'var(--type-ground)',
    Normal: '#a8a29e',
    Flying: '#93c5fd',
    Bug: '#84cc16',
    Poison: '#a855f7',
    Ghost: '#8b5cf6',
    Fighting: '#ef4444',
    Ice: '#67e8f9',
    Dragon: '#7c3aed',
    Dark: '#57534e',
    Steel: '#9ca3af',
};

const getHPClass = (percentage: number): string => {
    if (percentage > 50) return 'hp-high';
    if (percentage > 20) return 'hp-medium';
    return 'hp-low';
};

export default function PartyStatus({ party }: PartyStatusProps) {
    const pokemon = party?.pokemon || [];

    return (
        <div className="card" style={{ padding: 'var(--spacing-lg)' }}>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 'var(--spacing-md)',
            }}>
                <h2 style={{
                    fontSize: '1rem',
                    fontWeight: 600,
                    color: 'var(--color-text-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--spacing-sm)',
                }}>
                    <span>⚡</span> Party Pokemon
                </h2>

                {party && (
                    <span style={{
                        fontSize: '0.75rem',
                        color: 'var(--color-text-secondary)',
                        background: 'var(--color-bg-tertiary)',
                        padding: 'var(--spacing-xs) var(--spacing-sm)',
                        borderRadius: 'var(--radius-sm)',
                    }}>
                        {party.party_count}/6
                    </span>
                )}
            </div>

            {pokemon.length > 0 ? (
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: 'var(--spacing-md)',
                }}>
                    {pokemon.map((poke, index) => (
                        <div
                            key={index}
                            style={{
                                padding: 'var(--spacing-md)',
                                background: poke.is_fainted ? 'rgba(239, 68, 68, 0.1)' : 'var(--color-bg-tertiary)',
                                borderRadius: 'var(--radius-md)',
                                opacity: poke.is_fainted ? 0.6 : 1,
                            }}
                        >
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                marginBottom: 'var(--spacing-xs)',
                            }}>
                                <span style={{
                                    fontSize: '0.75rem',
                                    fontWeight: 600,
                                    color: 'var(--color-text-primary)',
                                }}>
                                    {poke.nickname || `Pokemon ${index + 1}`}
                                </span>
                                <span style={{
                                    fontSize: '0.625rem',
                                    color: 'var(--color-text-secondary)',
                                }}>
                                    Lv.{poke.level}
                                </span>
                            </div>

                            <div className="hp-bar" style={{ marginBottom: 'var(--spacing-xs)' }}>
                                <div
                                    className={`hp-bar-fill ${getHPClass(poke.hp_percentage)}`}
                                    style={{ width: `${poke.hp_percentage}%` }}
                                />
                            </div>

                            <div style={{
                                fontSize: '0.625rem',
                                color: 'var(--color-text-muted)',
                                display: 'flex',
                                justifyContent: 'space-between',
                            }}>
                                <span>{poke.current_hp}/{poke.max_hp}</span>
                                <span>{poke.is_fainted ? '💀' : '✓'}</span>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div style={{
                    padding: 'var(--spacing-xl)',
                    textAlign: 'center',
                    color: 'var(--color-text-muted)',
                    fontSize: '0.875rem',
                }}>
                    No party data available
                </div>
            )}

            {party && party.pokemon.length > 0 && (
                <div style={{
                    marginTop: 'var(--spacing-md)',
                    padding: 'var(--spacing-sm)',
                    background: 'var(--color-bg-tertiary)',
                    borderRadius: 'var(--radius-sm)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '0.75rem',
                }}>
                    <span style={{ color: 'var(--color-text-secondary)' }}>Team Health</span>
                    <span style={{
                        color: party.total_hp_percentage > 50 ? 'var(--color-success)' : 'var(--color-warning)',
                        fontWeight: 600,
                    }}>
                        {party.total_hp_percentage.toFixed(0)}%
                    </span>
                </div>
            )}
        </div>
    );
}
