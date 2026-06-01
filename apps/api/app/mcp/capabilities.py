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


class DeviceCapabilities(BaseModel):
    lifecycle: LifecycleCapabilities = LifecycleCapabilities()
    observe: ObserveCapabilities = ObserveCapabilities()
    interact: InteractCapabilities = InteractCapabilities()
    read_content: ReadCapabilities = ReadCapabilities()
    files: FileCapabilities = FileCapabilities()
    network: NetworkCapabilities = NetworkCapabilities()
    screen_recording: ScreenRecordingCapabilities = ScreenRecordingCapabilities()
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

LINUX_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, stop=True, start=True, terminate=True),
    observe=ObserveCapabilities(screenshot=True, ax_tree=True),
    interact=_FULL_INTERACT,
    files=FileCapabilities(upload=True, download=True, path_read=True),
    network=NetworkCapabilities(proxy=True, capture=True),
    screen_recording=ScreenRecordingCapabilities(supported=True, output_format="mp4"),
    streaming=True,
)

MACOS_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, terminate=True),
    observe=ObserveCapabilities(screenshot=True, ax_tree=True),
    interact=_FULL_INTERACT,
    files=FileCapabilities(upload=True, download=True, path_read=True),
    network=NetworkCapabilities(proxy=True, capture=True),
    screen_recording=ScreenRecordingCapabilities(supported=True, output_format="mp4"),
    streaming=True,
)

WINDOWS_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, stop=True, start=True, terminate=True, snapshot=True),
    observe=ObserveCapabilities(screenshot=True, ax_tree=True),
    interact=_FULL_INTERACT,
    files=FileCapabilities(upload=True, download=True, path_read=True),
    network=NetworkCapabilities(proxy=True, capture=True),
    screen_recording=ScreenRecordingCapabilities(supported=True, output_format="mp4"),
    streaming=True,
)

ANDROID_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, terminate=True),
    observe=ObserveCapabilities(screenshot=True, ax_tree=True),
    interact=_TOUCH_INTERACT,
    network=NetworkCapabilities(proxy=True, capture=True),
    screen_recording=ScreenRecordingCapabilities(supported=True, max_duration_seconds=180, output_format="mp4"),
    streaming=True,
)

IOS_SIM_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, terminate=True, snapshot=True),
    observe=ObserveCapabilities(screenshot=True),
    interact=_TOUCH_INTERACT,
    screen_recording=ScreenRecordingCapabilities(supported=True, output_format="mp4"),
    streaming=True,
)

BROWSER_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, terminate=True),
    observe=ObserveCapabilities(screenshot=True, ax_tree=True),
    interact=_FULL_INTERACT,
    screen_recording=ScreenRecordingCapabilities(supported=True, output_format="webm"),
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
