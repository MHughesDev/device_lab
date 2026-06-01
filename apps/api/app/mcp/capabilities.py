from pydantic import BaseModel


class LifecycleCapabilities(BaseModel):
    provision: bool = False
    stop: bool = False
    start: bool = False
    terminate: bool = False
    snapshot: bool = False


class ObserveCapabilities(BaseModel):
    ax_tree: bool = False
    ocr: bool = False
    screenshot: bool = False
    vlm: bool = False


class InteractCapabilities(BaseModel):
    click: bool = False
    double_click: bool = False
    right_click: bool = False
    mouse_move: bool = False
    drag: bool = False
    scroll: bool = False
    cursor_position: bool = False
    type: bool = False
    key: bool = False


class ReadCapabilities(BaseModel):
    text: bool = False
    headings: bool = False
    tables: bool = False
    links: bool = False
    regions: bool = False


class FileCapabilities(BaseModel):
    upload: bool = False
    download: bool = False
    path_read: bool = False


class NetworkCapabilities(BaseModel):
    proxy: bool = False
    capture: bool = False
    inject: bool = False


class ScreenRecordingCapabilities(BaseModel):
    supported: bool = False
    # Maximum recording duration the adapter enforces (0 = unlimited by adapter)
    max_duration_seconds: int = 0
    # Container format the adapter produces
    output_format: str = "mp4"


class SystemCapabilities(BaseModel):
    """Shell, clipboard, app launch, filesystem, window/process management."""
    run_shell: bool = False
    key_hold: bool = False       # key_down / key_up
    clipboard: bool = False      # get_clipboard / set_clipboard
    launch_app: bool = False
    wait_for: bool = False
    filesystem: bool = False     # read_file / write_file / list_directory
    processes: bool = False      # list_processes / kill_process
    windows: bool = False        # list_windows / focus_window / resize_window
    screen_size: bool = False    # get_screen_size


class MobileCapabilities(BaseModel):
    """Touch gestures and hardware buttons — applicable to android and ios_sim."""
    long_press: bool = False
    pinch: bool = False
    press_button: bool = False


class BrowserCapabilities(BaseModel):
    """Playwright-backed browser-specific tools."""
    navigate: bool = False
    tabs: bool = False           # new_tab / close_tab / list_tabs / switch_tab
    console_logs: bool = False
    network_requests: bool = False
    dialogs: bool = False        # handle_dialog


class DeviceCapabilities(BaseModel):
    lifecycle: LifecycleCapabilities = LifecycleCapabilities()
    observe: ObserveCapabilities = ObserveCapabilities()
    interact: InteractCapabilities = InteractCapabilities()
    read_content: ReadCapabilities = ReadCapabilities()
    files: FileCapabilities = FileCapabilities()
    network: NetworkCapabilities = NetworkCapabilities()
    screen_recording: ScreenRecordingCapabilities = ScreenRecordingCapabilities()
    system: SystemCapabilities = SystemCapabilities()
    mobile: MobileCapabilities = MobileCapabilities()
    browser: BrowserCapabilities = BrowserCapabilities()
    recipes: bool = False
    streaming: bool = False
    dangerous_mode: bool = False


_FULL_INTERACT = InteractCapabilities(
    click=True, double_click=True, right_click=True, mouse_move=True,
    drag=True, scroll=True, cursor_position=True, type=True, key=True,
)

_TOUCH_INTERACT = InteractCapabilities(
    # Touchscreen: no right_click, mouse_move, or cursor_position
    click=True, double_click=True, drag=True, scroll=True, type=True, key=True,
)

_FULL_SYSTEM = SystemCapabilities(
    run_shell=True, key_hold=True, clipboard=True, launch_app=True, wait_for=True,
    filesystem=True, processes=True, windows=True, screen_size=True,
)

LINUX_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, stop=True, start=True, terminate=True),
    observe=ObserveCapabilities(screenshot=True, ax_tree=True),
    interact=_FULL_INTERACT,
    files=FileCapabilities(upload=True, download=True, path_read=True),
    network=NetworkCapabilities(proxy=True, capture=True),
    screen_recording=ScreenRecordingCapabilities(supported=True, output_format="mp4"),
    system=_FULL_SYSTEM,
    streaming=True,
)

MACOS_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, terminate=True),
    observe=ObserveCapabilities(screenshot=True, ax_tree=True),
    interact=_FULL_INTERACT,
    files=FileCapabilities(upload=True, download=True, path_read=True),
    network=NetworkCapabilities(proxy=True, capture=True),
    screen_recording=ScreenRecordingCapabilities(supported=True, output_format="mp4"),
    system=_FULL_SYSTEM,
    streaming=True,
)

WINDOWS_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, stop=True, start=True, terminate=True, snapshot=True),
    observe=ObserveCapabilities(screenshot=True, ax_tree=True),
    interact=_FULL_INTERACT,
    files=FileCapabilities(upload=True, download=True, path_read=True),
    network=NetworkCapabilities(proxy=True, capture=True),
    screen_recording=ScreenRecordingCapabilities(supported=True, output_format="mp4"),
    system=_FULL_SYSTEM,
    streaming=True,
)

ANDROID_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, terminate=True),
    observe=ObserveCapabilities(screenshot=True, ax_tree=True),
    interact=_TOUCH_INTERACT,
    network=NetworkCapabilities(proxy=True, capture=True),
    screen_recording=ScreenRecordingCapabilities(supported=True, max_duration_seconds=180, output_format="mp4"),
    system=SystemCapabilities(
        run_shell=True, key_hold=True, filesystem=True,
        processes=True, screen_size=True,
    ),
    mobile=MobileCapabilities(long_press=True, pinch=True, press_button=True),
    streaming=True,
)

IOS_SIM_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, terminate=True, snapshot=True),
    observe=ObserveCapabilities(screenshot=True),
    interact=_TOUCH_INTERACT,
    screen_recording=ScreenRecordingCapabilities(supported=True, output_format="mp4"),
    system=SystemCapabilities(
        run_shell=True, key_hold=True, launch_app=True, filesystem=True,
        processes=True, screen_size=True,
    ),
    mobile=MobileCapabilities(long_press=True, press_button=True),
    streaming=True,
)

BROWSER_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, terminate=True),
    observe=ObserveCapabilities(screenshot=True, ax_tree=True),
    interact=_FULL_INTERACT,
    screen_recording=ScreenRecordingCapabilities(supported=True, output_format="webm"),
    system=SystemCapabilities(
        key_hold=True, clipboard=True, launch_app=True,
        wait_for=True, screen_size=True,
    ),
    browser=BrowserCapabilities(
        navigate=True, tabs=True, console_logs=True,
        network_requests=True, dialogs=True,
    ),
)

FAMILY_CAPABILITIES: dict[str, DeviceCapabilities] = {
    "linux": LINUX_CAPABILITIES,
    "macos": MACOS_CAPABILITIES,
    "windows": WINDOWS_CAPABILITIES,
    "android": ANDROID_CAPABILITIES,
    "ios_sim": IOS_SIM_CAPABILITIES,
    "browser": BROWSER_CAPABILITIES,
}


def get_capabilities(family: str) -> DeviceCapabilities:
    return FAMILY_CAPABILITIES.get(family, DeviceCapabilities())
