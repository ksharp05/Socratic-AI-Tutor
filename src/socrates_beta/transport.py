"""Canonical HTTPS origin for the hosted beta; local defaults remain local-only."""
from dataclasses import dataclass
from urllib.parse import urlsplit
import re


@dataclass(frozen=True)
class BrowserTransport:
    origin: str | None
    hosts: tuple[str, ...]
    origins: tuple[str, ...] = ()

    @classmethod
    def configured(cls, origin=None, *, testing=False, additional_origins=()):
        local = ("localhost", "127.0.0.1") + (("testserver",) if testing else ())
        if origin is None:
            if additional_origins:raise ValueError("Additional origins require a public origin")
            return cls(None, local)
        if not isinstance(origin, str) or len(origin) > 300:
            raise ValueError("A canonical HTTPS public_origin is required")
        parsed = urlsplit(origin)
        if (parsed.scheme != "https" or parsed.username or parsed.password or not parsed.hostname
                or parsed.query or parsed.fragment or parsed.path not in ("", "/")
                or parsed.netloc != parsed.netloc.lower()
                or not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?(?::[0-9]+)?", parsed.netloc)):
            raise ValueError("public_origin must be a single canonical HTTPS origin")
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("Invalid public origin port") from exc
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("Invalid public origin port")
        if any(not part or len(part)>63 or part.startswith("-") or part.endswith("-") for part in parsed.hostname.split(".")):
            raise ValueError("Invalid public origin hostname")
        canonical = f"https://{parsed.hostname}" + (f":{port}" if port and port != 443 else "")
        others=tuple(cls.configured(value) for value in additional_origins)
        return cls(canonical, tuple(dict.fromkeys(local + (parsed.hostname,) + tuple(h for other in others for h in other.hosts))),
                   tuple(dict.fromkeys((canonical,) + tuple(other.origin for other in others))))

    @property
    def secure_cookie(self):
        return self.origin is not None
