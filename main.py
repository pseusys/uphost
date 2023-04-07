import asyncio
from re import match
from socket import socket, AF_INET, SOCK_STREAM
from asyncio import create_subprocess_exec, iscoroutine, sleep
from typing import List, Union, Callable, Awaitable, TypeVar

from type import UpHostQuery

_DEFAULT_TIMEOUT = 5
_T = TypeVar('_T')


def _ping_server(host: str) -> Callable[[], int]:
    groups = match(r"^(.*):(\d+)$", host)
    if groups is None:
        raise RuntimeError(f"Host string `{host}` should be formatted like this: `HOST:PORT`!")

    def pinger() -> int:
        try:
            sock = socket(AF_INET, SOCK_STREAM)
            sock.settimeout(_DEFAULT_TIMEOUT)
            sock.connect((groups.group(1), int(groups.group(2))))
        except OSError as _:
            return 1
        else:
            sock.close()
            return 0
    return pinger


async def _execute_subprocess(subprocess: Union[str, Callable[[], Union[_T, Awaitable[_T]]]]) -> _T:
    if isinstance(subprocess, str):
        return (await create_subprocess_exec(subprocess)).returncode
    elif iscoroutine(subprocess):
        return await subprocess()
    else:
        return subprocess()


async def process_up_host_query_queue(queue: List[UpHostQuery]):
    for query in queue:
        if query.get("command", None) is None:
            if query.get("host", None) is None:
                raise RuntimeError(f"Neither `host` nor `command` are defined!")
            elif isinstance(query["host"], str):
                host = query["host"]
            elif isinstance(query["host"], dict):
                host = f"{query['host']['protocol']}://{query['host']['host']}:{query['host']['port']}"
            else:
                raise RuntimeError(f"Unexpected value of `host` property!")
            command = _ping_server(host)
        elif isinstance(query["command"], Callable):
            command = query["command"]
        else:
            raise RuntimeError(f"Subprocess `command` of type `{type(query['command'])}` is not executable!")

        if query.get("wait", False) is False:
            result = await _execute_subprocess(command)
        elif isinstance(query["wait"], bool) and query["wait"]:
            result = 1
            while result != 0:
                result = await _execute_subprocess(command)
        elif isinstance(query["wait"], dict):
            await sleep(int(query["wait"]["timeout"]))
            result = await _execute_subprocess(command)
            for _ in range(int(query["wait"]["retries"])):
                if result == 0:
                    break
                await sleep(int(query["wait"]["interval"]))
                result = await _execute_subprocess(command)
        else:
            raise RuntimeError(f"Unexpected value of `wait` property!")

        if query.get("on_success", None) is not None and result == 0:
            await _execute_subprocess(query["on_success"])

        if query.get("on_fail", None) is not None and result != 0:
            await _execute_subprocess(query["on_fail"])


if __name__ == '__main__':
    asyncio.run(process_up_host_query_queue([{
        "host": "google.com:443",
    }]))
