"""Single source of truth for the DZ-14 UART and BLE protocol."""

# UART / timing
UART_BAUDRATE = 115200
UART_TIMEOUT_SECONDS = 2.0
COMMAND_TIMEOUT_SECONDS = 10.0
BOOT_TIMEOUT_SECONDS = 15.0
BOOT_READY_MARKERS = (
    "device ready",
    "type 'help' for commands",
)

# station_WiFi commands and response markers
WIFI_SCAN_COMMAND = "scan"
WIFI_CONNECT_COMMAND = "connect"
WIFI_STATUS_COMMAND = "status"
WIFI_DISCONNECT_COMMAND = "disconnect"
REBOOT_COMMAND = "reboot"
WIFI_SSID_PROMPT = "enter ssid, number from list, or enter to use saved"
WIFI_PASSWORD_PROMPT = "enter password:"
WIFI_CONNECT_SUCCESS_MARKER = "successfully connected to ssid:"
WIFI_DISCONNECTED_STATE_MARKER = "wifi station: disconnected"

FAILURE_MARKERS = (
    "connection failed",
    "connection timeout",
    "connect to the ap fail",
    "wrong password",
    "auth failed",
    "password: fail",
    "not found",
    "unable to connect",
    "error:",
)

# SENTRY-BLE identity and GATT contract
BLE_DEVICE_NAME = "SENTRY-BLE"
BLE_LED_CHARACTERISTIC_UUID = "00001525-1212-efde-1523-785feabcd123"
BLE_RELAY_CHARACTERISTIC_UUID = "00001526-1212-efde-1523-785feabcd123"
BLE_SCAN_TIMEOUT_SECONDS = 10.0
BLE_CONNECT_TIMEOUT_SECONDS = 15.0
BLE_UART_PATTERN_TIMEOUT_SECONDS = 5.0
BLE_LED_ON_MARKER = "LED ON!"
BLE_LED_OFF_MARKER = "LED OFF!"
