"""Launch the PAL preview with a separate portable PCSX2 profile on Windows."""

import argparse
import configparser
import logging
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core.pine_ipc import PineError, PineIPC
from game.pal import PalSession

PORT = 28173


def setup_profile(pcsx2, profile):
    if profile == pcsx2.parent:
        raise ValueError("Choisis un dossier séparé pour le profil Reforged.")
    config = profile / "inis" / "PCSX2.ini"
    if config.is_file():
        return
    original = configparser.ConfigParser(interpolation=None)
    original.optionxform = str
    original.read(pcsx2.parent / "inis" / "PCSX2.ini", encoding="utf-8-sig")
    bios = original.get("Filenames", "BIOS", fallback="")
    bios_dir = pcsx2.parent / "bios"
    if not bios or Path(bios).name != bios or not (bios_dir / bios).is_file():
        raise ValueError("Sélectionne d'abord ton BIOS PS2 dans PCSX2.")

    config.parent.mkdir(parents=True, exist_ok=True)
    for filename in (pcsx2, pcsx2.parent / "qt.conf", *pcsx2.parent.glob("*.dll")):
        if filename.is_file():
            shutil.copy2(filename, profile)
    for name in ("QtPlugins", "resources", "translations"):
        directory = pcsx2.parent / name
        if directory.is_dir():
            shutil.copytree(directory, profile / name, dirs_exist_ok=True)
    (profile / "bios").mkdir(exist_ok=True)
    shutil.copy2(bios_dir / bios, profile / "bios")
    (profile / "portable.ini").touch()

    settings = configparser.ConfigParser(interpolation=None)
    settings.optionxform = str
    for section in ("InputSources", "Pad", *(f"Pad{i}" for i in range(1, 9))):
        if section in original:
            settings[section] = original[section]
    settings["UI"] = {"SettingsVersion": "1", "SetupWizardIncomplete": "false"}
    settings["AutoUpdater"] = {"CheckAtStartup": "false"}
    settings["Filenames"] = {"BIOS": bios}
    settings["EmuCore"] = {"EnablePINE": "true", "PINESlot": str(PORT)}
    settings["EmuCore/GS"] = {"upscale_multiplier": "3"}
    with config.open("w", encoding="utf-8") as stream:
        settings.write(stream)


def play(pcsx2, game, profile):
    with socket.socket() as sock:
        sock.settimeout(0.2)
        if sock.connect_ex(("127.0.0.1", PORT)) == 0:
            raise ValueError("Le port du mod est déjà utilisé. Ferme l'autre session Reforged PAL.")
    setup_profile(pcsx2, profile)
    emulator = subprocess.Popen([
        str(profile / pcsx2.name), "-portable", "-batch", "-nofullscreen", "-fastboot", "--", str(game),
    ], cwd=profile)
    ipc = PineIPC(PORT)
    try:
        deadline = time.monotonic() + 20
        print("Dark Cloud Reforged PAL démarre.", flush=True)
        while emulator.poll() is None and not ipc.connect():
            if time.monotonic() >= deadline:
                raise ValueError("PCSX2 ne répond pas sur le port du mod.")
            time.sleep(0.2)
        session = PalSession(ipc)
        while emulator.poll() is None:
            session.step()
            time.sleep(0.05)
    except (ConnectionError, OSError, PineError):
        if emulator.poll() is None:
            raise
    finally:
        ipc.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jouer à Dark Cloud Reforged PAL sur Windows")
    parser.add_argument("--pcsx2", type=Path, required=True, help="Chemin du pcsx2-qt.exe de RomStation")
    parser.add_argument("--game", type=Path, required=True, help="Image locale du disque européen (ISO ou CHD)")
    parser.add_argument("--profile", type=Path, required=True, help="Dossier dédié à Reforged PAL")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("Ce lanceur utilise le PCSX2 Windows de RomStation.")
    if not args.pcsx2.is_file() or not args.game.is_file():
        parser.error("Le chemin de PCSX2 ou de l'image du jeu est introuvable.")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("mods").setLevel(logging.WARNING)
    try:
        play(args.pcsx2.resolve(), args.game.resolve(), args.profile.resolve())
    except (ValueError, OSError, PineError) as exc:
        parser.exit(1, f"{exc}\n")
