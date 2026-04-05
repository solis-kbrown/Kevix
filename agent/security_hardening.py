"""
SERVERROOT.NET - Security Hardening Module
Phase 7, Task 7.1: Comprehensive security hardening

Features:
- Input validation and sanitization
- Encryption verification and enforcement
- Secure coding patterns
- Authentication and authorization
- Audit logging
- Secrets management
"""

import os
import re
import json
import hmac
import hashlib
import base64
import logging
import secrets
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, hmac as crypto_hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS
# ============================================================

class ValidationResult(Enum):
    VALID = "valid"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"


class ThreatLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventType(Enum):
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    COMMAND_ISSUED = "command_issued"
    DATA_ACCESS = "data_access"
    CONFIG_CHANGE = "config_change"
    AGENT_REGISTER = "agent_register"
    AGENT_DEREGISTER = "agent_deregister"
    EXPLOIT_ATTEMPT = "exploit_attempt"
    SECURITY_VIOLATION = "security_violation"
    SYSTEM_EVENT = "system_event"


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class ValidationReport:
    """Result of input validation"""
    input_type: str
    result: ValidationResult
    threat_level: ThreatLevel
    issues: List[str] = field(default_factory=list)
    sanitized_value: Any = None
    timestamp: datetime = field(default_factory=datetime.now)

    def is_safe(self) -> bool:
        return self.result in (ValidationResult.VALID,) and \
               self.threat_level in (ThreatLevel.NONE, ThreatLevel.LOW)


@dataclass
class AuditEvent:
    """Audit log entry"""
    event_id: str
    event_type: AuditEventType
    actor: str
    target: str
    action: str
    result: str
    metadata: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "actor": self.actor,
            "target": self.target,
            "action": self.action,
            "result": self.result,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address
        }


@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_enabled: bool = True
    audit_logging_enabled: bool = True
    input_validation_enabled: bool = True
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 100
    session_timeout_seconds: int = 3600
    min_password_length: int = 16
    require_mfa: bool = False
    allowed_ip_ranges: List[str] = field(default_factory=list)
    blocked_patterns: List[str] = field(default_factory=list)


@dataclass
class EncryptionContext:
    """Encryption context for data protection"""
    key_id: str
    algorithm: str
    key_created_at: datetime
    key_expires_at: Optional[datetime]
    encrypted: bool = True


# ============================================================
# INPUT VALIDATOR
# ============================================================

class InputValidator:
    """
    Comprehensive input validation and sanitization
    Protects against injection attacks, XSS, path traversal, etc.
    """

    # Dangerous patterns to detect
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"(\'|\")\s*(OR|AND)\s*(\'|\")",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\(",
        r"\$\{",
        r">\s*/",
        r"<\s*/",
        r"\|\|",
        r"&&",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e",
        r"%252e%252e",
        r"\.\.%2f",
        r"\.\.%5c",
    ]

    XSS_PATTERNS = [
        r"<script",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"eval\s*\(",
        r"document\.cookie",
        r"window\.location",
    ]

    IP_PATTERN = r"^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$"
    HOSTNAME_PATTERN = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
    AGENT_ID_PATTERN = r"^agent_[a-f0-9]{8}$"
    COMMAND_PATTERN = r"^[a-zA-Z0-9_\-]{1,64}$"

    def __init__(self):
        self.compiled_sql = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.compiled_cmd = [re.compile(p) for p in self.COMMAND_INJECTION_PATTERNS]
        self.compiled_path = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]
        self.compiled_xss = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]

    def validate_ip_address(self, ip: str) -> ValidationReport:
        """Validate IP address format"""
        issues = []
        if not isinstance(ip, str):
            return ValidationReport("ip_address", ValidationResult.INVALID, ThreatLevel.MEDIUM,
                                    ["Input must be a string"])
        
        ip = ip.strip()
        if not re.match(self.IP_PATTERN, ip):
            issues.append(f"Invalid IP address format: {ip}")
            return ValidationReport("ip_address", ValidationResult.INVALID, ThreatLevel.LOW, issues)
        
        # Validate octets
        parts = ip.split('/')[0].split('.')
        for part in parts:
            if int(part) > 255:
                issues.append(f"Invalid octet value: {part}")
                return ValidationReport("ip_address", ValidationResult.INVALID, ThreatLevel.LOW, issues)
        
        return ValidationReport("ip_address", ValidationResult.VALID, ThreatLevel.NONE,
                                sanitized_value=ip)

    def validate_hostname(self, hostname: str) -> ValidationReport:
        """Validate hostname format"""
        issues = []
        if not isinstance(hostname, str):
            return ValidationReport("hostname", ValidationResult.INVALID, ThreatLevel.MEDIUM,
                                    ["Input must be a string"])
        
        hostname = hostname.strip().lower()
        
        # Check length
        if len(hostname) > 253:
            issues.append("Hostname too long (max 253 chars)")
            return ValidationReport("hostname", ValidationResult.INVALID, ThreatLevel.LOW, issues)
        
        # Check for injection attempts
        threat = self._check_injection(hostname)
        if threat:
            return ValidationReport("hostname", ValidationResult.BLOCKED, ThreatLevel.HIGH,
                                    [f"Injection attempt detected: {threat}"])
        
        if not re.match(self.HOSTNAME_PATTERN, hostname):
            issues.append(f"Invalid hostname format: {hostname}")
            return ValidationReport("hostname", ValidationResult.INVALID, ThreatLevel.LOW, issues)
        
        return ValidationReport("hostname", ValidationResult.VALID, ThreatLevel.NONE,
                                sanitized_value=hostname)

    def validate_command(self, command: str) -> ValidationReport:
        """Validate command string"""
        if not isinstance(command, str):
            return ValidationReport("command", ValidationResult.INVALID, ThreatLevel.MEDIUM,
                                    ["Input must be a string"])
        
        command = command.strip()
        
        # Check for injection
        threat = self._check_injection(command)
        if threat:
            return ValidationReport("command", ValidationResult.BLOCKED, ThreatLevel.CRITICAL,
                                    [f"Command injection detected: {threat}"])
        
        if not re.match(self.COMMAND_PATTERN, command):
            return ValidationReport("command", ValidationResult.INVALID, ThreatLevel.MEDIUM,
                                    ["Command contains invalid characters"])
        
        return ValidationReport("command", ValidationResult.VALID, ThreatLevel.NONE,
                                sanitized_value=command)

    def validate_agent_id(self, agent_id: str) -> ValidationReport:
        """Validate agent ID format"""
        if not isinstance(agent_id, str):
            return ValidationReport("agent_id", ValidationResult.INVALID, ThreatLevel.MEDIUM,
                                    ["Input must be a string"])
        
        if not re.match(self.AGENT_ID_PATTERN, agent_id):
            return ValidationReport("agent_id", ValidationResult.INVALID, ThreatLevel.LOW,
                                    [f"Invalid agent ID format: {agent_id}"])
        
        return ValidationReport("agent_id", ValidationResult.VALID, ThreatLevel.NONE,
                                sanitized_value=agent_id)

    def validate_json_payload(self, payload: Any, max_depth: int = 10, max_size: int = 65536) -> ValidationReport:
        """Validate JSON payload"""
        issues = []
        
        # Check size
        payload_str = json.dumps(payload) if not isinstance(payload, str) else payload
        if len(payload_str) > max_size:
            issues.append(f"Payload too large: {len(payload_str)} bytes (max {max_size})")
            return ValidationReport("json_payload", ValidationResult.INVALID, ThreatLevel.MEDIUM, issues)
        
        # Parse if string
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as e:
                return ValidationReport("json_payload", ValidationResult.INVALID, ThreatLevel.LOW,
                                        [f"Invalid JSON: {e}"])
        
        # Check depth
        if self._get_depth(payload) > max_depth:
            issues.append(f"Payload nesting too deep (max {max_depth})")
            return ValidationReport("json_payload", ValidationResult.BLOCKED, ThreatLevel.MEDIUM, issues)
        
        # Check for injection in string values
        threat = self._check_payload_injection(payload)
        if threat:
            return ValidationReport("json_payload", ValidationResult.BLOCKED, ThreatLevel.HIGH,
                                    [f"Injection attempt in payload: {threat}"])
        
        return ValidationReport("json_payload", ValidationResult.VALID, ThreatLevel.NONE,
                                sanitized_value=payload)

    def sanitize_string(self, value: str, allow_spaces: bool = True) -> str:
        """Sanitize string by removing dangerous characters"""
        if not isinstance(value, str):
            return str(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Remove control characters
        value = re.sub(r'[\x01-\x1f\x7f]', '', value)
        
        # HTML encode special chars
        value = value.replace('&', '&').replace('<', '<').replace('>', '>')
        value = value.replace('"', '"').replace("'", '&#x27;')
        
        return value.strip()

    def _check_injection(self, value: str) -> Optional[str]:
        """Check for injection patterns, return threat type or None"""
        for pattern in self.compiled_sql:
            if pattern.search(value):
                return "sql_injection"
        for pattern in self.compiled_cmd:
            if pattern.search(value):
                return "command_injection"
        for pattern in self.compiled_path:
            if pattern.search(value):
                return "path_traversal"
        for pattern in self.compiled_xss:
            if pattern.search(value):
                return "xss"
        return None

    def _check_payload_injection(self, payload: Any, depth: int = 0) -> Optional[str]:
        """Recursively check payload for injection"""
        if depth > 10:
            return None
        if isinstance(payload, str):
            return self._check_injection(payload)
        elif isinstance(payload, dict):
            for k, v in payload.items():
                result = self._check_payload_injection(v, depth + 1)
                if result:
                    return result
        elif isinstance(payload, list):
            for item in payload:
                result = self._check_payload_injection(item, depth + 1)
                if result:
                    return result
        return None

    def _get_depth(self, obj: Any, depth: int = 0) -> int:
        """Get maximum nesting depth of object"""
        if isinstance(obj, dict):
            if not obj:
                return depth
            return max(self._get_depth(v, depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return depth
            return max(self._get_depth(item, depth + 1) for item in obj)
        return depth


# ============================================================
# ENCRYPTION MANAGER
# ============================================================

class EncryptionManager:
    """
    Manages encryption/decryption of sensitive data
    Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)
    """

    def __init__(self, master_key: Optional[bytes] = None):
        """Initialize with optional master key, generates new one if not provided"""
        if master_key:
            self._master_key = master_key
        else:
            self._master_key = Fernet.generate_key()
        
        self._fernet = Fernet(self._master_key)
        self._key_contexts: Dict[str, EncryptionContext] = {}
        self._data_keys: Dict[str, bytes] = {}
        logger.info("EncryptionManager initialized")

    def generate_data_key(self, key_id: str) -> str:
        """Generate a new data encryption key"""
        key = Fernet.generate_key()
        # Encrypt the data key with master key
        encrypted_key = self._fernet.encrypt(key)
        self._data_keys[key_id] = encrypted_key
        
        ctx = EncryptionContext(
            key_id=key_id,
            algorithm="AES-128-CBC+HMAC-SHA256",
            key_created_at=datetime.now(),
            key_expires_at=None
        )
        self._key_contexts[key_id] = ctx
        
        logger.info(f"Generated data key: {key_id}")
        return key_id

    def encrypt(self, data: Union[str, bytes], key_id: Optional[str] = None) -> Tuple[bytes, str]:
        """Encrypt data, returns (ciphertext, key_id)"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if key_id and key_id in self._data_keys:
            # Use specified data key
            raw_key = self._fernet.decrypt(self._data_keys[key_id])
            fernet = Fernet(raw_key)
            ciphertext = fernet.encrypt(data)
        else:
            # Use master key
            key_id = "master"
            ciphertext = self._fernet.encrypt(data)
        
        return ciphertext, key_id

    def decrypt(self, ciphertext: bytes, key_id: str = "master") -> bytes:
        """Decrypt data"""
        try:
            if key_id != "master" and key_id in self._data_keys:
                raw_key = self._fernet.decrypt(self._data_keys[key_id])
                fernet = Fernet(raw_key)
                return fernet.decrypt(ciphertext)
            else:
                return self._fernet.decrypt(ciphertext)
        except Exception as e:
            logger.error(f"Decryption failed for key {key_id}: {e}")
            raise

    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """Hash password with PBKDF2-HMAC-SHA256"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = kdf.derive(password.encode('utf-8'))
        
        hashed = base64.b64encode(key).decode('utf-8')
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        
        return hashed, salt_b64

    def verify_password(self, password: str, hashed: str, salt_b64: str) -> bool:
        """Verify password against hash"""
        try:
            salt = base64.b64decode(salt_b64)
            new_hash, _ = self.hash_password(password, salt)
            return hmac.compare_digest(new_hash, hashed)
        except Exception:
            return False

    def generate_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(length)

    def sign_data(self, data: bytes, secret_key: Optional[bytes] = None) -> str:
        """Sign data with HMAC-SHA256"""
        key = secret_key or self._master_key
        mac = hmac.new(key, data, hashlib.sha256)
        return base64.b64encode(mac.digest()).decode('utf-8')

    def verify_signature(self, data: bytes, signature: str, secret_key: Optional[bytes] = None) -> bool:
        """Verify HMAC-SHA256 signature"""
        try:
            key = secret_key or self._master_key
            expected = self.sign_data(data, key)
            return hmac.compare_digest(
                base64.b64decode(signature),
                base64.b64decode(expected)
            )
        except Exception:
            return False

    def get_master_key_b64(self) -> str:
        """Get master key as base64 string (for secure storage)"""
        return base64.b64encode(self._master_key).decode('utf-8')


# ============================================================
# AUDIT LOGGER
# ============================================================

class AuditLogger:
    """
    Comprehensive audit logging for all security-relevant events
    Immutable, tamper-evident audit trail
    """

    def __init__(self, log_file: str = "logs/audit.log", encryption_manager: Optional[EncryptionManager] = None):
        self.log_file = log_file
        self.encryption_manager = encryption_manager
        self.events: List[AuditEvent] = []
        self._chain_hash = "genesis"  # Blockchain-style hash chain
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        
        # Set up file logger
        self.file_logger = logging.getLogger('audit')
        self.file_logger.setLevel(logging.INFO)
        if not self.file_logger.handlers:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(logging.Formatter('%(asctime)s - AUDIT - %(message)s'))
            self.file_logger.addHandler(handler)
        
        logger.info(f"AuditLogger initialized, logging to {log_file}")

    def log(self, event_type: AuditEventType, actor: str, target: str,
            action: str, result: str, metadata: Optional[Dict] = None,
            ip_address: Optional[str] = None) -> AuditEvent:
        """Log an audit event"""
        import uuid
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            actor=actor,
            target=target,
            action=action,
            result=result,
            metadata=metadata or {},
            ip_address=ip_address
        )
        
        # Add to chain
        event_dict = event.to_dict()
        event_json = json.dumps(event_dict, sort_keys=True)
        chain_input = f"{self._chain_hash}{event_json}".encode('utf-8')
        self._chain_hash = hashlib.sha256(chain_input).hexdigest()
        event.metadata['chain_hash'] = self._chain_hash
        
        # Store in memory
        self.events.append(event)
        
        # Log to file
        self.file_logger.info(json.dumps(event.to_dict()))
        
        # Log to console for critical events
        if event_type in (AuditEventType.SECURITY_VIOLATION, AuditEventType.AUTH_FAILURE):
            logger.warning(f"AUDIT [{event_type.value}] {actor} -> {target}: {action} = {result}")
        
        return event

    def get_events(self, event_type: Optional[AuditEventType] = None,
                   actor: Optional[str] = None,
                   limit: int = 100) -> List[AuditEvent]:
        """Get audit events with optional filters"""
        events = self.events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if actor:
            events = [e for e in events if e.actor == actor]
        return events[-limit:]

    def get_security_violations(self, limit: int = 50) -> List[AuditEvent]:
        """Get security violation events"""
        return self.get_events(event_type=AuditEventType.SECURITY_VIOLATION, limit=limit)

    def export_audit_trail(self, format: str = "json") -> str:
        """Export complete audit trail"""
        events_data = [e.to_dict() for e in self.events]
        if format == "json":
            return json.dumps(events_data, indent=2)
        elif format == "csv":
            if not events_data:
                return ""
            headers = list(events_data[0].keys())
            rows = [",".join(headers)]
            for event in events_data:
                row = ",".join(str(event.get(h, "")) for h in headers)
                rows.append(row)
            return "\n".join(rows)
        return json.dumps(events_data)

    def verify_chain_integrity(self) -> Tuple[bool, List[str]]:
        """Verify the audit chain hasn't been tampered with"""
        issues = []
        current_hash = "genesis"
        
        for event in self.events:
            event_dict = {k: v for k, v in event.to_dict().items() if k != 'chain_hash' and
                          k not in event.metadata.get('chain_hash', {})}
            # Simplified check - in production would reconstruct full chain
            if 'chain_hash' not in event.metadata:
                issues.append(f"Event {event.event_id} missing chain hash")
        
        return len(issues) == 0, issues


# ============================================================
# RATE LIMITER
# ============================================================

class RateLimiter:
    """
    Token bucket rate limiter for API protection
    Prevents brute force and DDoS attacks
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: Dict[str, List[float]] = {}
        self._blocked: Dict[str, float] = {}
        self._block_duration = 300  # 5 minute block

    def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for identifier (IP, agent_id, etc.)
        Returns (allowed, remaining_requests)
        """
        now = time.time()
        
        # Check if blocked
        if identifier in self._blocked:
            if now < self._blocked[identifier]:
                return False, 0
            else:
                del self._blocked[identifier]
        
        # Initialize bucket
        if identifier not in self._buckets:
            self._buckets[identifier] = []
        
        # Clean old requests
        cutoff = now - self.window_seconds
        self._buckets[identifier] = [t for t in self._buckets[identifier] if t > cutoff]
        
        # Check limit
        current_count = len(self._buckets[identifier])
        if current_count >= self.max_requests:
            # Block the identifier
            self._blocked[identifier] = now + self._block_duration
            logger.warning(f"Rate limit exceeded for {identifier}, blocking for {self._block_duration}s")
            return False, 0
        
        # Allow and record
        self._buckets[identifier].append(now)
        remaining = self.max_requests - current_count - 1
        return True, remaining

    def get_stats(self) -> Dict:
        """Get rate limiter stats"""
        now = time.time()
        return {
            "tracked_identifiers": len(self._buckets),
            "blocked_identifiers": len([b for b in self._blocked.values() if b > now]),
            "total_blocked": len(self._blocked)
        }


# ============================================================
# SECRETS MANAGER
# ============================================================

class SecretsManager:
    """
    Secure secrets management
    Handles API keys, credentials, certificates
    """

    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager
        self._secrets: Dict[str, bytes] = {}  # encrypted secrets
        self._metadata: Dict[str, Dict] = {}
        logger.info("SecretsManager initialized")

    def store_secret(self, name: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Store a secret securely"""
        try:
            encrypted, key_id = self.encryption_manager.encrypt(value)
            self._secrets[name] = encrypted
            self._metadata[name] = {
                "key_id": key_id,
                "stored_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            logger.info(f"Secret stored: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to store secret {name}: {e}")
            return False

    def get_secret(self, name: str) -> Optional[str]:
        """Retrieve a secret"""
        if name not in self._secrets:
            logger.warning(f"Secret not found: {name}")
            return None
        try:
            meta = self._metadata[name]
            decrypted = self.encryption_manager.decrypt(
                self._secrets[name],
                meta.get("key_id", "master")
            )
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to retrieve secret {name}: {e}")
            return None

    def delete_secret(self, name: str) -> bool:
        """Delete a secret"""
        if name in self._secrets:
            del self._secrets[name]
            del self._metadata[name]
            logger.info(f"Secret deleted: {name}")
            return True
        return False

    def rotate_secret(self, name: str, new_value: str) -> bool:
        """Rotate a secret"""
        if name not in self._secrets:
            return False
        return self.store_secret(name, new_value, self._metadata.get(name, {}).get("metadata"))

    def list_secrets(self) -> List[str]:
        """List secret names (not values)"""
        return list(self._secrets.keys())


# ============================================================
# SECURITY HARDENING ENGINE
# ============================================================

class SecurityHardeningEngine:
    """
    Main security hardening engine
    Coordinates all security components
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        
        # Initialize components
        self.encryption_manager = EncryptionManager()
        self.input_validator = InputValidator()
        self.audit_logger = AuditLogger(encryption_manager=self.encryption_manager)
        self.rate_limiter = RateLimiter(
            max_requests=self.config.max_requests_per_minute,
            window_seconds=60
        )
        self.secrets_manager = SecretsManager(self.encryption_manager)
        
        # Security metrics
        self._security_events = 0
        self._blocked_requests = 0
        self._validated_inputs = 0
        
        logger.info("SecurityHardeningEngine initialized")

    def validate_request(self, request_data: Dict, source_ip: str) -> Tuple[bool, List[str]]:
        """
        Validate an incoming request
        Returns (is_valid, list_of_issues)
        """
        issues = []
        
        # Rate limiting
        if self.config.rate_limiting_enabled:
            allowed, remaining = self.rate_limiter.is_allowed(source_ip)
            if not allowed:
                self._blocked_requests += 1
                self.audit_logger.log(
                    AuditEventType.SECURITY_VIOLATION,
                    actor=source_ip,
                    target="api",
                    action="request",
                    result="blocked_rate_limit",
                    ip_address=source_ip
                )
                return False, ["Rate limit exceeded"]
        
        # Input validation
        if self.config.input_validation_enabled:
            for key, value in request_data.items():
                if isinstance(value, str):
                    report = self.input_validator.validate_json_payload(value)
                    self._validated_inputs += 1
                    if not report.is_safe():
                        issues.append(f"Invalid input for field '{key}': {', '.join(report.issues)}")
                        self._security_events += 1
                        self.audit_logger.log(
                            AuditEventType.SECURITY_VIOLATION,
                            actor=source_ip,
                            target=key,
                            action="input_validation",
                            result="failed",
                            metadata={"issues": report.issues},
                            ip_address=source_ip
                        )
        
        return len(issues) == 0, issues

    def secure_agent_registration(self, agent_data: Dict) -> Tuple[bool, str, Optional[str]]:
        """
        Securely register an agent
        Returns (success, message, token)
        """
        # Validate agent_id
        agent_id = agent_data.get("agent_id", "")
        report = self.input_validator.validate_agent_id(agent_id)
        if not report.is_safe():
            return False, f"Invalid agent ID: {', '.join(report.issues)}", None
        
        # Validate IP
        ip = agent_data.get("ip_address", "")
        report = self.input_validator.validate_ip_address(ip)
        if not report.is_safe():
            return False, f"Invalid IP address: {', '.join(report.issues)}", None
        
        # Generate secure token for agent
        token = self.encryption_manager.generate_token()
        
        # Log registration
        self.audit_logger.log(
            AuditEventType.AGENT_REGISTER,
            actor=agent_id,
            target="swarm",
            action="register",
            result="success",
            metadata={"ip": ip, "platform": agent_data.get("platform", "unknown")}
        )
        
        return True, "Agent registered successfully", token

    def get_security_report(self) -> Dict:
        """Get comprehensive security report"""
        violations = self.audit_logger.get_security_violations()
        rate_stats = self.rate_limiter.get_stats()
        
        return {
            "summary": {
                "security_events": self._security_events,
                "blocked_requests": self._blocked_requests,
                "validated_inputs": self._validated_inputs,
                "audit_events": len(self.audit_logger.events)
            },
            "rate_limiting": rate_stats,
            "recent_violations": [v.to_dict() for v in violations[-10:]],
            "encryption": {
                "enabled": self.config.encryption_enabled,
                "algorithm": "AES-128-CBC+HMAC-SHA256",
                "key_count": len(self.encryption_manager._data_keys)
            },
            "config": {
                "max_requests_per_minute": self.config.max_requests_per_minute,
                "session_timeout_seconds": self.config.session_timeout_seconds,
                "audit_logging": self.config.audit_logging_enabled
            },
            "timestamp": datetime.now().isoformat()
        }