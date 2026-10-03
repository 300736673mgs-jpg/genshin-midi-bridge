# Genshin MIDI Bridge

A Windows desktop app that maps a MIDI keyboard to the controls of playable instruments in Genshin Impact in real time.

> This is an independent community project. It is not affiliated with, authorized by, or endorsed by the game's developer or publisher.

## Download and install

Most users do not need Python and should not run any `.bat` files:

1. Open **Releases** on the right side of this GitHub repository.
2. Download the latest `Genshin-MIDI-Bridge-Setup.exe`.
3. Run the installer and approve the Windows administrator prompt.
4. Start **Genshin MIDI Bridge** from the Start menu or its optional desktop shortcut.
5. Choose your language the first time the app opens. You can change it later in **Settings**.

If Microsoft Defender SmartScreen displays “Windows protected your PC,” the app has not yet been signed with a commercial code-signing certificate. After confirming that the file came from this repository's Release page, select **More info → Run anyway**.

## Quick start

1. Connect a keyboard that sends MIDI Note On/Off messages through USB or Bluetooth MIDI.
2. Start Genshin MIDI Bridge and select your MIDI device and the matching in-game instrument.
3. Select **Connect**, then **Start mapping**.
4. Return to the game, open the instrument, and play.

A regular Bluetooth typing keyboard is not a MIDI device. If a Bluetooth MIDI keyboard does not appear, it may require the manufacturer's driver or a BLE-MIDI bridge for Windows. See the in-app **User guide** for complete setup and troubleshooting instructions.

## Features

- USB MIDI and Bluetooth MIDI inputs exposed to Windows
- Presets for three-row, two-row, chord, chromatic, and percussion instruments
- Visual piano editor with independently configurable white and black keys
- Left/right black-key mapping, outer-octave folding, transpose, octave shift, and velocity threshold
- CC64 sustain pedal support, including repeated notes while the pedal is held
- Simplified Chinese, English, Spanish, and Japanese interfaces
- `Ctrl + Alt + F8` to start or stop mapping
- Local settings storage; the app does not read the game process or modify game files

## Why administrator access is requested

Windows prevents a normal application from sending input to a game running with administrator privileges. Genshin MIDI Bridge requests the same privilege so that mapped keystrokes can reach the game. It only sends the keyboard inputs configured in the app.

## Instrument modes

- Windsong Lyre, Leaping Spirit Piano, and Harmonic Keys: three rows and 21 notes
- Nightwind Horn: two rows and 14 notes
- “Lingering Euphonia” and Ukulele: chords placed one physical octave below the melody
- Vintage Lyre: accidentals mapped to real black keys; unavailable notes remain disabled
- Festive Drum and Djem Djem Drum: only the percussion inputs available in game are mapped

## Run from source

Requires Windows 10/11 and Python 3. Run `run.bat`; on its first run it creates `.venv` and installs the dependencies.

## Build a release

Run `build_exe.bat` to create `dist\Genshin-MIDI-Bridge.exe`. After installing [Inno Setup](https://jrsoftware.org/isinfo.php), run `build_installer.bat` to create `dist\Genshin-MIDI-Bridge-Setup.exe`.

GitHub Actions also builds the executable and installer when a version tag beginning with `v` is pushed.

## Configuration and logs

- Configuration: `%LOCALAPPDATA%\GenshinMidiBridge\config.json`
- Log: `%LOCALAPPDATA%\GenshinMidiBridge\app.log`

## Privacy

The app does not connect to the internet or collect telemetry. Settings and logs remain on the local computer.
