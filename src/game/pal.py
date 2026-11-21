"""Reforged's PAL preview, for the European retail disc in PCSX2."""

import logging
import struct
import time

from core.pine_ipc import (
    PineError, PineIPC, PINE_PORT,
    MSG_READ32, MSG_WRITE8, MSG_WRITE16, MSG_WRITE32,
)
from game.addresses import Mode
from mods.dailyshop import _SLOT_ADDRS, base_shop_changes, roll_daily_items
from mods.shop import ShopMod
from mods.town import TOWN_PATCHES
from mods.weapons import WeaponsMod

log = logging.getLogger(__name__)

SERIAL = "SCES-50295"
CRC = "0BAA8DD8"
MODE = 0x002A4E40
FRAME_COUNTER = 0x002A4D10
GAME_DAY = 0x01CE6C18
VIEW_MATRIX_INSTRUCTION = 0x0012E228
VIEW_MATRIX_EXPECTED = (0x3C023F80, 0x3C023F40)

# NTSC-U addresses used by the existing mods, PAL address, verified symbol size.
# WeaponList, ITEM_LIST, PriceList, ItemShopList2, and exitemlst have the
# same layout on both discs. Addresses are from the retail PAL ELF symbols.
TABLES = (
    (0x2027A6C0, 0x0027CB60, 0x23A0),
    (0x2027D0A0, 0x0027F540, 0x0DAC),
    (0x20291B80, 0x00294020, 0x04A0),
    (0x20292020, 0x002944C0, 0x02D0),
    (0x202929D0, 0x00294E50, 0x008C),
)

# Escape powder needs its dungeon hook before it can be put in active slots.
# Changes to the Matador model use disc-specific asset buffers.
ITEM_PATCHES = (
    0x2027DD50, 0x2027DD28, 0x2027DC80, 0x2027DC94,
    0x2027D81C, 0x2027D830, 0x2027D8A8, 0x20292A3E,
)


def translate_table(address, width):
    for us, pal, length in TABLES:
        if us <= address and address + width <= us + length:
            return pal + address - us
    raise ValueError(f"Adresse PAL non vérifiée : 0x{address:08X}")


class PalTables:
    """Apply original Reforged table edits through the verified PAL symbols."""

    def __init__(self, ipc):
        self.ipc = ipc
        self.writes = []

    def read_short(self, address):
        return self.ipc.read16(translate_table(address, 2))

    def write_byte(self, address, value):
        self.writes.append((MSG_WRITE8, translate_table(address, 1), value))

    def write_short(self, address, value):
        self.writes.append((MSG_WRITE16, translate_table(address, 2), value))

    def write_int(self, address, value):
        self.writes.append((MSG_WRITE32, translate_table(address, 4), value))

    def write_float(self, address, value):
        self.write_int(address, struct.unpack("<I", struct.pack("<f", value))[0])


class PalSession:
    def __init__(self, ipc):
        self.ipc = ipc
        self.applied = False
        self.frame = 0
        self.last_day = None

    def step(self):
        if self.ipc.status() != 0:
            return
        serial = self.ipc.game_id()
        crc = self.ipc.game_crc()
        if (serial, crc) != (SERIAL, CRC):
            raise ValueError(f"Jeu détecté : {serial} ({crc}). Cette version du mod attend {SERIAL} ({CRC}).")
        opcode, frame, mode = self.ipc.batch([
            (MSG_READ32, VIEW_MATRIX_INSTRUCTION), (MSG_READ32, FRAME_COUNTER), (MSG_READ32, MODE),
        ])
        if opcode not in VIEW_MATRIX_EXPECTED or frame == 0:
            return  # Wait for the executable to finish loading.
        if frame < self.frame:
            self.applied = False
            self.last_day = None
        self.frame = frame
        if not self.applied:
            tables = PalTables(self.ipc)
            ShopMod(tables).apply_once()
            WeaponsMod(tables).apply_once(adjust_lamb=False)
            base_shop_changes(tables)
            for address, value, kind in TOWN_PATCHES:
                if address in ITEM_PATCHES:
                    write = tables.write_byte if kind == "byte" else tables.write_short
                    write(address, value)
            if (self.ipc.game_id(), self.ipc.game_crc()) != (SERIAL, CRC):
                return
            self.ipc.batch(tables.writes)
            self.applied = True
            log.info("Dark Cloud Europe détecté. Armes, objets et boutiques Reforged actifs.")
        if mode in (Mode.TOWN, Mode.DUNGEON):
            day = self.ipc.read32(GAME_DAY)
            if day != self.last_day:
                self.ipc.batch([
                    (MSG_WRITE16, translate_table(address, 2), item)
                    for address, item in zip(_SLOT_ADDRS, roll_daily_items(day))
                ])
                self.last_day = day


def run(port=PINE_PORT):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ipc = PineIPC(port)
    log.info("Dark Cloud Reforged PAL — en attente de PCSX2 sur le port %s.", port)
    while True:
        if not ipc.connect():
            time.sleep(1)
            continue
        try:
            session = PalSession(ipc)
            while True:
                session.step()
                time.sleep(0.1)
        except (ConnectionError, OSError, PineError):
            ipc.disconnect()
            time.sleep(0.5)
        finally:
            ipc.disconnect()
