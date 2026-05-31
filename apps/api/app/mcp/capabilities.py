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
    type_text: bool = False
    fill_form: bool = False
    select: bool = False
    scroll: bool = False
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


class DeviceCapabilities(BaseModel):
    lifecycle: LifecycleCapabilities = LifecycleCapabilities()
    observe: ObserveCapabilities = ObserveCapabilities()
    interact: InteractCapabilities = InteractCapabilities()
    read_content: ReadCapabilities = ReadCapabilities()
    files: FileCapabilities = FileCapabilities()
    network: NetworkCapabilities = NetworkCapabilities()
    recipes: bool = False
    streaming: bool = False
    dangerous_mode: bool = False


LINUX_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, stop=True, start=True, terminate=True),
    observe=ObserveCapabilities(ax_tree=True, ocr=True, screenshot=True),
    interact=InteractCapabilities(click=True, type_text=True, fill_form=True, select=True, scroll=True, key=True),
    read_content=ReadCapabilities(text=True, headings=True, tables=True, links=True, regions=True),
    files=FileCapabilities(upload=True, download=True, path_read=True),
    network=NetworkCapabilities(proxy=True, capture=True),
)

BROWSER_CAPABILITIES = DeviceCapabilities(
    lifecycle=LifecycleCapabilities(provision=True, terminate=True),
    observe=ObserveCapabilities(ax_tree=True, screenshot=True),
    interact=InteractCapabilities(click=True, type_text=True, fill_form=True, select=True, scroll=True),
    read_content=ReadCapabilities(text=True, headings=True, tables=True, links=True),
)

FAMILY_CAPABILITIES: dict[str, DeviceCapabilities] = {
    "linux": LINUX_CAPABILITIES,
    "browser": BROWSER_CAPABILITIES,
}


def get_capabilities(family: str) -> DeviceCapabilities:
    return FAMILY_CAPABILITIES.get(family, DeviceCapabilities())
