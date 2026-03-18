from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

import httpx

from app.core.config import Settings


class SafeUrlFetcher:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def fetch(self, url: str) -> tuple[str, httpx.Response]:
        current_url = self.validate(url)
        with httpx.Client(timeout=self._settings.request_timeout_seconds, follow_redirects=False) as client:
            for _ in range(self._settings.url_ingest_max_redirects + 1):
                response = client.get(current_url)
                if response.is_redirect:
                    current_url = self._resolve_redirect_target(current_url, response)
                    continue
                response.raise_for_status()
                return current_url, response
        raise ValueError("URL ingest blocked: too many redirects.")

    def validate(self, url: str) -> str:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("URL ingest blocked: only http and https URLs are allowed.")
        if not parsed.hostname:
            raise ValueError("URL ingest blocked: missing hostname.")
        hostname = parsed.hostname.rstrip(".").lower()
        self._validate_allowed_domain(hostname)
        self._validate_public_target(hostname)
        return url

    def _resolve_redirect_target(self, current_url: str, response: httpx.Response) -> str:
        location = response.headers.get("location")
        if not location:
            raise ValueError("URL ingest blocked: redirect response missing location header.")
        return self.validate(str(httpx.URL(current_url).join(location)))

    def _validate_allowed_domain(self, hostname: str) -> None:
        allowed_domains = [domain.rstrip(".").lower() for domain in self._settings.url_ingest_allowed_domains]
        if not allowed_domains:
            return
        if any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_domains):
            return
        raise ValueError("URL ingest blocked: hostname is not in the configured allowlist.")

    def _validate_public_target(self, hostname: str) -> None:
        for address in self._resolve_ip_addresses(hostname):
            if not address.is_global:
                raise ValueError("URL ingest blocked: private, loopback, or reserved network targets are not allowed.")

    def _resolve_ip_addresses(self, hostname: str) -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        literal_address = self._parse_ip_literal(hostname)
        if literal_address is not None:
            return {literal_address}
        try:
            results = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError("URL ingest blocked: hostname could not be resolved.") from exc
        addresses: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
        for result in results:
            address_text = result[4][0]
            parsed_address = self._parse_ip_literal(address_text)
            if parsed_address is not None:
                addresses.add(parsed_address)
        if not addresses:
            raise ValueError("URL ingest blocked: hostname resolved to no usable IP addresses.")
        return addresses

    @staticmethod
    def _parse_ip_literal(hostname: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
        try:
            return ipaddress.ip_address(hostname)
        except ValueError:
            return None
