# Genshin MIDI Bridge

Ever tried playing a Genshin instrument on your computer keyboard and ended up tying your fingers in knots? Connect a MIDI keyboard, select an instrument, and press **Start mapping**. That is all it takes to play with piano keys instead.

Genshin MIDI Bridge is a small Windows app made for playing Genshin Impact's in-game instruments by hand. It supports regular three-row instruments, two-row instruments, chord instruments, the Vintage Lyre's accidentals, and the game's drums. You can edit every white and black piano key yourself, fold notes outside the playable range, choose which neighboring white key a black key uses, transpose the keyboard, and use a CC64 sustain pedal.

The interface is available in Simplified Chinese, English, Spanish, and Japanese. On the first launch, the app asks which language you would like to use. It also includes three saved color themes: The Abyss, People of the Springs, and Vanarana.

> This is an independent community tool. It is not affiliated with, authorized by, or endorsed by the game's developer or publisher. It does not read the game process or modify game files; it only turns MIDI notes into the keyboard inputs you configure.

## Download and play

You do not need Python and you do not need to touch any `.bat` files. Open this repository's **Releases** page, download the newest `Genshin-MIDI-Bridge-Setup.exe`, and run the installer. Start the app from the Start menu or the optional desktop shortcut, connect your MIDI keyboard, select the same instrument you opened in game, then press **Connect** and **Start mapping**.

Windows will ask for administrator permission. Please select **Yes**: when the game is running as administrator, Windows will not let a normal app send keys to it. If SmartScreen says that Windows protected your PC, this is because the app does not yet have a commercial code-signing certificate. After checking that the installer came from this repository's Release page, choose **More info → Run anyway**.

A normal Bluetooth typing keyboard is not a MIDI keyboard. USB MIDI devices should appear after Windows detects them. Bluetooth MIDI devices may need the manufacturer's driver or a BLE-MIDI bridge before Windows exposes a MIDI port. If you are not sure how to connect your particular keyboard, check its manual, visit the manufacturer's website, or ask the all-knowing AI.

The full user guide is in the bottom-left corner of the app. If something still refuses to work, find 匿叶龙吃炸弹 on Bilibili (B站).

## A few useful details

The app remembers your language, theme, MIDI device, instrument, mappings, transpose settings, and playing preferences locally. `Ctrl + Alt + F8` starts or stops mapping while the game is in front. Notes beyond an instrument's playable range can be folded into the nearest octave, and black keys can be sent to either the neighboring white key on the left or the one on the right.

The Vintage Lyre uses its available accidentals directly. “Lingering Euphonia” and the Ukulele place their seven chords one physical octave below the melody. The Festive Drum uses four consecutive white keys, while the Djem Djem Drum uses two groups of four.

Configuration is stored in `%LOCALAPPDATA%\GenshinMidiBridge\config.json`, and the troubleshooting log is stored beside it as `app.log`. The app does not connect to the internet or collect telemetry.

## Running from source and building

Developers need Windows 10 or 11 and Python 3. Run `run.bat`; it creates a local `.venv` and installs the required packages the first time. Run `build_exe.bat` to produce `dist\Genshin-MIDI-Bridge.exe`. With [Inno Setup](https://jrsoftware.org/isinfo.php) installed, `build_installer.bat` produces `dist\Genshin-MIDI-Bridge-Setup.exe`.

The GitHub Actions workflow builds the executable and installer whenever a version tag beginning with `v` is pushed.

流泉不息，哗啦逐浪，玛门永存 。
