"""Pokemon FireRed memory reader for parsing game state from RAM."""

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional
import structlog

from .emulator import EmulatorController

logger = structlog.get_logger()


# =============================================================================
# Memory Addresses for Pokemon FireRed (US v1.0)
# =============================================================================

class MemoryAddresses(IntEnum):
    """Important memory addresses for Pokemon FireRed."""
    # Party Pokemon (6 slots, 100 bytes each)
    PARTY_BASE = 0x02024284
    PARTY_COUNT = 0x02024029

    # Player Data
    PLAYER_NAME = 0x02024284 - 0x1C  # Player name before party
    PLAYER_MONEY = 0x02025838
    PLAYER_BADGES = 0x02025824

    # Position
    PLAYER_X = 0x02036E30
    PLAYER_Y = 0x02036E32
    MAP_BANK = 0x02036DFC
    MAP_NUMBER = 0x02036DFE

    # Battle State
    IN_BATTLE = 0x0202428C
    BATTLE_TURN = 0x02023E8C

    # Wild Pokemon in battle
    ENEMY_POKEMON = 0x02024744


# Pokemon structure offsets within 100-byte block
class PokemonOffsets(IntEnum):
    """Offsets within a Pokemon data structure."""
    PERSONALITY = 0x00      # 4 bytes
    OT_ID = 0x04            # 4 bytes  
    NICKNAME = 0x08         # 10 bytes
    LANGUAGE = 0x12         # 2 bytes
    OT_NAME = 0x14          # 7 bytes
    MARKINGS = 0x1B         # 1 byte
    CHECKSUM = 0x1C         # 2 bytes
    PADDING = 0x1E          # 2 bytes
    DATA = 0x20             # 48 bytes (encrypted substructures)
    STATUS = 0x50           # 4 bytes
    LEVEL = 0x54            # 1 byte
    POKERUS = 0x55          # 1 byte
    CURRENT_HP = 0x56       # 2 bytes
    MAX_HP = 0x58           # 2 bytes
    ATTACK = 0x5A           # 2 bytes
    DEFENSE = 0x5C          # 2 bytes
    SPEED = 0x5E            # 2 bytes
    SP_ATTACK = 0x60        # 2 bytes
    SP_DEFENSE = 0x62       # 2 bytes


# Pokemon type IDs
POKEMON_TYPES = {
    0: "Normal", 1: "Fighting", 2: "Flying", 3: "Poison",
    4: "Ground", 5: "Rock", 6: "Bug", 7: "Ghost",
    8: "Steel", 9: "???", 10: "Fire", 11: "Water",
    12: "Grass", 13: "Electric", 14: "Psychic", 15: "Ice",
    16: "Dragon", 17: "Dark"
}


@dataclass
class PokemonData:
    """Data structure for a single Pokemon."""
    species_id: int = 0
    nickname: str = ""
    level: int = 1
    current_hp: int = 0
    max_hp: int = 0
    attack: int = 0
    defense: int = 0
    speed: int = 0
    sp_attack: int = 0
    sp_defense: int = 0
    status: int = 0  # 0 = healthy
    is_fainted: bool = False
    types: list[str] = field(default_factory=list)

    @property
    def hp_percentage(self) -> float:
        """Get HP as a percentage."""
        if self.max_hp == 0:
            return 0.0
        return (self.current_hp / self.max_hp) * 100

    @property
    def is_healthy(self) -> bool:
        """Check if Pokemon has no status condition."""
        return self.status == 0 and not self.is_fainted

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "species_id": self.species_id,
            "nickname": self.nickname,
            "level": self.level,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "hp_percentage": self.hp_percentage,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "sp_attack": self.sp_attack,
            "sp_defense": self.sp_defense,
            "status": self.status,
            "is_fainted": self.is_fainted,
            "types": self.types
        }


@dataclass
class PartyData:
    """Data structure for the player's Pokemon party."""
    pokemon: list[PokemonData] = field(default_factory=list)
    party_count: int = 0

    @property
    def lead_pokemon(self) -> Optional[PokemonData]:
        """Get the first non-fainted Pokemon."""
        for poke in self.pokemon:
            if not poke.is_fainted:
                return poke
        return None

    @property
    def all_fainted(self) -> bool:
        """Check if all Pokemon are fainted (blackout condition)."""
        return all(p.is_fainted for p in self.pokemon)

    @property
    def total_hp_percentage(self) -> float:
        """Get average HP percentage across party."""
        if not self.pokemon:
            return 0.0
        return sum(p.hp_percentage for p in self.pokemon) / len(self.pokemon)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "party_count": self.party_count,
            "pokemon": [p.to_dict() for p in self.pokemon],
            "all_fainted": self.all_fainted,
            "total_hp_percentage": self.total_hp_percentage
        }


@dataclass
class PlayerPosition:
    """Player's current position in the game world."""
    x: int = 0
    y: int = 0
    map_bank: int = 0
    map_number: int = 0

    @property
    def location_id(self) -> str:
        """Get a unique location identifier."""
        return f"{self.map_bank}_{self.map_number}"

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "map_bank": self.map_bank,
            "map_number": self.map_number,
            "location_id": self.location_id
        }


@dataclass
class GameState:
    """Complete game state snapshot."""
    party: PartyData = field(default_factory=PartyData)
    position: PlayerPosition = field(default_factory=PlayerPosition)
    money: int = 0
    badges: int = 0
    in_battle: bool = False
    enemy_pokemon: Optional[PokemonData] = None

    def to_dict(self) -> dict:
        return {
            "party": self.party.to_dict(),
            "position": self.position.to_dict(),
            "money": self.money,
            "badges": self.badges,
            "badge_count": bin(self.badges).count('1'),
            "in_battle": self.in_battle,
            "enemy_pokemon": self.enemy_pokemon.to_dict() if self.enemy_pokemon else None
        }


class MemoryReader:
    """
    Reads and parses Pokemon FireRed game state from memory.
    
    Uses mGBA-http memory read API to extract game information
    like party Pokemon, player position, badges, etc.
    """

    def __init__(self, emulator: EmulatorController):
        """
        Initialize the memory reader.
        
        Args:
            emulator: EmulatorController instance for memory access.
        """
        self.emulator = emulator

    async def read_party(self) -> PartyData:
        """
        Read the player's Pokemon party from memory.
        
        Returns:
            PartyData with all party Pokemon.
        """
        party = PartyData()

        # Read party count
        count_data = await self.emulator.read_memory(MemoryAddresses.PARTY_COUNT, 1)
        if count_data:
            party.party_count = count_data[0]
        else:
            party.party_count = 0
            return party

        # Read each Pokemon in party
        for i in range(min(party.party_count, 6)):
            pokemon_addr = MemoryAddresses.PARTY_BASE + (i * 100)
            pokemon_data = await self.emulator.read_memory(pokemon_addr, 100)

            if pokemon_data:
                pokemon = self._parse_pokemon(pokemon_data)
                party.pokemon.append(pokemon)

        logger.debug("Party read", count=party.party_count)
        return party

    def _parse_pokemon(self, data: bytes) -> PokemonData:
        """
        Parse a 100-byte Pokemon data structure.
        
        Args:
            data: 100 bytes of Pokemon data.
        
        Returns:
            Parsed PokemonData.
        """
        pokemon = PokemonData()

        try:
            # Parse nickname (10 bytes starting at offset 0x08)
            nickname_bytes = data[PokemonOffsets.NICKNAME:PokemonOffsets.NICKNAME + 10]
            pokemon.nickname = self._decode_string(nickname_bytes)

            # Parse stats
            pokemon.level = data[PokemonOffsets.LEVEL]
            pokemon.current_hp = struct.unpack_from('<H', data, PokemonOffsets.CURRENT_HP)[0]
            pokemon.max_hp = struct.unpack_from('<H', data, PokemonOffsets.MAX_HP)[0]
            pokemon.attack = struct.unpack_from('<H', data, PokemonOffsets.ATTACK)[0]
            pokemon.defense = struct.unpack_from('<H', data, PokemonOffsets.DEFENSE)[0]
            pokemon.speed = struct.unpack_from('<H', data, PokemonOffsets.SPEED)[0]
            pokemon.sp_attack = struct.unpack_from('<H', data, PokemonOffsets.SP_ATTACK)[0]
            pokemon.sp_defense = struct.unpack_from('<H', data, PokemonOffsets.SP_DEFENSE)[0]

            # Status condition
            pokemon.status = struct.unpack_from('<I', data, PokemonOffsets.STATUS)[0]
            pokemon.is_fainted = pokemon.current_hp == 0

            # Personality value (for species and other encrypted data)
            personality = struct.unpack_from('<I', data, PokemonOffsets.PERSONALITY)[0]
            pokemon.species_id = personality & 0xFFFF  # Simplified - actual reading requires decryption

        except Exception as e:
            logger.error("Error parsing Pokemon data", error=str(e))

        return pokemon

    def _decode_string(self, data: bytes) -> str:
        """
        Decode a Pokemon character encoding string.
        
        Pokemon Gen 3 uses a custom character encoding.
        0xFF = terminator.
        
        Args:
            data: Raw bytes to decode.
        
        Returns:
            Decoded string.
        """
        # Simplified Gen 3 character map (partial)
        char_map = {
            0xBB: 'A', 0xBC: 'B', 0xBD: 'C', 0xBE: 'D', 0xBF: 'E',
            0xC0: 'F', 0xC1: 'G', 0xC2: 'H', 0xC3: 'I', 0xC4: 'J',
            0xC5: 'K', 0xC6: 'L', 0xC7: 'M', 0xC8: 'N', 0xC9: 'O',
            0xCA: 'P', 0xCB: 'Q', 0xCC: 'R', 0xCD: 'S', 0xCE: 'T',
            0xCF: 'U', 0xD0: 'V', 0xD1: 'W', 0xD2: 'X', 0xD3: 'Y',
            0xD4: 'Z', 0xD5: 'a', 0xD6: 'b', 0xD7: 'c', 0xD8: 'd',
            0xD9: 'e', 0xDA: 'f', 0xDB: 'g', 0xDC: 'h', 0xDD: 'i',
            0xDE: 'j', 0xDF: 'k', 0xE0: 'l', 0xE1: 'm', 0xE2: 'n',
            0xE3: 'o', 0xE4: 'p', 0xE5: 'q', 0xE6: 'r', 0xE7: 's',
            0xE8: 't', 0xE9: 'u', 0xEA: 'v', 0xEB: 'w', 0xEC: 'x',
            0xED: 'y', 0xEE: 'z', 0x00: ' ',
            0xFF: ''  # Terminator
        }

        result = []
        for byte in data:
            if byte == 0xFF:  # String terminator
                break
            result.append(char_map.get(byte, '?'))
        return ''.join(result)

    async def read_position(self) -> PlayerPosition:
        """
        Read the player's current position.
        
        Returns:
            PlayerPosition with coordinates and map info.
        """
        position = PlayerPosition()

        try:
            # Read X and Y coordinates (2 bytes each)
            x_data = await self.emulator.read_memory(MemoryAddresses.PLAYER_X, 2)
            y_data = await self.emulator.read_memory(MemoryAddresses.PLAYER_Y, 2)

            if x_data:
                position.x = struct.unpack('<H', x_data)[0]
            if y_data:
                position.y = struct.unpack('<H', y_data)[0]

            # Read map bank and number
            bank_data = await self.emulator.read_memory(MemoryAddresses.MAP_BANK, 2)
            map_data = await self.emulator.read_memory(MemoryAddresses.MAP_NUMBER, 2)

            if bank_data:
                position.map_bank = struct.unpack('<H', bank_data)[0]
            if map_data:
                position.map_number = struct.unpack('<H', map_data)[0]

            logger.debug("Position read", x=position.x, y=position.y, 
                        map_bank=position.map_bank, map_number=position.map_number)

        except Exception as e:
            logger.error("Error reading position", error=str(e))

        return position

    async def read_money(self) -> int:
        """Read the player's money."""
        data = await self.emulator.read_memory(MemoryAddresses.PLAYER_MONEY, 4)
        if data:
            return struct.unpack('<I', data)[0]
        return 0

    async def read_badges(self) -> int:
        """Read the player's badges (as a bitmask)."""
        data = await self.emulator.read_memory(MemoryAddresses.PLAYER_BADGES, 1)
        if data:
            return data[0]
        return 0

    async def is_in_battle(self) -> bool:
        """Check if the player is currently in a battle."""
        data = await self.emulator.read_memory(MemoryAddresses.IN_BATTLE, 1)
        if data:
            return data[0] != 0
        return False

    async def read_full_state(self) -> GameState:
        """
        Read the complete game state.
        
        Returns:
            GameState with all game information.
        """
        state = GameState()

        state.party = await self.read_party()
        state.position = await self.read_position()
        state.money = await self.read_money()
        state.badges = await self.read_badges()
        state.in_battle = await self.is_in_battle()

        if state.in_battle:
            # Could read enemy Pokemon data here
            pass

        logger.info("Full game state read", 
                   party_count=state.party.party_count,
                   in_battle=state.in_battle,
                   badges=bin(state.badges).count('1'))

        return state
