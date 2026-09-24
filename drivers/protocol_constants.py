"""Single source of truth for the DZ-14 UART protocol and timings."""

# UART / timing
UART_BAUDRATE = 115200
UART_TIMEOUT_SECONDS = 2.0
COMMAND_TIMEOUT_SECONDS = 10.0
BOOT_TIMEOUT_SECONDS = 15.0
BOOT_READY_MARKERS = (
    "device ready",
    "type 'help' for commands",
)

# station_WiFi commands and exact response markers
WIFI_SCAN_COMMAND = "scan"
WIFI_CONNECT_COMMAND = "connect"
WIFI_STATUS_COMMAND = "status"
WIFI_DISCONNECT_COMMAND = "disconnect"
REBOOT_COMMAND = "reboot"

# Static prefix of the real prompt; the saved SSID in brackets is dynamic.
WIFI_SSID_PROMPT = "enter ssid, number from list, or enter to use saved"
WIFI_PASSWORD_PROMPT = "enter password:"
WIFI_CONNECT_SUCCESS_MARKER = "successfully connected to ssid:"
WIFI_DISCONNECTED_STATE_MARKER = "wifi station: disconnected"

# Generic negative markers used when classifying a connect attempt.
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
