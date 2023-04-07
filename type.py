from typing import TypedDict, Union, Callable, Awaitable
from typing_extensions import NotRequired

UpHostQuery = TypedDict("UpHostQuery", {
    "host": NotRequired[Union[str, TypedDict("Host", {
        "protocol": str,
        "host": str,
        "port": int
    })]],
    "command": NotRequired[Union[str, Callable[[], Union[int, Awaitable[int]]]]],
    "wait": NotRequired[Union[bool, TypedDict("Wait", {
        "interval": int,
        "timeout": int,
        "retries": int
    })]],
    "on_success": NotRequired[Union[str, Callable]],
    "on_fail": NotRequired[Union[str, Callable]]
})
