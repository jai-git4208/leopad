import board
import busio
import displayio
import terminalio
from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC
from kmk.modules.layers import Layers
from kmk.extensions.RGB import RGB
from kmk.extensions.media_keys import MediaKeys
import adafruit_displayio_ssd1306
from adafruit_display_text import label

keyboard = KMKKeyboard()

layers = Layers()
media_keys = MediaKeys()

keyboard.modules.append(layers)
keyboard.extensions.append(media_keys)

# neeed to update according to actual microcontroller pins
PINS = [
    board.D0,   # Key 1 - Run/Build
    board.D1,   # Key 2 - Comment/Uncomment
    board.D2,   # Key 3 - Duplicate Line
    board.D3,   # Key 4 - Format Document
    board.D4,   # Key 5 - Open Terminal
    board.D5,   # Key 6 - Project Search
    board.D6,   # Key 7 - Git Quick Commit
    board.D7,   # Key 8 - Mode Switch
]

keyboard.matrix = KeysScanner(
    pins=PINS,
    value_when_pressed=False,
)

# RGB LED configuration for SK6812MINI
rgb = RGB(
    pixel_pin=board.D10,  #need to check which pin is used for rgb data
    num_pixels=2,
    val_limit=100,
    val_default=50,
)
keyboard.extensions.append(rgb)


displayio.release_displays()
i2c = busio.I2C(scl=board.SCL, sda=board.SDA)


DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64  
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)

# Create display group
splash = displayio.Group()
display.show(splash)

# Layer names for OLED display
LAYER_NAMES = [
    "PROG",     # Layer 0: Programming Mode
    "GIT",      # Layer 1: Git Mode
    "SYSTEM",   # Layer 2: System Controls
    "CUSTOM",   # Layer 3: Custom Mode
]

# Create text labels for OLED
title_label = label.Label(
    terminalio.FONT,
    text="LEOPAD",
    color=0xFFFFFF,
    x=35,
    y=10
)

mode_label = label.Label(
    terminalio.FONT,
    text="Mode: PROG",
    color=0xFFFFFF,
    x=10,
    y=30
)

info_label = label.Label(
    terminalio.FONT,
    text="Ready",
    color=0xFFFFFF,
    x=10,
    y=50
)

splash.append(title_label)
splash.append(mode_label)
splash.append(info_label)

# custom key definitions
RUN_BUILD = KC.F5                                    # Key 1
COMMENT = KC.LCTL(KC.SLASH)                          # Key 2: Ctrl+/
DUPLICATE = KC.LCTL(KC.D)                            # Key 3: Ctrl+D
FORMAT = KC.LSFT(KC.LALT(KC.F))                     # Key 4: Shift+Alt+F
TERMINAL = KC.LCTL(KC.GRAVE)                         # Key 5: Ctrl+`
SEARCH = KC.LCTL(KC.LSFT(KC.F))                     # Key 6: Ctrl+Shift+F
GIT_COMMIT = KC.LCTL(KC.LSFT(KC.G))                 # Key 7: Git panel

# LAYER 0: programming Mode (Default)
LAYER_PROGRAMMING = [
    RUN_BUILD,      # Key 1: F5 - Run/Build
    COMMENT,        # Key 2: Ctrl+/ - Comment
    DUPLICATE,      # Key 3: Ctrl+D - Duplicate
    FORMAT,         # Key 4: Shift+Alt+F - Format
    TERMINAL,       # Key 5: Ctrl+` - Terminal
    SEARCH,         # Key 6: Ctrl+Shift+F - Search
    GIT_COMMIT,     # Key 7: Git panel
    KC.TO(1),       # Key 8: Switch to Git Mode
]

# LAYER 1: git Mode
LAYER_GIT = [
    KC.LCTL(KC.LSFT(KC.G)),              # Key 1: Open Git panel
    KC.LCTL(KC.ENTER),                    # Key 2: Commit
    KC.LCTL(KC.K),                        # Key 3: Git command prefix
    KC.LCTL(KC.LSFT(KC.P)),              # Key 4: Command palette
    KC.ESC,                               # Key 5: Escape/Cancel
    KC.LCTL(KC.Z),                        # Key 6: Undo
    KC.RGB_TOG,                           # Key 7: Toggle RGB
    KC.TO(2),                             # Key 8: Switch to System Mode
]

# LAYER 2: system Controls Mode
LAYER_SYSTEM = [
    KC.LCTL(KC.LSFT(KC.N)),              # Key 1: New window
    KC.LCTL(KC.W),                        # Key 2: Close tab
    KC.LCTL(KC.TAB),                      # Key 3: Next tab
    KC.LCTL(KC.LSFT(KC.TAB)),            # Key 4: Previous tab
    KC.VOLU,                              # Key 5: Volume Up
    KC.VOLD,                              # Key 6: Volume Down
    KC.MUTE,                              # Key 7: Mute
    KC.TO(3),                             # Key 8: Switch to Custom Mode
]

# LAYER 3: custom Mode
LAYER_CUSTOM = [
    KC.F13,         # Key 1: F13 (map in software)
    KC.F14,         # Key 2: F14
    KC.F15,         # Key 3: F15
    KC.F16,         # Key 4: F16
    KC.F17,         # Key 5: F17
    KC.F18,         # Key 6: F18
    KC.RGB_HUI,     # Key 7: RGB Hue+
    KC.TO(0),       # Key 8: Back to Programming Mode
]

# assign all layers to keyboard
keyboard.keymap = [
    LAYER_PROGRAMMING,  # Layer 0
    LAYER_GIT,          # Layer 1
    LAYER_SYSTEM,       # Layer 2
    LAYER_CUSTOM,       # Layer 3
]

# track current layer for OLED updates
current_layer = 0

# custom layer change handler to update OLED
def update_oled_layer(new_layer):
    global current_layer
    current_layer = new_layer
    mode_label.text = f"Mode: {LAYER_NAMES[new_layer]}"
    
    
    if new_layer == 0:
        info_label.text = "F5|Cmt|Dup|Fmt"
    elif new_layer == 1:
        info_label.text = "Git Controls"
    elif new_layer == 2:
        info_label.text = "System Ctrl"
    elif new_layer == 3:
        info_label.text = "Custom Keys"


original_process_key = keyboard.process_key

def custom_process_key(key, is_pressed, coord_int=None):
    global current_layer
    result = original_process_key(key, is_pressed, coord_int)
    
    
    if keyboard.active_layers != [current_layer]:
        if len(keyboard.active_layers) > 0:
            update_oled_layer(keyboard.active_layers[0])
    
    return result

keyboard.process_key = custom_process_key


update_oled_layer(0)

if __name__ == '__main__':
    keyboard.go()