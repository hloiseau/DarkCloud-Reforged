# Dark Cloud Reforged PAL

Aperçu pour Dark Cloud Europe (`SCES-50295`, CRC PCSX2 `0BAA8DD8`). Choisis **Français** au démarrage du jeu. L’édition européenne fournit les menus et dialogues d’origine.

Cet aperçu reprend les prix Reforged, la rotation quotidienne des boutiques, la plupart des changements de statistiques d’armes et plusieurs modifications d’objets. Les poudres de résurrection, de réparation et d’auto-réparation sont empilables. Les seuils de transformation de l’Épée de l’agneau et les modifications qui nécessitent les hooks NTSC restent à porter. Cela comprend les quêtes et dialogues supplémentaires, les alliés en ville et le contenu remanié des donjons.

## Jouer sous Windows avec le PCSX2 de RomStation

Utilise Python 3.10 ou plus récent et une image locale du jeu européen. Si elle est dans une archive ZIP, extrais d’abord le fichier ISO. Lance depuis ce dépôt :

```powershell
python scripts/launch_pal.py --pcsx2 "C:\chemin\vers\pcsx2-qt.exe" --game "C:\chemin\vers\DARK_CLOUD.ISO" --profile "C:\chemin\vers\Reforged-PAL"
```

Au premier lancement, le script prépare une instance portable à partir du PCSX2 existant, avec ses réglages de manette, un port PINE dédié et ses propres cartes mémoire. Choisis **Français**, puis **Nouvelle partie**. Les sauvegardes sur carte mémoire sont dans le dossier `memcards` du profil Reforged. Relance le jeu avec la même commande pour les retrouver.

Avec ton propre profil PCSX2, active PINE dans **Paramètres → Avancé** et lance `python src/main.py --pal` à côté de l’émulateur. Indique `--pine-port` si tu as choisi un port différent du port par défaut 28011.

## Vérification

Les adresses proviennent des symboles du disque européen commercial. Les [cartes de Chronicle](https://github.com/TheMoonPeople/Chronicle/tree/master/ps2/config) ont permis d’associer les tables avec celles reprises dans Reforged. Le mod vérifie le numéro de série, le CRC et une instruction de l’exécutable avant d’appliquer les changements.

`python -m unittest discover -s tests` vérifie le rejet d’une révision différente, les bornes des tables et les réponses PINE groupées.
