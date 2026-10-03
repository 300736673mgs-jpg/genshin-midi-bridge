from __future__ import annotations

import ctypes
import json
import logging
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import traceback
from ctypes import wintypes
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

import rtmidi
from PySide6.QtCore import QPoint, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSizeGrip,
    QSpinBox, QStackedWidget, QTextBrowser, QVBoxLayout, QWidget,
)


APP_NAME = "GenshinMidiBridge"
APP_DIR = Path(__file__).resolve().parent
CONFIG_DIR = Path.home() / "AppData" / "Local" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "app.log"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LEGACY_CONFIG_FILE = Path.home() / "AppData" / "Local" / "MidiBridge" / "config.json"
if not CONFIG_FILE.exists() and LEGACY_CONFIG_FILE.exists():
    try:
        shutil.copy2(LEGACY_CONFIG_FILE, CONFIG_FILE)
    except OSError:
        pass
try:
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
except OSError:
    LOG_FILE = CONFIG_DIR / f"app-{os.getpid()}.log"
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")

WHITE_PCS = (0, 2, 4, 5, 7, 9, 11)
NOTE_NAMES = ("C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B")
LANGUAGES = {"zh": "简体中文", "en": "English", "es": "Español", "ja": "日本語"}
TEXT = {
    "zh": {
        "home": "主页", "instruments": "乐器", "settings": "设置", "about": "说明书",
        "home_title": "准备演奏", "home_sub": "选择乐器，连接 MIDI，然后开始。",
        "refresh": "刷新", "connect": "连接", "disconnect": "断开", "start": "开始映射", "stop": "停止映射",
        "not_connected": "未连接", "connected": "设备已连接", "mapping": "正在映射", "waiting": "等待 MIDI 输入",
        "instrument_title": "乐器与键位", "instrument_sub": "选择模式；点击琴键可以覆盖当前预设。",
        "instrument_info": "乐器简介", "map_to": "映射到", "disabled": "关闭", "reset": "恢复此模式默认值",
        "settings_sub": "演奏参数与输入行为。", "language": "界面语言", "pitch": "音高",
        "octave": "八度偏移", "transpose": "半音移调", "behavior": "输入行为", "velocity": "力度门槛",
        "sustain": "处理延音踏板（CC64）", "black_keys": "把黑键映射到相邻白键", "black_direction": "黑键映射方向", "black_left": "左侧白键", "black_right": "右侧白键", "fold": "把外侧两个八度折叠到最近可用音区",
        "no_device": "没有发现 MIDI 设备", "choose_device": "请先连接 MIDI 设备，然后刷新列表。", "device_missing": "找不到所选 MIDI 设备，请刷新后重试。",
        "enumerate_error": "枚举 MIDI 设备失败：{error}", "press": "按下", "release": "松开",
        "unmapped": "当前模式未映射", "pedal_down": "延音踏板  ·  踩下", "pedal_up": "延音踏板  ·  松开",
        "hotkey_busy": "Ctrl + Alt + F8 被其他程序占用", "got_it": "知道了", "error": "发生错误",
        "manual_title": "Genshin MIDI Bridge 使用说明",
        "velocity_live": "力度",
        "midi_error": "处理 MIDI 消息失败：{error}",
    },
    "en": {
        "home": "Home", "instruments": "Instruments", "settings": "Settings", "about": "User guide",
        "home_title": "Ready to play", "home_sub": "Choose an instrument, connect MIDI, and start playing.",
        "refresh": "Refresh", "connect": "Connect", "disconnect": "Disconnect", "start": "Start mapping", "stop": "Stop mapping",
        "not_connected": "Not connected", "connected": "Device connected", "mapping": "Mapping active", "waiting": "Waiting for MIDI input",
        "instrument_title": "Instrument & keys", "instrument_sub": "Choose a mode. Click any piano key to override its mapping.",
        "instrument_info": "Instrument info", "map_to": "Map to", "disabled": "Off", "reset": "Restore mode defaults",
        "settings_sub": "Performance and input preferences.", "language": "Interface language", "pitch": "Pitch",
        "octave": "Octave shift", "transpose": "Semitone transpose", "behavior": "Input behavior", "velocity": "Velocity threshold",
        "sustain": "Use sustain pedal (CC64)", "black_keys": "Map black keys to adjacent white keys", "black_direction": "Black-key direction", "black_left": "White key on the left", "black_right": "White key on the right", "fold": "Fold outer octaves into the nearest playable range",
        "no_device": "No MIDI device found", "choose_device": "Connect a MIDI device, then refresh the list.", "device_missing": "The selected MIDI device was not found. Refresh and try again.",
        "enumerate_error": "Could not list MIDI devices: {error}", "press": "Pressed", "release": "Released",
        "unmapped": "Not mapped in this mode", "pedal_down": "Sustain pedal  ·  Down", "pedal_up": "Sustain pedal  ·  Up",
        "hotkey_busy": "Ctrl + Alt + F8 is in use by another app", "got_it": "Done", "error": "Something went wrong",
        "manual_title": "Genshin MIDI Bridge User Guide",
        "velocity_live": "Velocity",
        "midi_error": "Could not process the MIDI message: {error}",
    },
    "es": {
        "home": "Inicio", "instruments": "Instrumentos", "settings": "Ajustes", "about": "Manual",
        "home_title": "Listo para tocar", "home_sub": "Elige un instrumento, conecta MIDI y empieza a tocar.",
        "refresh": "Actualizar", "connect": "Conectar", "disconnect": "Desconectar", "start": "Iniciar mapeo", "stop": "Detener mapeo",
        "not_connected": "Sin conexión", "connected": "Dispositivo conectado", "mapping": "Mapeo activo", "waiting": "Esperando entrada MIDI",
        "instrument_title": "Instrumento y teclas", "instrument_sub": "Elige un modo. Pulsa una tecla del piano para cambiar su asignación.",
        "instrument_info": "Información", "map_to": "Asignar a", "disabled": "Desactivada", "reset": "Restaurar valores del modo",
        "settings_sub": "Preferencias de interpretación y entrada.", "language": "Idioma de la interfaz", "pitch": "Tono",
        "octave": "Cambio de octava", "transpose": "Transposición en semitonos", "behavior": "Comportamiento de entrada", "velocity": "Umbral de velocidad",
        "sustain": "Usar pedal de sustain (CC64)", "black_keys": "Asignar las teclas negras a teclas blancas adyacentes", "black_direction": "Dirección de las teclas negras", "black_left": "Tecla blanca izquierda", "black_right": "Tecla blanca derecha", "fold": "Plegar octavas exteriores al rango más cercano",
        "no_device": "No se encontró ningún dispositivo MIDI", "choose_device": "Conecta un dispositivo MIDI y actualiza la lista.", "device_missing": "No se encontró el dispositivo MIDI seleccionado. Actualiza la lista e inténtalo de nuevo.",
        "enumerate_error": "No se pudieron listar los dispositivos MIDI: {error}", "press": "Pulsada", "release": "Soltada",
        "unmapped": "Sin asignar en este modo", "pedal_down": "Pedal de sustain  ·  Pulsado", "pedal_up": "Pedal de sustain  ·  Soltado",
        "hotkey_busy": "Ctrl + Alt + F8 está en uso por otra aplicación", "got_it": "Listo", "error": "Se produjo un error",
        "manual_title": "Manual de Genshin MIDI Bridge",
        "velocity_live": "Velocidad",
        "midi_error": "No se pudo procesar el mensaje MIDI: {error}",
    },
    "ja": {
        "home": "ホーム", "instruments": "楽器", "settings": "設定", "about": "使い方",
        "home_title": "演奏の準備", "home_sub": "楽器を選択し、MIDIを接続して演奏を始めます。",
        "refresh": "更新", "connect": "接続", "disconnect": "切断", "start": "マッピング開始", "stop": "マッピング停止",
        "not_connected": "未接続", "connected": "デバイス接続済み", "mapping": "マッピング中", "waiting": "MIDI入力を待っています",
        "instrument_title": "楽器とキー", "instrument_sub": "モードを選択し、ピアノのキーをクリックして割り当てを変更できます。",
        "instrument_info": "楽器の説明", "map_to": "割り当て", "disabled": "オフ", "reset": "このモードを初期設定に戻す",
        "settings_sub": "演奏と入力の設定。", "language": "表示言語", "pitch": "ピッチ",
        "octave": "オクターブシフト", "transpose": "半音移調", "behavior": "入力動作", "velocity": "ベロシティしきい値",
        "sustain": "サステインペダルを使用（CC64）", "black_keys": "黒鍵を隣の白鍵に割り当てる", "black_direction": "黒鍵の割り当て方向", "black_left": "左側の白鍵", "black_right": "右側の白鍵", "fold": "範囲外のオクターブを最も近い演奏範囲に折りたたむ",
        "no_device": "MIDIデバイスが見つかりません", "choose_device": "MIDIデバイスを接続してから一覧を更新してください。", "device_missing": "選択したMIDIデバイスが見つかりません。一覧を更新してもう一度お試しください。",
        "enumerate_error": "MIDIデバイスを取得できませんでした：{error}", "press": "押す", "release": "離す",
        "unmapped": "このモードでは未割り当て", "pedal_down": "サステインペダル  ·  オン", "pedal_up": "サステインペダル  ·  オフ",
        "hotkey_busy": "Ctrl + Alt + F8 は別のアプリで使用中です", "got_it": "閉じる", "error": "エラーが発生しました",
        "manual_title": "Genshin MIDI Bridge 使用ガイド",
        "velocity_live": "ベロシティ",
        "midi_error": "MIDIメッセージを処理できませんでした：{error}",
    },
}

MANUAL_HTML = {
    "zh": """
        <h2>快速开始</h2>
        <ol><li>连接 MIDI 键盘。</li><li>启动 Genshin MIDI Bridge，并在系统提示时允许管理员权限。</li>
        <li>在主页选择 MIDI 设备和游戏中的乐器。</li><li>点击“连接”，再点击“开始映射”。</li>
        <li>切回游戏并打开对应乐器，即可直接演奏。</li></ol>
        <h2>连接设备</h2>
        <p><b>USB MIDI：</b>用 USB 线连接电子琴和电脑，等待 Windows 完成识别，然后点击“刷新”。</p>
        <p><b>蓝牙 MIDI：</b>先在 Windows 蓝牙设置中配对。如果设备没有出现在列表里，请安装厂商驱动，或使用能把 BLE MIDI 暴露为 Windows MIDI 端口的桥接软件。</p>
        <p><b>注意：</b>普通蓝牙打字键盘不是 MIDI 设备，不能作为钢琴输入。设备必须能发送 MIDI Note On/Off 消息。</p>
        <h2>管理员权限</h2>
        <p>游戏通常以管理员权限运行。Windows 不允许普通权限程序向高权限游戏发送按键，因此本软件默认请求管理员权限。出现 UAC 窗口时请选择“是”。</p>
        <h2>乐器与键位</h2>
        <p>在“乐器”页切换预设。点击大钢琴上的任意白键或黑键，可以手动修改它发送的键盘按键。黑键映射方向、外侧八度折叠、移调和力度门槛位于“设置”。</p>
        <h2>延音踏板</h2>
        <p>支持 CC64 延音踏板。踩住踏板后可以重复弹同一个音，每次按下都会重新触发；松开踏板会释放所有延音。</p>
        <h2>无法使用时</h2>
        <ul><li>设备不在列表：重新插线或配对，然后点击“刷新”。</li><li>软件有输入但游戏无反应：确认允许了管理员权限，并确认游戏内已经打开乐器。</li>
        <li>快捷键无效：Ctrl + Alt + F8 可能被其他软件占用，仍可使用主页按钮。</li><li>切换设备或乐器后异常：停止映射，重新连接后再开始。</li></ul>
    """,
    "en": """
        <h2>Quick start</h2><ol><li>Connect a MIDI keyboard.</li><li>Launch Genshin MIDI Bridge and approve the administrator prompt.</li>
        <li>Choose the MIDI device and the matching in-game instrument.</li><li>Select Connect, then Start mapping.</li><li>Return to the game, open that instrument, and play.</li></ol>
        <h2>Connecting a device</h2><p><b>USB MIDI:</b> Connect the keyboard by USB, wait for Windows to detect it, then select Refresh.</p>
        <p><b>Bluetooth MIDI:</b> Pair it in Windows first. If it does not appear, install the manufacturer's driver or a BLE-MIDI bridge that exposes a Windows MIDI port.</p>
        <p><b>Note:</b> A regular Bluetooth typing keyboard is not a MIDI device. The device must send MIDI Note On/Off messages.</p>
        <h2>Administrator access</h2><p>The game commonly runs as administrator. Windows blocks a normal app from sending input to an elevated game, so Genshin MIDI Bridge requests administrator access by default. Select Yes in the UAC prompt.</p>
        <h2>Instruments and mappings</h2><p>Choose a preset on the Instruments page. Click any white or black piano key to customize its output. Black-key direction, octave folding, transpose, and velocity threshold are in Settings.</p>
        <h2>Sustain pedal</h2><p>CC64 pedals are supported. Repeating the same note while the pedal is held retriggers it; releasing the pedal releases all sustained notes.</p>
        <h2>Troubleshooting</h2><ul><li>Device missing: reconnect or pair it, then select Refresh.</li><li>MIDI is detected but the game is silent: approve administrator access and open the instrument in game.</li><li>Hotkey unavailable: another app may use Ctrl + Alt + F8; use the Home button instead.</li><li>After switching devices or presets: stop mapping, reconnect, and start again.</li></ul>
    """,
    "es": """
        <h2>Inicio rápido</h2><ol><li>Conecta un teclado MIDI.</li><li>Abre Genshin MIDI Bridge y acepta el permiso de administrador.</li>
        <li>Elige el dispositivo MIDI y el instrumento del juego.</li><li>Pulsa Conectar y después Iniciar mapeo.</li><li>Vuelve al juego, abre el instrumento y toca.</li></ol>
        <h2>Conectar un dispositivo</h2><p><b>MIDI por USB:</b> Conecta el teclado, espera a que Windows lo detecte y pulsa Actualizar.</p>
        <p><b>MIDI por Bluetooth:</b> Emparéjalo primero en Windows. Si no aparece, instala el controlador del fabricante o un puente BLE-MIDI que cree un puerto MIDI de Windows.</p>
        <p><b>Nota:</b> Un teclado Bluetooth normal para escribir no es un dispositivo MIDI. Debe enviar mensajes MIDI Note On/Off.</p>
        <h2>Permisos de administrador</h2><p>El juego suele ejecutarse como administrador. Windows impide que una aplicación normal envíe teclas a un juego elevado, por lo que Genshin MIDI Bridge solicita este permiso de forma predeterminada.</p>
        <h2>Instrumentos y asignaciones</h2><p>Elige un modo en Instrumentos. Pulsa cualquier tecla blanca o negra del piano para cambiar su asignación. La dirección de teclas negras, el plegado de octavas, la transposición y la velocidad están en Ajustes.</p>
        <h2>Pedal de sustain</h2><p>Se admiten pedales CC64. Una nota repetida mientras se mantiene el pedal vuelve a activarse; al soltarlo se liberan todas las notas sostenidas.</p>
        <h2>Solución de problemas</h2><ul><li>El dispositivo no aparece: vuelve a conectarlo o emparejarlo y pulsa Actualizar.</li><li>Se detecta MIDI pero el juego no responde: acepta el permiso de administrador y abre el instrumento dentro del juego.</li><li>El atajo no funciona: otra aplicación puede estar usando Ctrl + Alt + F8.</li></ul>
    """,
    "ja": """
        <h2>クイックスタート</h2><ol><li>MIDIキーボードを接続します。</li><li>Genshin MIDI Bridgeを起動し、管理者権限を許可します。</li>
        <li>MIDIデバイスとゲーム内の楽器を選択します。</li><li>「接続」、「マッピング開始」の順に押します。</li><li>ゲームに戻り、対応する楽器を開いて演奏します。</li></ol>
        <h2>デバイスの接続</h2><p><b>USB MIDI：</b>USBで接続し、Windowsの認識を待ってから「更新」を押します。</p>
        <p><b>Bluetooth MIDI：</b>Windowsで先にペアリングします。表示されない場合はメーカーのドライバー、またはBLE MIDIをWindows MIDIポートとして公開するブリッジソフトを使用してください。</p>
        <p><b>注意：</b>文字入力用の一般的なBluetoothキーボードはMIDI機器ではありません。MIDI Note On/Offを送信できる機器が必要です。</p>
        <h2>管理者権限</h2><p>ゲームが管理者権限で動作している場合、通常権限のアプリからキー入力を送信できません。そのためGenshin MIDI Bridgeは既定で管理者権限を要求します。UACでは「はい」を選択してください。</p>
        <h2>楽器とキー割り当て</h2><p>「楽器」ページでプリセットを選びます。ピアノの白鍵・黒鍵をクリックすると割り当てを変更できます。黒鍵方向、オクターブ折りたたみ、移調、ベロシティは「設定」にあります。</p>
        <h2>サステインペダル</h2><p>CC64に対応しています。ペダル中に同じ音を弾き直しても毎回再発音し、ペダルを離すと保持中の音を解放します。</p>
        <h2>トラブルシューティング</h2><ul><li>機器がない：再接続または再ペアリング後に「更新」。</li><li>入力は見えるがゲームが反応しない：管理者権限とゲーム内で楽器を開いていることを確認。</li><li>ショートカットが使えない：Ctrl + Alt + F8を別アプリが使用している可能性があります。</li></ul>
    """,
}
GAME_KEY_LABELS = {
    "q": "Q", "w": "W", "e": "E", "r": "R", "t": "T", "y": "Y", "u": "U",
    "i": "I", "o": "O", "p": "P", "lbracket": "[", "rbracket": "]",
    "backslash": "\\", "num7": "Num 7", "a": "A", "s": "S", "d": "D",
    "f": "F", "g": "G", "h": "H", "j": "J", "k": "K", "l": "L",
    "z": "Z", "x": "X", "c": "C", "v": "V", "b": "B", "n": "N", "m": "M",
}


def white_notes(octave: int) -> list[int]:
    base = (octave + 1) * 12
    return [base + pitch for pitch in WHITE_PCS]


def row_map(octave: int, keys: str | list[str]) -> dict[int, str]:
    values = list(keys) if isinstance(keys, str) else keys
    return dict(zip(white_notes(octave), values, strict=True))


@dataclass(frozen=True)
class InstrumentProfile:
    id: str
    name: str
    category: str
    summary: str
    description: str
    mapping: dict[int, str]
    display_from: int = 24
    display_to: int = 107


def build_profiles() -> dict[str, InstrumentProfile]:
    standard = row_map(3, "zxcvbnm") | row_map(4, "asdfghj") | row_map(5, "qwertyu")
    two_rows = row_map(3, "asdfghj") | row_map(4, "qwertyu")
    chord = row_map(2, "qwertyu") | row_map(3, "zxcvbnm") | row_map(4, "asdfghj")
    yukele = row_map(2, "zxcvbnm") | row_map(3, "qwertyu") | row_map(
        4, ["i", "o", "p", "lbracket", "rbracket", "backslash", "num7"])
    old_lyre = {
        48: "z", 50: "x", 51: "c", 53: "v", 55: "b", 57: "n", 58: "m",
        60: "a", 62: "s", 63: "d", 65: "f", 67: "g", 69: "h", 70: "j",
        72: "q", 73: "w", 75: "e", 77: "r", 79: "t", 80: "y", 82: "u",
    }
    profiles = [
        InstrumentProfile("windsong", "风物之诗琴", "三排旋律", "三组八度 · 七声音阶",
                          "经典三排二十一键布局。低、中、高音区分别对应 Z–M、A–J、Q–U。", standard),
        InstrumentProfile("euphonium", "余音", "和弦与旋律", "七个和弦 · 两组旋律",
                          "和弦放在旋律区下方一个物理八度：C2–B2 触发 Q–U；C3–B3 与 C4–B4 演奏两组旋律。",
                          chord, 24, 83),
        InstrumentProfile("nightwind", "晚风圆号", "两排旋律", "两组八度 · 延音音色",
                          "两排十四键布局。C3–B3 对应 A–J，C4–B4 对应 Q–U。", two_rows, 36, 95),
        InstrumentProfile("yukele", "悠可琴", "和弦与旋律", "和弦低置 · 特殊键位",
                          "和弦位于 C2–B2；两组旋律分别使用 Q–U 与 I、O、P、[、]、\\、Num 7。",
                          yukele, 24, 83),
        InstrumentProfile("leaping", "跃律琴", "三排旋律", "三组八度 · 七声音阶",
                          "三排二十一键布局，使用标准三音区映射。", standard),
        InstrumentProfile("harmonic", "谐律键琴", "三排旋律", "三组八度 · 七声音阶",
                          "三排二十一键布局，使用标准三音区映射。", standard),
        InstrumentProfile("vintage", "老旧的诗琴", "变化音阶", "黑键直连 · 缺失音关闭",
                          "变化音直接使用钢琴黑键。游戏里不存在的音不会回退到白键，而是保持关闭。", old_lyre),
        InstrumentProfile("string_drum", "绮筵之鼓", "打击乐", "四个鼓点",
                          "四个鼓点分布到 C、D、A、B，分别触发 A、S、K、L。",
                          {48: "a", 50: "s", 57: "k", 59: "l"}, 48, 71),
        InstrumentProfile("juju_drum", "聚聚鼓", "打击乐", "两组四个鼓点",
                          "低组使用 A、S、K、L，高组使用 Q、W、I、O。",
                          {48: "a", 50: "s", 57: "k", 59: "l", 60: "q", 62: "w", 69: "i", 71: "o"},
                          48, 83),
    ]
    return {profile.id: profile for profile in profiles}


PROFILES = build_profiles()

PROFILE_TEXT = {
    "en": {
        "windsong": ("Windsong Lyre", "Three-row melody", "Three octaves · diatonic", "Classic 21-key layout: low, middle, and high ranges use Z–M, A–J, and Q–U."),
        "euphonium": ('"Lingering Euphonia"', "Chords & melody", "Seven chords · two melody rows", "Chords sit one physical octave below the melody: C2–B2 triggers Q–U; C3–B3 and C4–B4 play the two melody rows."),
        "nightwind": ("Nightwind Horn", "Two-row melody", "Two octaves · sustained tone", "Fourteen-key layout: C3–B3 maps to A–J and C4–B4 maps to Q–U."),
        "yukele": ("Ukulele", "Chords & melody", "Low chords · extended keys", "Chords use C2–B2. Melody rows use Q–U and I, O, P, [, ], \\, Num 7."),
        "leaping": ("Leaping Spirit Piano", "Three-row melody", "Three octaves · diatonic", "Standard three-range, 21-key mapping."),
        "harmonic": ("Harmonic Keys", "Three-row melody", "Three octaves · diatonic", "Standard three-range, 21-key mapping."),
        "vintage": ("Vintage Lyre", "Chromatic scale", "Direct accidentals · missing notes off", "Accidentals map directly to black keys. Notes absent from the game remain disabled."),
        "string_drum": ("Festive Drum", "Percussion", "Four drum hits", "Four hits on C, D, A, and B trigger A, S, K, and L."),
        "juju_drum": ("Djem Djem Drum", "Percussion", "Two groups of four hits", "The low group uses A, S, K, L; the high group uses Q, W, I, O."),
    },
    "es": {
        "windsong": ("Lira de la brisa", "Melodía de tres filas", "Tres octavas · escala diatónica", "Distribución clásica de 21 teclas: Z–M, A–J y Q–U para los registros grave, medio y agudo."),
        "euphonium": ("Eufonía persistente", "Acordes y melodía", "Siete acordes · dos filas melódicas", "Los acordes están una octava física bajo la melodía: C2–B2 activa Q–U; C3–B3 y C4–B4 tocan las melodías."),
        "nightwind": ("Trompa cefironocturna", "Melodía de dos filas", "Dos octavas · sonido sostenido", "Distribución de catorce teclas: C3–B3 usa A–J y C4–B4 usa Q–U."),
        "yukele": ("Ukelele", "Acordes y melodía", "Acordes graves · teclas especiales", "Los acordes usan C2–B2. Las melodías usan Q–U e I, O, P, [, ], \\, Num 7."),
        "leaping": ("Piano animaespíritu", "Melodía de tres filas", "Tres octavas · escala diatónica", "Asignación estándar de 21 teclas en tres registros."),
        "harmonic": ("Teclado armónico", "Melodía de tres filas", "Tres octavas · escala diatónica", "Asignación estándar de 21 teclas en tres registros."),
        "vintage": ("Lira antigua", "Escala cromática", "Alteraciones directas · notas ausentes desactivadas", "Las alteraciones se asignan a teclas negras. Las notas que no existen en el juego quedan desactivadas."),
        "string_drum": ("Tambor del festín", "Percusión", "Cuatro golpes", "Cuatro golpes en C, D, A y B activan A, S, K y L."),
        "juju_drum": ("Tambor Yemyem", "Percusión", "Dos grupos de cuatro golpes", "El grupo grave usa A, S, K, L; el agudo usa Q, W, I, O."),
    },
    "ja": {
        "windsong": ("風吹きのライアー", "3段メロディ", "3オクターブ · 7音音階", "21キーの標準配置。低・中・高音域はZ–M、A–J、Q–Uに対応します。"),
        "euphonium": ("「余韻」", "コードとメロディ", "7コード · 2段メロディ", "コードはメロディより1オクターブ下に配置。C2–B2でQ–U、C3–B3とC4–B4で2段のメロディを演奏します。"),
        "nightwind": ("ナイトウィンド・ホルン", "2段メロディ", "2オクターブ · 持続音", "14キー配置。C3–B3はA–J、C4–B4はQ–Uに対応します。"),
        "yukele": ("ウクレレ", "コードとメロディ", "低音コード · 特殊キー", "コードはC2–B2。メロディはQ–UとI、O、P、[、]、\\、Num 7を使用します。"),
        "leaping": ("ホッピングピアノ", "3段メロディ", "3オクターブ · 7音音階", "3音域、21キーの標準マッピングです。"),
        "harmonic": ("諧律のチェンバロ", "3段メロディ", "3オクターブ · 7音音階", "3音域、21キーの標準マッピングです。"),
        "vintage": ("古びたライアー", "変化音階", "黒鍵を直接使用 · 存在しない音はオフ", "変化音を黒鍵へ直接割り当てます。ゲームに存在しない音は無効のままです。"),
        "string_drum": ("綺宴の鼓", "打楽器", "4つの打音", "C、D、A、Bの4音でA、S、K、Lを入力します。"),
        "juju_drum": ("ジャンベ", "打楽器", "4音×2グループ", "低音グループはA、S、K、L、高音グループはQ、W、I、Oを使用します。"),
    },
}


@dataclass
class Config:
    language: str = "zh"
    language_selected: bool = False
    midi_port: str = ""
    profile_id: str = "windsong"
    octave_shift: int = 0
    transpose: int = 0
    velocity_threshold: int = 1
    sustain_enabled: bool = True
    map_black_keys_to_white: bool = True
    black_key_direction: str = "left"
    fold_outer_octaves: bool = True
    profile_overrides: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Config":
        try:
            raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            allowed = {item.name for item in fields(cls)}
            config = cls(**{key: value for key, value in raw.items() if key in allowed})
            if config.profile_id not in PROFILES:
                config.profile_id = "windsong"
            if config.language not in LANGUAGES:
                config.language = "zh"
            if config.black_key_direction not in {"left", "right"}:
                config.black_key_direction = "left"
            if not isinstance(config.profile_overrides, dict):
                config.profile_overrides = {}
            return config
        except FileNotFoundError:
            return cls()
        except Exception:
            logging.exception("Could not load config")
            return cls()

    def save(self) -> None:
        CONFIG_FILE.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT), ("hi", _HARDWAREINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]


class KeySender:
    INPUT_KEYBOARD, KEYEVENTF_KEYUP, KEYEVENTF_SCANCODE = 1, 0x0002, 0x0008
    SCAN_CODES = {
        "q": 0x10, "w": 0x11, "e": 0x12, "r": 0x13, "t": 0x14, "y": 0x15, "u": 0x16,
        "i": 0x17, "o": 0x18, "p": 0x19, "lbracket": 0x1A, "rbracket": 0x1B,
        "a": 0x1E, "s": 0x1F, "d": 0x20, "f": 0x21, "g": 0x22, "h": 0x23,
        "j": 0x24, "k": 0x25, "l": 0x26, "backslash": 0x2B,
        "z": 0x2C, "x": 0x2D, "c": 0x2E, "v": 0x2F, "b": 0x30, "n": 0x31, "m": 0x32,
        "num7": 0x47,
    }

    def send(self, key: str, down: bool) -> None:
        flags = self.KEYEVENTF_SCANCODE | (0 if down else self.KEYEVENTF_KEYUP)
        event = _INPUT(type=self.INPUT_KEYBOARD,
                       union=_INPUT_UNION(ki=_KEYBDINPUT(0, self.SCAN_CODES[key], flags, 0, None)))
        if ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
            raise ctypes.WinError()


class MidiBridge:
    def __init__(self, config: Config, events: queue.Queue):
        self.config, self.events = config, events
        self.midi: rtmidi.MidiIn | None = None
        self.port_name, self.enabled, self.sustain = "", False, False
        self.sender, self.lock = KeySender(), threading.RLock()
        self.source_to_key: dict[int, str] = {}
        self.key_refcount: dict[str, int] = {}
        self.deferred_off: set[int] = set()

    @staticmethod
    def ports() -> list[str]:
        probe = rtmidi.MidiIn()
        try:
            return probe.get_ports()
        finally:
            del probe

    def profile_mapping(self) -> dict[int, str]:
        mapping = dict(PROFILES[self.config.profile_id].mapping)
        for note_text, key in self.config.profile_overrides.get(self.config.profile_id, {}).items():
            try:
                note = int(note_text)
            except ValueError:
                continue
            if key:
                mapping[note] = key
            else:
                mapping.pop(note, None)
        return mapping

    def map_note(self, note: int) -> str | None:
        note += self.config.transpose + self.config.octave_shift * 12
        mapping = self.profile_mapping()
        if note in mapping:
            return mapping[note]
        melodic_profiles = {"windsong", "euphonium", "nightwind", "yukele", "leaping", "harmonic"}
        if (self.config.map_black_keys_to_white
                and self.config.profile_id in melodic_profiles
                and note % 12 not in WHITE_PCS):
            step = -1 if self.config.black_key_direction == "left" else 1
            for adjacent in (note + step, note - step):
                if adjacent in mapping:
                    return mapping[adjacent]
            # Outside the displayed range there is no adjacent mapped key yet;
            # quantize downward first so octave folding can find the matching white key.
            note += step
        if not self.config.fold_outer_octaves:
            return None
        if mapping and min(mapping) <= note <= max(mapping):
            return None
        candidates = [mapped for mapped in mapping if mapped % 12 == note % 12 and abs(mapped - note) <= 24]
        return mapping[min(candidates, key=lambda mapped: abs(mapped - note))] if candidates else None

    def connect(self, port_name: str) -> None:
        with self.lock:
            self.disconnect()
            ports = self.ports()
            if port_name not in ports:
                raise RuntimeError("找不到所选 MIDI 设备，请刷新后重试。")
            midi = rtmidi.MidiIn()
            midi.ignore_types(sysex=True, timing=True, active_sense=True)
            midi.open_port(ports.index(port_name), port_name)
            midi.set_callback(self._callback)
            self.midi, self.port_name = midi, port_name
            self.events.put(("connection", True, port_name))
            logging.info("Connected to MIDI port %s", port_name)

    def disconnect(self) -> None:
        self.set_enabled(False)
        if self.midi is not None:
            try:
                self.midi.cancel_callback()
                self.midi.close_port()
            except Exception:
                logging.exception("Error closing MIDI port")
            self.midi = None
        if self.port_name:
            self.events.put(("connection", False, self.port_name))
        self.port_name = ""

    def set_enabled(self, value: bool) -> None:
        with self.lock:
            if not value:
                self._release_all()
            self.enabled = bool(value and self.midi is not None)
            self.events.put(("enabled", self.enabled))

    def set_profile(self, profile_id: str) -> None:
        with self.lock:
            self._release_all()
            self.config.profile_id = profile_id
            self.config.save()

    def _callback(self, event, _data=None) -> None:
        try:
            message, _delta = event
            if not message:
                return
            status = message[0] & 0xF0
            if status == 0x90 and len(message) >= 3 and message[2] > 0:
                self._note_on(message[1], message[2])
            elif status in (0x80, 0x90) and len(message) >= 3:
                self._note_off(message[1])
            elif status == 0xB0 and len(message) >= 3 and message[1] == 64:
                self._sustain(message[2] >= 64)
        except Exception as exc:
            logging.exception("MIDI callback failed")
            self.events.put(("error", f"处理 MIDI 消息失败：{exc}"))

    def _note_on(self, note: int, velocity: int) -> None:
        with self.lock:
            self.events.put(("midi", note, velocity))
            if not self.enabled or velocity < self.config.velocity_threshold:
                return
            key = self.map_note(note)
            repeated_key = self.source_to_key.get(note) == key and key is not None
            if note in self.source_to_key:
                self._release_source(note)
            if key is None:
                self.events.put(("ignored", note))
                return
            self.deferred_off.discard(note)
            self.source_to_key[note] = key
            count = self.key_refcount.get(key, 0)
            self.key_refcount[key] = count + 1
            if repeated_key:
                # Games sample keyboard state once per frame. Keep the key up long
                # enough for a repeated sustained note to register as a new press.
                if count > 0:
                    self.sender.send(key, False)
                time.sleep(0.025)
                self.sender.send(key, True)
            elif count == 0:
                self.sender.send(key, True)
            self.events.put(("played", note, key, True))

    def _note_off(self, note: int) -> None:
        with self.lock:
            if self.config.sustain_enabled and self.sustain and note in self.source_to_key:
                self.deferred_off.add(note)
            else:
                self._release_source(note)

    def _release_source(self, note: int) -> None:
        key = self.source_to_key.pop(note, None)
        self.deferred_off.discard(note)
        if key is None:
            return
        count = self.key_refcount.get(key, 0) - 1
        if count <= 0:
            self.key_refcount.pop(key, None)
            self.sender.send(key, False)
        else:
            self.key_refcount[key] = count
        self.events.put(("played", note, key, False))

    def _sustain(self, down: bool) -> None:
        with self.lock:
            self.sustain = down
            self.events.put(("sustain", down))
            if not down:
                for note in list(self.deferred_off):
                    self._release_source(note)

    def _release_all(self) -> None:
        for key in list(self.key_refcount):
            try:
                self.sender.send(key, False)
            except Exception:
                logging.exception("Failed to release %s", key)
        self.source_to_key.clear()
        self.key_refcount.clear()
        self.deferred_off.clear()
        self.sustain = False


class GlobalHotkey(threading.Thread):
    WM_HOTKEY, WM_QUIT = 0x0312, 0x0012
    MOD_ALT, MOD_CONTROL, VK_F8, HOTKEY_ID = 0x0001, 0x0002, 0x77, 0xB145

    def __init__(self, on_toggle, events: queue.Queue):
        super().__init__(daemon=True, name="GlobalHotkey")
        self.on_toggle, self.events, self.thread_id = on_toggle, events, 0

    def run(self) -> None:
        user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
        self.thread_id = kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, self.HOTKEY_ID, self.MOD_CONTROL | self.MOD_ALT, self.VK_F8):
            self.events.put(("hotkey_error",))
            return
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == self.WM_HOTKEY and msg.wParam == self.HOTKEY_ID:
                    self.on_toggle()
        finally:
            user32.UnregisterHotKey(None, self.HOTKEY_ID)

    def stop(self) -> None:
        if self.thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.thread_id, self.WM_QUIT, 0, 0)


def note_name(note: int) -> str:
    return f"{NOTE_NAMES[note % 12]}{note // 12 - 1}"


class PianoWidget(QWidget):
    note_selected = Signal(int)
    WHITE_W, WHITE_H, BLACK_W, BLACK_H = 40, 238, 26, 145

    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_note, self.end_note, self.selected = 24, 107, 60
        self.mapping: dict[int, str] = {}
        self.hit_regions: list[tuple[QRectF, int]] = []
        self.setFixedSize(1962, self.WHITE_H + 38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_profile(self, profile: InstrumentProfile, mapping: dict[int, str]) -> None:
        self.start_note, self.end_note, self.mapping = profile.display_from, profile.display_to, mapping
        count = sum(1 for note in range(self.start_note, self.end_note + 1) if note % 12 in WHITE_PCS)
        self.setFixedSize(max(count * self.WHITE_W + 2, 760), self.WHITE_H + 38)
        if not self.start_note <= self.selected <= self.end_note:
            self.selected = self.start_note
        self.update()

    def set_selected(self, note: int) -> None:
        self.selected = note
        self.update()

    def x_for_note(self, note: int) -> int:
        """Return the horizontal centre of a MIDI note in the rendered keyboard."""
        white_before = sum(
            1 for current in range(self.start_note, min(note, self.end_note + 1))
            if current % 12 in WHITE_PCS
        )
        if note % 12 in WHITE_PCS:
            return white_before * self.WHITE_W + self.WHITE_W // 2
        return max(0, white_before * self.WHITE_W)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#111319"))
        self.hit_regions.clear()
        white_x: dict[int, float] = {}
        white_index = 0
        for note in range(self.start_note, self.end_note + 1):
            if note % 12 not in WHITE_PCS:
                continue
            x = white_index * self.WHITE_W + 1
            white_x[note] = x
            rect = QRectF(x, 8, self.WHITE_W - 2, self.WHITE_H)
            painter.setPen(QPen(QColor("#303540"), 1))
            painter.setBrush(QColor("#B8C7FF") if note == self.selected else QColor("#F5F5F3"))
            painter.drawRoundedRect(rect, 6, 6)
            key = self.mapping.get(note)
            painter.setPen(QColor("#17191F") if key else QColor("#9A9EA8"))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            painter.drawText(QRectF(x, self.WHITE_H - 12, self.WHITE_W - 2, 22),
                             Qt.AlignmentFlag.AlignCenter, GAME_KEY_LABELS.get(key, ""))
            painter.setFont(QFont("Segoe UI", 7))
            painter.drawText(QRectF(x, self.WHITE_H + 9, self.WHITE_W - 2, 18),
                             Qt.AlignmentFlag.AlignCenter, note_name(note))
            self.hit_regions.append((rect, note))
            white_index += 1
        for note in range(self.start_note, self.end_note + 1):
            if note % 12 in WHITE_PCS or note - 1 not in white_x:
                continue
            x = white_x[note - 1] + self.WHITE_W - self.BLACK_W / 2 - 1
            rect = QRectF(x, 8, self.BLACK_W, self.BLACK_H)
            key = self.mapping.get(note)
            painter.setPen(QPen(QColor("#111319"), 1))
            painter.setBrush(QColor("#758BFF") if note == self.selected else QColor("#242832"))
            painter.drawRoundedRect(rect, 5, 5)
            painter.setPen(QColor("#FFFFFF") if key else QColor("#777D89"))
            painter.setFont(QFont("Segoe UI", 7, QFont.Weight.DemiBold))
            painter.drawText(QRectF(x, self.BLACK_H - 8, self.BLACK_W, 20),
                             Qt.AlignmentFlag.AlignCenter, GAME_KEY_LABELS.get(key, ""))
            self.hit_regions.append((rect, note))
        painter.end()

    def mousePressEvent(self, event) -> None:
        for rect, note in reversed(self.hit_regions):
            if rect.contains(event.position()):
                self.selected = note
                self.note_selected.emit(note)
                self.update()
                return


class TitleBar(QWidget):
    def __init__(self, window: "MainWindow"):
        super().__init__(window)
        self.window_ref, self.drag_pos = window, None
        self.setObjectName("titleBar")
        self.setFixedHeight(48)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 8, 0)
        title = QLabel("Genshin MIDI Bridge")
        title.setObjectName("appTitle")
        layout.addWidget(title)
        layout.addStretch()
        for text, action, name in (("—", window.showMinimized, "windowButton"),
                                   ("□", self.toggle_maximize, "windowButton"),
                                   ("×", window.close, "closeButton")):
            button = QPushButton(text)
            button.setObjectName(name)
            button.setFixedSize(42, 34)
            button.clicked.connect(action)
            layout.addWidget(button)

    def toggle_maximize(self) -> None:
        self.window_ref.showNormal() if self.window_ref.isMaximized() else self.window_ref.showMaximized()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.window_ref.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:
        if self.drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if self.window_ref.isMaximized():
                self.window_ref.showNormal()
            self.window_ref.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, _event) -> None:
        self.drag_pos = None

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()


def card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(12)
    return frame, layout


def page_header(title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(34, 28, 34, 30)
    layout.setSpacing(16)
    heading = QLabel(title)
    heading.setObjectName("pageTitle")
    detail = QLabel(subtitle)
    detail.setObjectName("muted")
    layout.addWidget(heading)
    layout.addWidget(detail)
    return page, layout


class LanguageDialog(QDialog):
    """One-time language chooser shown before the main window."""

    def __init__(self, current_language: str = "zh"):
        super().__init__()
        self.language = current_language if current_language in LANGUAGES else "zh"
        self.setWindowTitle("Genshin MIDI Bridge")
        self.setModal(True)
        self.setFixedSize(420, 330)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(38, 32, 38, 32)
        layout.setSpacing(12)
        heading = QLabel("Choose your language")
        heading.setObjectName("languageHeading")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("选择语言  ·  Elegir idioma  ·  言語を選択")
        subtitle.setObjectName("languageSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        for code, label in LANGUAGES.items():
            button = QPushButton(label)
            button.setProperty("selected", code == self.language)
            button.clicked.connect(lambda _checked=False, value=code: self.select_language(value))
            layout.addWidget(button)
        self.setStyleSheet("""
            QDialog { background: #111319; }
            QLabel { color: #F1F3F7; font-family: "Segoe UI Variable", "Microsoft YaHei UI"; }
            #languageHeading { font-size: 23px; font-weight: 700; }
            #languageSubtitle { color: #969DAB; font-size: 13px; }
            QPushButton { background: #232730; color: #E8EBF2; border: 1px solid #353A46;
                          border-radius: 9px; padding: 10px; font-size: 14px; }
            QPushButton:hover { background: #2D323E; border-color: #6577FF; }
            QPushButton[selected="true"] { background: #6577FF; color: white; border-color: #6577FF; }
        """)

    def select_language(self, language: str) -> None:
        self.language = language
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, config: Config | None = None):
        super().__init__()
        self.setWindowTitle("Genshin MIDI Bridge")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1100, 720)
        self.setMinimumSize(820, 560)
        self.config = config or Config.load()
        self.events: queue.Queue = queue.Queue()
        self.bridge = MidiBridge(self.config, self.events)
        self.connected, self.selected_note = False, 60
        shell = QFrame()
        shell.setObjectName("windowShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(TitleBar(self))
        shell_layout.addWidget(self._build_body(), 1)
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 4, 4)
        grip_row.addStretch()
        grip_row.addWidget(QSizeGrip(shell))
        shell_layout.addLayout(grip_row)
        self.setCentralWidget(shell)
        self._apply_styles()
        self._retranslate_ui()
        self._sync_profile_ui()
        self.refresh_ports(auto_connect=True)
        self.hotkey = GlobalHotkey(lambda: self.events.put(("toggle",)), self.events)
        self.hotkey.start()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._drain_events)
        self.timer.start(30)

    def _build_body(self) -> QWidget:
        body = QWidget()
        body.setObjectName("body")
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        self.pages = QStackedWidget()
        self.home_page = self._build_home()
        self.instrument_page = self._build_instruments()
        self.settings_page = self._build_settings()
        for page in (self.home_page, self.instrument_page, self.settings_page):
            self.pages.addWidget(page)
        layout.addWidget(self.pages, 1)
        return body

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(176)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 22, 14, 18)
        layout.setSpacing(8)
        brand = QLabel("MB")
        brand.setObjectName("brand")
        layout.addWidget(brand)
        layout.addSpacing(18)
        self.nav_buttons = []
        for index, (label, symbol) in enumerate((("主页", "●"), ("乐器", "♬"), ("设置", "⚙"))):
            button = QPushButton(f"{symbol}   {label}")
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, page=index: self._show_page(page))
            layout.addWidget(button)
            self.nav_buttons.append(button)
        self.nav_buttons[0].setChecked(True)
        layout.addStretch()
        self.about_button = QPushButton("?   关于")
        self.about_button.setObjectName("navButton")
        self.about_button.clicked.connect(self.show_manual)
        layout.addWidget(self.about_button)
        return sidebar

    def _build_home(self) -> QWidget:
        page, layout = page_header("准备演奏", "选择乐器，连接 MIDI，然后开始。")
        self.home_heading, self.home_subtitle = page.findChildren(QLabel)[:2]
        device, device_layout = card()
        row = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(260)
        row.addWidget(self.port_combo, 1)
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.clicked.connect(self.refresh_ports)
        row.addWidget(self.refresh_button)
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.toggle_connection)
        row.addWidget(self.connect_button)
        device_layout.addLayout(row)
        layout.addWidget(device)
        perform, perform_layout = card()
        top = QHBoxLayout()
        labels = QVBoxLayout()
        self.profile_title = QLabel()
        self.profile_title.setObjectName("sectionTitle")
        self.profile_summary = QLabel()
        self.profile_summary.setObjectName("muted")
        labels.addWidget(self.profile_title)
        labels.addWidget(self.profile_summary)
        top.addLayout(labels, 1)
        self.profile_combo_home = QComboBox()
        self._fill_profiles(self.profile_combo_home)
        self.profile_combo_home.currentIndexChanged.connect(
            lambda: self.change_profile(self.profile_combo_home.currentData()))
        top.addWidget(self.profile_combo_home)
        perform_layout.addLayout(top)
        action = QHBoxLayout()
        self.enable_button = QPushButton("开始映射")
        self.enable_button.setObjectName("primaryAction")
        self.enable_button.setEnabled(False)
        self.enable_button.clicked.connect(self.toggle_enabled)
        action.addWidget(self.enable_button)
        hotkey = QLabel("Ctrl  +  Alt  +  F8")
        hotkey.setObjectName("shortcut")
        action.addWidget(hotkey)
        action.addStretch()
        perform_layout.addLayout(action)
        layout.addWidget(perform)
        status, status_layout = card()
        self.status_label = QLabel("未连接")
        self.status_label.setObjectName("statusTitle")
        self.live_label = QLabel("等待 MIDI 输入")
        self.live_label.setObjectName("liveText")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.live_label)
        layout.addWidget(status)
        layout.addStretch()
        return page

    def _build_instruments(self) -> QWidget:
        page, layout = page_header("乐器与键位", "选择模式；点击琴键可以覆盖当前预设。")
        self.instrument_heading, self.instrument_subtitle = page.findChildren(QLabel)[:2]
        row = QHBoxLayout()
        self.profile_combo_instrument = QComboBox()
        self._fill_profiles(self.profile_combo_instrument)
        self.profile_combo_instrument.currentIndexChanged.connect(
            lambda: self.change_profile(self.profile_combo_instrument.currentData()))
        row.addWidget(self.profile_combo_instrument)
        self.info_button = QPushButton("乐器简介")
        self.info_button.setObjectName("secondaryButton")
        self.info_button.clicked.connect(self.show_profile_info)
        row.addWidget(self.info_button)
        row.addStretch()
        layout.addLayout(row)
        keyboard_card, keyboard_layout = card()
        self.keyboard_scroll = QScrollArea()
        self.keyboard_scroll.setWidgetResizable(False)
        self.keyboard_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.keyboard_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.keyboard_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.piano = PianoWidget()
        self.piano.note_selected.connect(self.select_note)
        self.keyboard_scroll.setWidget(self.piano)
        keyboard_layout.addWidget(self.keyboard_scroll)
        edit_row = QHBoxLayout()
        self.selected_note_label = QLabel("C4")
        self.selected_note_label.setObjectName("selectedNote")
        edit_row.addWidget(self.selected_note_label)
        self.map_to_label = QLabel("映射到")
        edit_row.addWidget(self.map_to_label)
        self.key_combo = QComboBox()
        self.key_combo.addItem("关闭", "")
        for key, label in GAME_KEY_LABELS.items():
            self.key_combo.addItem(label, key)
        self.key_combo.currentIndexChanged.connect(self.update_selected_mapping)
        edit_row.addWidget(self.key_combo)
        self.reset_button = QPushButton("恢复此模式默认值")
        self.reset_button.setObjectName("secondaryButton")
        self.reset_button.clicked.connect(self.reset_profile_mapping)
        edit_row.addStretch()
        edit_row.addWidget(self.reset_button)
        keyboard_layout.addLayout(edit_row)
        layout.addWidget(keyboard_card, 1)
        return page

    def _build_settings(self) -> QWidget:
        outer = QWidget()
        outer.setObjectName("settingsOuter")
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.viewport().setObjectName("settingsViewport")
        content, layout = page_header("设置", "演奏参数与输入行为。")
        self.settings_heading, self.settings_subtitle = content.findChildren(QLabel)[:2]
        content.setObjectName("settingsContent")
        content.setMinimumHeight(760)
        pitch, pitch_layout = card()
        self.pitch_title = QLabel("音高")
        self.pitch_title.setObjectName("sectionTitle")
        pitch_layout.addWidget(self.pitch_title)
        form = QFormLayout()
        form.setSpacing(14)
        self.octave_spin = QSpinBox()
        self.octave_spin.setRange(-3, 3)
        self.octave_spin.setValue(self.config.octave_shift)
        self.transpose_spin = QSpinBox()
        self.transpose_spin.setRange(-11, 11)
        self.transpose_spin.setValue(self.config.transpose)
        self.octave_label = QLabel("八度偏移")
        self.transpose_label = QLabel("半音移调")
        form.addRow(self.octave_label, self.octave_spin)
        form.addRow(self.transpose_label, self.transpose_spin)
        pitch_layout.addLayout(form)
        layout.addWidget(pitch)
        language_card, language_layout = card()
        self.language_title = QLabel("界面语言")
        self.language_title.setObjectName("sectionTitle")
        language_layout.addWidget(self.language_title)
        self.language_combo = QComboBox()
        for code, label in LANGUAGES.items():
            self.language_combo.addItem(label, code)
        self.language_combo.setCurrentIndex(max(0, self.language_combo.findData(self.config.language)))
        self.language_combo.currentIndexChanged.connect(self.change_language)
        language_layout.addWidget(self.language_combo)
        layout.addWidget(language_card)
        behavior, behavior_layout = card()
        self.behavior_title = QLabel("输入行为")
        self.behavior_title.setObjectName("sectionTitle")
        behavior_layout.addWidget(self.behavior_title)
        self.velocity_spin = QSpinBox()
        self.velocity_spin.setRange(1, 127)
        self.velocity_spin.setValue(self.config.velocity_threshold)
        self.velocity_label = QLabel("力度门槛")
        behavior_layout.addWidget(self.velocity_label)
        behavior_layout.addWidget(self.velocity_spin)
        self.sustain_check = QCheckBox("处理延音踏板（CC64）")
        self.sustain_check.setChecked(self.config.sustain_enabled)
        self.black_keys_check = QCheckBox("把黑键映射到最近的白键")
        self.black_keys_check.setChecked(self.config.map_black_keys_to_white)
        self.black_direction_label = QLabel("黑键映射方向")
        self.black_direction_combo = QComboBox()
        self.black_direction_combo.addItem("左侧白键", "left")
        self.black_direction_combo.addItem("右侧白键", "right")
        self.black_direction_combo.setCurrentIndex(
            max(0, self.black_direction_combo.findData(self.config.black_key_direction))
        )
        self.black_direction_combo.setEnabled(self.config.map_black_keys_to_white)
        self.fold_check = QCheckBox("把外侧两个八度折叠到最近可用音区")
        self.fold_check.setChecked(self.config.fold_outer_octaves)
        behavior_layout.addWidget(self.sustain_check)
        behavior_layout.addWidget(self.black_keys_check)
        direction_row = QHBoxLayout()
        direction_row.addWidget(self.black_direction_label)
        direction_row.addStretch()
        direction_row.addWidget(self.black_direction_combo)
        behavior_layout.addLayout(direction_row)
        behavior_layout.addWidget(self.fold_check)
        layout.addWidget(behavior)
        layout.addStretch()
        for widget in (self.octave_spin, self.transpose_spin, self.velocity_spin):
            widget.valueChanged.connect(self.apply_settings)
        self.sustain_check.toggled.connect(self.apply_settings)
        self.black_keys_check.toggled.connect(self.black_direction_combo.setEnabled)
        self.black_keys_check.toggled.connect(self.apply_settings)
        self.black_direction_combo.currentIndexChanged.connect(self.apply_settings)
        self.fold_check.toggled.connect(self.apply_settings)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
        return outer

    def _fill_profiles(self, combo: QComboBox) -> None:
        for profile in PROFILES.values():
            combo.addItem(self._profile_text(profile)[0], profile.id)

    def _t(self, key: str, **values) -> str:
        return TEXT.get(self.config.language, TEXT["zh"]).get(key, TEXT["zh"].get(key, key)).format(**values)

    def _profile_text(self, profile: InstrumentProfile) -> tuple[str, str, str, str]:
        translated = PROFILE_TEXT.get(self.config.language, {}).get(profile.id)
        return translated or (profile.name, profile.category, profile.summary, profile.description)

    def change_language(self, *_args) -> None:
        language = self.language_combo.currentData()
        if language not in LANGUAGES or language == self.config.language:
            return
        self.config.language = language
        self.config.language_selected = True
        self.config.save()
        self._retranslate_ui()
        self._sync_profile_ui()

    def _retranslate_ui(self) -> None:
        nav = (("home", "●"), ("instruments", "♬"), ("settings", "⚙"))
        for button, (key, symbol) in zip(self.nav_buttons, nav, strict=True):
            button.setText(f"{symbol}   {self._t(key)}")
        self.about_button.setText(f"?   {self._t('about')}")
        self.home_heading.setText(self._t("home_title"))
        self.home_subtitle.setText(self._t("home_sub"))
        self.refresh_button.setText(self._t("refresh"))
        self.instrument_heading.setText(self._t("instrument_title"))
        self.instrument_subtitle.setText(self._t("instrument_sub"))
        self.info_button.setText(self._t("instrument_info"))
        self.map_to_label.setText(self._t("map_to"))
        self.key_combo.setItemText(0, self._t("disabled"))
        self.reset_button.setText(self._t("reset"))
        self.settings_heading.setText(self._t("settings"))
        self.settings_subtitle.setText(self._t("settings_sub"))
        self.language_title.setText(self._t("language"))
        self.pitch_title.setText(self._t("pitch"))
        self.octave_label.setText(self._t("octave"))
        self.transpose_label.setText(self._t("transpose"))
        self.behavior_title.setText(self._t("behavior"))
        self.velocity_label.setText(self._t("velocity"))
        self.sustain_check.setText(self._t("sustain"))
        self.black_keys_check.setText(self._t("black_keys"))
        self.black_direction_label.setText(self._t("black_direction"))
        self.black_direction_combo.setItemText(0, self._t("black_left"))
        self.black_direction_combo.setItemText(1, self._t("black_right"))
        self.fold_check.setText(self._t("fold"))
        for combo in (self.profile_combo_home, self.profile_combo_instrument):
            for index, profile in enumerate(PROFILES.values()):
                combo.setItemText(index, self._profile_text(profile)[0])
        self.connect_button.setText(self._t("disconnect" if self.connected else "connect"))
        self.enable_button.setText(self._t("stop" if self.bridge.enabled else "start"))
        self.status_label.setText(self._t("mapping" if self.bridge.enabled else ("connected" if self.connected else "not_connected")))
        if not self.bridge.enabled and not self.connected:
            self.live_label.setText(self._t("waiting"))

    def _show_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

    def current_mapping(self) -> dict[int, str]:
        return self.bridge.profile_mapping()

    def _sync_profile_ui(self) -> None:
        profile = PROFILES[self.config.profile_id]
        name, category, summary, _description = self._profile_text(profile)
        for combo in (self.profile_combo_home, self.profile_combo_instrument):
            combo.blockSignals(True)
            combo.setCurrentIndex(combo.findData(profile.id))
            combo.blockSignals(False)
        self.profile_title.setText(name)
        self.profile_summary.setText(f"{category}  ·  {summary}")
        self.piano.set_profile(profile, self.current_mapping())
        self.select_note(self.piano.selected)

    def change_profile(self, profile_id: str | None) -> None:
        if profile_id and profile_id != self.config.profile_id:
            self.bridge.set_profile(profile_id)
            self._sync_profile_ui()

    def select_note(self, note: int) -> None:
        self.selected_note = note
        self.selected_note_label.setText(f"{note_name(note)}   MIDI {note}")
        index = self.key_combo.findData(self.current_mapping().get(note, ""))
        self.key_combo.blockSignals(True)
        self.key_combo.setCurrentIndex(max(index, 0))
        self.key_combo.blockSignals(False)
        self.piano.set_selected(note)
        QTimer.singleShot(
            0,
            lambda: self.keyboard_scroll.ensureVisible(
                self.piano.x_for_note(note), self.piano.height() // 2, 130, 10
            ),
        )

    def update_selected_mapping(self) -> None:
        key = self.key_combo.currentData()
        overrides = self.config.profile_overrides.setdefault(self.config.profile_id, {})
        default = PROFILES[self.config.profile_id].mapping.get(self.selected_note, "")
        if key == default:
            overrides.pop(str(self.selected_note), None)
        else:
            overrides[str(self.selected_note)] = key
        self.config.save()
        self.piano.set_profile(PROFILES[self.config.profile_id], self.current_mapping())

    def reset_profile_mapping(self) -> None:
        self.config.profile_overrides.pop(self.config.profile_id, None)
        self.config.save()
        self._sync_profile_ui()

    def refresh_ports(self, auto_connect: bool = False) -> None:
        try:
            current = self.port_combo.currentText() or self.config.midi_port
            ports = self.bridge.ports()
            self.port_combo.clear()
            self.port_combo.addItems(ports)
            if current in ports:
                self.port_combo.setCurrentText(current)
            if not ports:
                self.status_label.setText(self._t("no_device"))
            elif auto_connect and self.config.midi_port in ports:
                self.connect_device()
        except Exception as exc:
            self.show_error(self._t("enumerate_error", error=exc))

    def toggle_connection(self) -> None:
        self.bridge.disconnect() if self.connected else self.connect_device()

    def connect_device(self) -> None:
        name = self.port_combo.currentText()
        if not name:
            QMessageBox.information(self, "Genshin MIDI Bridge", self._t("choose_device"))
            return
        try:
            self.bridge.connect(name)
            self.connected = True
            self.config.midi_port = name
            self.config.save()
            self.connect_button.setText(self._t("disconnect"))
            self.enable_button.setEnabled(True)
            self.status_label.setText(self._t("connected"))
        except Exception as exc:
            logging.exception("Connection failed")
            message = self._t("device_missing") if "找不到所选 MIDI 设备" in str(exc) else str(exc)
            self.show_error(message)

    def apply_settings(self, *_args) -> None:
        self.config.octave_shift = self.octave_spin.value()
        self.config.transpose = self.transpose_spin.value()
        self.config.velocity_threshold = self.velocity_spin.value()
        self.config.sustain_enabled = self.sustain_check.isChecked()
        self.config.map_black_keys_to_white = self.black_keys_check.isChecked()
        self.config.black_key_direction = self.black_direction_combo.currentData()
        self.config.fold_outer_octaves = self.fold_check.isChecked()
        self.config.save()

    def toggle_enabled(self) -> None:
        self.bridge.set_enabled(not self.bridge.enabled)

    def _drain_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "toggle":
                    self.toggle_enabled()
                elif kind == "enabled":
                    enabled = event[1]
                    self.enable_button.setText(self._t("stop" if enabled else "start"))
                    self.enable_button.setProperty("active", enabled)
                    self.enable_button.style().unpolish(self.enable_button)
                    self.enable_button.style().polish(self.enable_button)
                    self.status_label.setText(self._t("mapping" if enabled else ("connected" if self.connected else "not_connected")))
                elif kind == "connection" and not event[1]:
                    self.connected = False
                    self.connect_button.setText(self._t("connect"))
                    self.enable_button.setEnabled(False)
                elif kind == "midi":
                    self.live_label.setText(f"MIDI {event[1]}   {self._t('velocity_live')} {event[2]}")
                elif kind == "played":
                    action = self._t("press" if event[3] else "release")
                    self.live_label.setText(f"{note_name(event[1])}  →  {GAME_KEY_LABELS[event[2]]}   {action}")
                elif kind == "ignored":
                    self.live_label.setText(f"{note_name(event[1])}  ·  {self._t('unmapped')}")
                elif kind == "sustain":
                    self.live_label.setText(self._t("pedal_down" if event[1] else "pedal_up"))
                elif kind == "hotkey_error":
                    self.live_label.setText(self._t("hotkey_busy"))
                elif kind == "error":
                    raw = str(event[1])
                    detail = raw.split("：", 1)[-1] if "处理 MIDI 消息失败" in raw else raw
                    self.show_error(self._t("midi_error", error=detail))
        except queue.Empty:
            pass

    def show_profile_info(self) -> None:
        profile = PROFILES[self.config.profile_id]
        name, _category, _summary, description = self._profile_text(profile)
        dialog = QDialog(self)
        dialog.setWindowTitle(name)
        dialog.setModal(True)
        dialog.setMinimumWidth(420)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(26, 24, 26, 24)
        title = QLabel(name)
        title.setObjectName("pageTitle")
        detail = QLabel(description)
        detail.setWordWrap(True)
        detail.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(detail)
        close = QPushButton(self._t("got_it"))
        close.clicked.connect(dialog.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
        dialog.exec()

    def show_manual(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(self._t("manual_title"))
        dialog.resize(680, 640)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 20, 22, 20)
        title = QLabel(self._t("manual_title"))
        title.setObjectName("pageTitle")
        guide = QTextBrowser()
        guide.setOpenExternalLinks(True)
        guide.setHtml(MANUAL_HTML.get(self.config.language, MANUAL_HTML["zh"]))
        close = QPushButton(self._t("got_it"))
        close.clicked.connect(dialog.accept)
        layout.addWidget(title)
        layout.addWidget(guide, 1)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
        dialog.exec()

    def show_error(self, message: str) -> None:
        self.status_label.setText(self._t("error"))
        QMessageBox.critical(self, "Genshin MIDI Bridge", message)

    def closeEvent(self, event) -> None:
        try:
            self.apply_settings()
            self.bridge.disconnect()
            self.hotkey.stop()
        finally:
            event.accept()

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            * { font-family: "Segoe UI Variable", "Microsoft YaHei UI"; font-size: 14px; color: #F1F3F7; }
            QMainWindow { background: transparent; }
            #windowShell { background: #111319; border: 1px solid #2A2E38; border-radius: 14px; }
            #titleBar { background: #151820; border-top-left-radius: 14px; border-top-right-radius: 14px; }
            #appTitle { font-size: 14px; font-weight: 650; color: #DDE1EB; }
            #windowButton, #closeButton { border: none; background: transparent; color: #AEB4C2; font-size: 16px; }
            #windowButton:hover { background: #272B35; border-radius: 7px; color: white; }
            #closeButton:hover { background: #E5484D; border-radius: 7px; color: white; }
            #body { background: #111319; }
            #settingsOuter, #settingsContent, #settingsViewport { background: #111319; }
            #sidebar { background: #151820; border-right: 1px solid #242832; }
            #brand { background: #6577FF; color: white; border-radius: 12px; font-weight: 800; font-size: 16px;
                     min-width: 42px; max-width: 42px; min-height: 42px; max-height: 42px; qproperty-alignment: AlignCenter; }
            #navButton { text-align: left; border: none; background: transparent; color: #989FAD;
                         padding: 11px 13px; border-radius: 9px; font-weight: 550; }
            #navButton:hover { background: #20242D; color: #E8EBF2; }
            #navButton:checked { background: #292E3B; color: #FFFFFF; }
            #pageTitle { font-size: 26px; font-weight: 720; color: #F7F8FA; }
            #sectionTitle { font-size: 17px; font-weight: 680; color: #F4F5F8; }
            #muted { color: #969DAB; }
            #card { background: #191C24; border: 1px solid #292D38; border-radius: 14px; }
            #statusTitle { font-size: 19px; font-weight: 680; color: #FFFFFF; }
            #liveText { color: #AEB4C2; font-family: "Cascadia Mono", "Consolas"; }
            #shortcut { color: #B8C1FF; background: #252A3B; border: 1px solid #353C5A;
                        border-radius: 9px; padding: 10px 14px; font-family: "Cascadia Mono", "Consolas"; }
            #selectedNote { font-size: 17px; font-weight: 700; color: #B8C7FF; min-width: 150px; }
            QPushButton { background: #6577FF; color: white; border: none; border-radius: 9px;
                          padding: 10px 17px; font-weight: 650; }
            QPushButton:hover { background: #7485FF; }
            QPushButton:pressed { background: #5668E8; }
            QPushButton:disabled { background: #30343F; color: #737987; }
            #secondaryButton { background: #242832; color: #D7DAE2; border: 1px solid #353A47; }
            #secondaryButton:hover { background: #2D323E; }
            #primaryAction { min-width: 130px; font-size: 15px; padding: 12px 22px; }
            #primaryAction[active="true"] { background: #D65C67; }
            QComboBox, QSpinBox { background: #232730; border: 1px solid #353A46; border-radius: 8px;
                                  padding: 9px 12px; min-height: 20px; selection-background-color: #6577FF; }
            QComboBox:hover, QSpinBox:hover { border-color: #586178; }
            QComboBox::drop-down { border: none; width: 28px; }
            QComboBox QAbstractItemView { background: #20242C; border: 1px solid #353A46;
                                          selection-background-color: #6577FF; padding: 6px; }
            QCheckBox { spacing: 10px; padding: 4px 0; color: #D7DAE2; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #4A5060;
                                   border-radius: 5px; background: #232730; }
            QCheckBox::indicator:checked { background: #6577FF; border-color: #6577FF; }
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: transparent; width: 9px; margin: 3px; }
            QScrollBar::handle:vertical { background: #3B404C; min-height: 36px; border-radius: 4px; }
            QScrollBar:horizontal { background: #151820; height: 10px; margin: 2px; }
            QScrollBar::handle:horizontal { background: #3B404C; min-width: 60px; border-radius: 4px; }
            QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
            QDialog, QMessageBox { background: #191C24; }
            QTextBrowser { background: #151820; border: 1px solid #292D38; border-radius: 10px;
                           padding: 14px; color: #DDE1EA; }
        """)


def ensure_administrator() -> bool:
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    if getattr(sys, "frozen", False):
        executable = sys.executable
        parameters = subprocess.list2cmdline(sys.argv[1:])
    else:
        executable = sys.executable
        parameters = subprocess.list2cmdline([str(APP_DIR / "app.py"), *sys.argv[1:]])
    result = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", executable, parameters, str(APP_DIR), 1
    )
    return result > 32


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("This application requires Windows.")
    if not ensure_administrator():
        raise SystemExit("Administrator permission is required.")
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise SystemExit(0)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GenshinMidiBridge.Desktop")
    application = QApplication(sys.argv)
    application.setApplicationName("Genshin MIDI Bridge")
    application.setFont(QFont("Segoe UI Variable", 10))
    try:
        config = Config.load()
        if not config.language_selected:
            chooser = LanguageDialog(config.language)
            if chooser.exec() != QDialog.DialogCode.Accepted:
                raise SystemExit(0)
            config.language = chooser.language
            config.language_selected = True
            config.save()
        window = MainWindow(config)
        window.show()
        raise SystemExit(application.exec())
    except SystemExit:
        raise
    except Exception:
        logging.critical("Fatal error\n%s", traceback.format_exc())
        QMessageBox.critical(None, "Genshin MIDI Bridge", f"程序发生错误。详情见：\n{LOG_FILE}")
        raise


if __name__ == "__main__":
    main()
