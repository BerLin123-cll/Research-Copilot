"""minimal fastapi stub for offline smoke test"""
from typing import Any, Callable


class FastAPI:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.routes: list[tuple[str, str, Callable]] = []

    def add_middleware(self, *args: Any, **kwargs: Any) -> None:
        pass

    def include_router(self, router: Any) -> None:
        pass

    def get(self, path: str, **kwargs: Any) -> Callable:
        def deco(fn: Callable) -> Callable:
            self.routes.append(("GET", path, fn))
            return fn
        return deco


class APIRouter:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.routes: list[tuple[str, str, Callable]] = []

    def _route(self, method: str, path: str) -> Callable:
        def deco(fn: Callable) -> Callable:
            self.routes.append((method, path, fn))
            return fn
        return deco

    def get(self, path: str, **kwargs: Any) -> Callable:
        return self._route("GET", path)

    def post(self, path: str, **kwargs: Any) -> Callable:
        return self._route("POST", path)

    def delete(self, path: str, **kwargs: Any) -> Callable:
        return self._route("DELETE", path)

    def websocket(self, path: str, **kwargs: Any) -> Callable:
        return self._route("WS", path)


def Depends(dependency: Any = None) -> Any:
    return dependency


def Query(default: Any = None, **kwargs: Any) -> Any:
    return default


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any = None) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class WebSocket:
    pass


class WebSocketDisconnect(Exception):
    pass


class UploadFile:
    pass


def File(default: Any = None, **kwargs: Any) -> Any:
    return default
