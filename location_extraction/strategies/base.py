from typing import List, Optional, Protocol, runtime_checkable

try:
    import pydantic as _pydantic  # type: ignore
    BaseModel = _pydantic.BaseModel  # type: ignore[attr-defined]
    PrivateAttr = _pydantic.PrivateAttr  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    class BaseModel:  # type: ignore[no-redef]
        pass
    def PrivateAttr(*, default=None, default_factory=None):  # type: ignore[no-redef]
        if default_factory is not None:
            try:
                return default_factory()
            except Exception:
                return None
        return default


@runtime_checkable
class LocationExtractionStrategy(Protocol):
    def extract(self, text: str) -> List[str]:
        ...


@runtime_checkable
class GeocodingStrategy(Protocol):
    def geocode(self, location_name: str, context: Optional[str] = None) -> Optional[dict]:
        ...
