"""Model with service configuration."""

from pathlib import Path
from typing import Optional, Any, Pattern
from enum import Enum
from functools import cached_property
import re

import jsonpath_ng
from jsonpath_ng.exceptions import JSONPathError
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
    constr,
    FilePath,
    AnyHttpUrl,
    PositiveInt,
    NonNegativeInt,
    SecretStr,
)

from pydantic.dataclasses import dataclass
from typing_extensions import Self, Literal

import constants

from utils import checks


class ConfigurationBase(BaseModel):
    """Base class for all configuration models that rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")


class TLSConfiguration(ConfigurationBase):
    """TLS configuration."""

    tls_certificate_path: Optional[FilePath] = None
    tls_key_path: Optional[FilePath] = None
    tls_key_password: Optional[FilePath] = None

    @model_validator(mode="after")
    def check_tls_configuration(self) -> Self:
        """Check TLS configuration."""
        return self


class CORSConfiguration(ConfigurationBase):
    """CORS configuration."""

    allow_origins: list[str] = [
        "*"
    ]  # not AnyHttpUrl: we need to support "*" that is not valid URL
    allow_credentials: bool = False
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]

    @model_validator(mode="after")
    def check_cors_configuration(self) -> Self:
        """Check CORS configuration."""
        # credentials are not allowed with wildcard origins per CORS/Fetch spec.
        # see https://fastapi.tiangolo.com/tutorial/cors/
        if self.allow_credentials and "*" in self.allow_origins:
            raise ValueError(
                "Invalid CORS configuration: allow_credentials can not be set to true when "
                "allow origins contains '*' wildcard."
                "Use explicit origins or disable credential."
            )
        return self


class SQLiteDatabaseConfiguration(ConfigurationBase):
    """SQLite database configuration."""

    db_path: str


class InMemoryCacheConfig(ConfigurationBase):
    """In-memory cache configuration."""

    max_entries: PositiveInt


class PostgreSQLDatabaseConfiguration(ConfigurationBase):
    """PostgreSQL database configuration."""

    host: str = "localhost"
    port: PositiveInt = 5432
    db: str
    user: str
    password: SecretStr
    namespace: Optional[str] = "lightspeed-stack"
    ssl_mode: str = constants.POSTGRES_DEFAULT_SSL_MODE
    gss_encmode: str = constants.POSTGRES_DEFAULT_GSS_ENCMODE
    ca_cert_path: Optional[FilePath] = None

    @model_validator(mode="after")
    def check_postgres_configuration(self) -> Self:
        """Check PostgreSQL configuration."""
        if self.port > 65535:
            raise ValueError("Port value should be less than 65536")
        return self


class DatabaseConfiguration(ConfigurationBase):
    """Database configuration."""

    sqlite: Optional[SQLiteDatabaseConfiguration] = None
    postgres: Optional[PostgreSQLDatabaseConfiguration] = None

    @model_validator(mode="after")
    def check_database_configuration(self) -> Self:
        """Check that exactly one database type is configured."""
        total_configured_dbs = sum([self.sqlite is not None, self.postgres is not None])

        if total_configured_dbs == 0:
            # Default to SQLite in a (hopefully) tmpfs if no database configuration is provided.
            # This is good for backwards compatibility for deployments that do not mind having
            # no persistent database.
            sqlite_file_name = "/tmp/lightspeed-stack.db"
            self.sqlite = SQLiteDatabaseConfiguration(db_path=sqlite_file_name)
        elif total_configured_dbs > 1:
            raise ValueError("Only one database configuration can be provided")

        return self

    @property
    def db_type(self) -> Literal["sqlite", "postgres"]:
        """Return the configured database type."""
        if self.sqlite is not None:
            return "sqlite"
        if self.postgres is not None:
            return "postgres"
        raise ValueError("No database configuration found")

    @property
    def config(self) -> SQLiteDatabaseConfiguration | PostgreSQLDatabaseConfiguration:
        """Return the active database configuration."""
        if self.sqlite is not None:
            return self.sqlite
        if self.postgres is not None:
            return self.postgres
        raise ValueError("No database configuration found")


class ServiceConfiguration(ConfigurationBase):
    """Service configuration."""

    host: str = "localhost"
    port: PositiveInt = 8080
    auth_enabled: bool = False
    workers: PositiveInt = 1
    color_log: bool = True
    access_log: bool = True
    tls_config: TLSConfiguration = Field(default_factory=TLSConfiguration)
    cors: CORSConfiguration = Field(default_factory=CORSConfiguration)

    @model_validator(mode="after")
    def check_service_configuration(self) -> Self:
        """Check service configuration."""
        if self.port > 65535:
            raise ValueError("Port value should be less than 65536")
        return self


class ModelContextProtocolServer(ConfigurationBase):
    """model context protocol server configuration."""

    name: str
    provider_id: str = "model-context-protocol"
    url: str


class LlamaStackConfiguration(ConfigurationBase):
    """Llama stack configuration."""

    url: Optional[str] = None
    api_key: Optional[SecretStr] = None
    use_as_library_client: Optional[bool] = None
    library_client_config_path: Optional[str] = None

    @model_validator(mode="after")
    def check_llama_stack_model(self) -> Self:
        """
        Validate the Llama stack configuration after model initialization.

        Ensures that either a URL is provided for server mode or library client
        mode is explicitly enabled. If library client mode is enabled, verifies
        that a configuration file path is specified and points to an existing,
        readable file. Raises a ValueError if any required condition is not
        met.

        Returns:
            Self: The validated LlamaStackConfiguration instance.
        """
        if self.url is None:
            if self.use_as_library_client is None:
                raise ValueError(
                    "Llama stack URL is not specified and library client mode is not specified"
                )
            if self.use_as_library_client is False:
                raise ValueError(
                    "Llama stack URL is not specified and library client mode is not enabled"
                )
        if self.use_as_library_client is None:
            self.use_as_library_client = False
        if self.use_as_library_client:
            if self.library_client_config_path is None:
                # pylint: disable=line-too-long
                raise ValueError(
                    "Llama stack library client mode is enabled but a configuration file path is not specified"  # noqa: E501
                )
            # the configuration file must exists and be regular readable file
            checks.file_check(
                Path(self.library_client_config_path), "Llama Stack configuration file"
            )
        return self


class UserDataCollection(ConfigurationBase):
    """User data collection configuration."""

    feedback_enabled: bool = False
    feedback_storage: Optional[str] = None
    transcripts_enabled: bool = False
    transcripts_storage: Optional[str] = None

    @model_validator(mode="after")
    def check_storage_location_is_set_when_needed(self) -> Self:
        """Check that storage_location is set when enabled."""
        if self.feedback_enabled:
            if self.feedback_storage is None:
                raise ValueError(
                    "feedback_storage is required when feedback is enabled"
                )
            checks.directory_check(
                Path(self.feedback_storage),
                desc="Check directory to store feedback",
                must_exists=False,
                must_be_writable=True,
            )
        if self.transcripts_enabled:
            if self.transcripts_storage is None:
                raise ValueError(
                    "transcripts_storage is required when transcripts is enabled"
                )
            checks.directory_check(
                Path(self.transcripts_storage),
                desc="Check directory to store transcripts",
                must_exists=False,
                must_be_writable=True,
            )
        return self


class JsonPathOperator(str, Enum):
    """Supported operators for JSONPath evaluation."""

    EQUALS = "equals"
    CONTAINS = "contains"
    IN = "in"
    MATCH = "match"


class JwtRoleRule(ConfigurationBase):
    """Rule for extracting roles from JWT claims."""

    jsonpath: str  # JSONPath expression to evaluate against the JWT payload
    operator: JsonPathOperator  # Comparison operator
    negate: bool = False  # If True, negate the rule
    value: Any  # Value to compare against
    roles: list[str]  # Roles to assign if rule matches

    @model_validator(mode="after")
    def check_jsonpath(self) -> Self:
        """Verify that the JSONPath expression is valid."""
        try:
            jsonpath_ng.parse(self.jsonpath)
            return self
        except JSONPathError as e:
            raise ValueError(
                f"Invalid JSONPath expression: {self.jsonpath}: {e}"
            ) from e

    @model_validator(mode="after")
    def check_roles(self) -> Self:
        """Ensure that at least one role is specified."""
        if not self.roles:
            raise ValueError("At least one role must be specified in the rule")

        if len(self.roles) != len(set(self.roles)):
            raise ValueError("Roles must be unique in the rule")

        if any(role == "*" for role in self.roles):
            raise ValueError(
                "The wildcard '*' role is not allowed in role rules, "
                "everyone automatically gets this role"
            )

        return self

    @model_validator(mode="after")
    def check_regex_pattern(self) -> Self:
        """Verify that regex patterns are valid for MATCH operator."""
        if self.operator == JsonPathOperator.MATCH:
            if not isinstance(self.value, str):
                raise ValueError(
                    f"MATCH operator requires a string pattern, {type(self.value).__name__}"
                )
            try:
                re.compile(self.value)
            except re.error as e:
                raise ValueError(
                    f"Invalid regex pattern for MATCH operator: {self.value}: {e}"
                ) from e
        return self

    @cached_property
    def compiled_regex(self) -> Optional[Pattern[str]]:
        """Return compiled regex pattern for MATCH operator, None otherwise."""
        if self.operator == JsonPathOperator.MATCH and isinstance(self.value, str):
            return re.compile(self.value)
        return None


class Action(str, Enum):
    """Available actions in the system."""

    # Special action to allow unrestricted access to all actions
    ADMIN = "admin"

    # List the conversations of other users
    LIST_OTHERS_CONVERSATIONS = "list_other_conversations"

    # Read the contents of conversations of other users
    READ_OTHERS_CONVERSATIONS = "read_other_conversations"

    # Continue the conversations of other users
    QUERY_OTHERS_CONVERSATIONS = "query_other_conversations"

    # Delete the conversations of other users
    DELETE_OTHERS_CONVERSATIONS = "delete_other_conversations"

    # Access the query endpoint
    QUERY = "query"

    # Access the streaming query endpoint
    STREAMING_QUERY = "streaming_query"

    # Access the conversation endpoint
    GET_CONVERSATION = "get_conversation"

    # List own conversations
    LIST_CONVERSATIONS = "list_conversations"

    # Access the conversation delete endpoint
    DELETE_CONVERSATION = "delete_conversation"

    # Access the conversation update endpoint
    UPDATE_CONVERSATION = "update_conversation"
    FEEDBACK = "feedback"
    GET_MODELS = "get_models"
    GET_TOOLS = "get_tools"
    GET_SHIELDS = "get_shields"
    LIST_PROVIDERS = "list_providers"
    GET_PROVIDER = "get_provider"
    GET_METRICS = "get_metrics"
    GET_CONFIG = "get_config"

    INFO = "info"
    # Allow overriding model/provider via request
    MODEL_OVERRIDE = "model_override"


class AccessRule(ConfigurationBase):
    """Rule defining what actions a role can perform."""

    role: str  # Role name
    actions: list[Action]  # Allowed actions for this role


class AuthorizationConfiguration(ConfigurationBase):
    """Authorization configuration."""

    access_rules: list[AccessRule] = Field(
        default_factory=list
    )  # Rules for role-based access control


class JwtConfiguration(ConfigurationBase):
    """JWT configuration."""

    user_id_claim: str = constants.DEFAULT_JWT_UID_CLAIM
    username_claim: str = constants.DEFAULT_JWT_USER_NAME_CLAIM
    role_rules: list[JwtRoleRule] = Field(
        default_factory=list
    )  # Rules for extracting roles from JWT claims


class JwkConfiguration(ConfigurationBase):
    """JWK configuration."""

    url: AnyHttpUrl
    jwt_configuration: JwtConfiguration = Field(default_factory=JwtConfiguration)


class AuthenticationConfiguration(ConfigurationBase):
    """Authentication configuration."""

    module: str = constants.DEFAULT_AUTHENTICATION_MODULE
    skip_tls_verification: bool = False
    k8s_cluster_api: Optional[AnyHttpUrl] = None
    k8s_ca_cert_path: Optional[FilePath] = None
    jwk_config: Optional[JwkConfiguration] = None

    @model_validator(mode="after")
    def check_authentication_model(self) -> Self:
        """Validate YAML containing authentication configuration section."""
        if self.module not in constants.SUPPORTED_AUTHENTICATION_MODULES:
            supported_modules = ", ".join(constants.SUPPORTED_AUTHENTICATION_MODULES)
            raise ValueError(
                f"Unsupported authentication module '{self.module}'. "
                f"Supported modules: {supported_modules}"
            )

        if self.module == constants.AUTH_MOD_JWK_TOKEN:
            if self.jwk_config is None:
                raise ValueError(
                    "JWK configuration must be specified when using JWK token authentication"
                )

        return self

    @property
    def jwk_configuration(self) -> JwkConfiguration:
        """Return JWK configuration if the module is JWK token."""
        if self.module != constants.AUTH_MOD_JWK_TOKEN:
            raise ValueError(
                "JWK configuration is only available for JWK token authentication module"
            )
        if self.jwk_config is None:
            raise ValueError("JWK configuration should not be None")
        return self.jwk_config


@dataclass
class CustomProfile:
    """Custom profile customization for prompts and validation."""

    path: str
    prompts: dict[str, str] = Field(default={}, init=False)

    def __post_init__(self) -> None:
        """Validate and load profile."""
        self._validate_and_process()

    def _validate_and_process(self) -> None:
        """Validate and load the profile."""
        checks.file_check(Path(self.path), "custom profile")
        profile_module = checks.import_python_module("profile", self.path)
        if profile_module is not None and checks.is_valid_profile(profile_module):
            self.prompts = profile_module.PROFILE_CONFIG.get("system_prompts", {})

    def get_prompts(self) -> dict[str, str]:
        """Retrieve prompt attribute."""
        return self.prompts


class Customization(ConfigurationBase):
    """Service customization."""

    profile_path: Optional[str] = None
    disable_query_system_prompt: bool = False
    system_prompt_path: Optional[FilePath] = None
    system_prompt: Optional[str] = None
    custom_profile: Optional[CustomProfile] = Field(default=None, init=False)

    @model_validator(mode="after")
    def check_customization_model(self) -> Self:
        """Load customizations."""
        if self.profile_path:
            self.custom_profile = CustomProfile(path=self.profile_path)
        elif self.system_prompt_path is not None:
            checks.file_check(self.system_prompt_path, "system prompt")
            self.system_prompt = checks.get_attribute_from_file(
                dict(self), "system_prompt_path"
            )
        return self


class InferenceConfiguration(ConfigurationBase):
    """Inference configuration."""

    default_model: Optional[str] = None
    default_provider: Optional[str] = None

    @model_validator(mode="after")
    def check_default_model_and_provider(self) -> Self:
        """Check default model and provider."""
        if self.default_model is None and self.default_provider is not None:
            raise ValueError(
                "Default model must be specified when default provider is set"
            )
        if self.default_model is not None and self.default_provider is None:
            raise ValueError(
                "Default provider must be specified when default model is set"
            )
        return self


class ConversationCacheConfiguration(ConfigurationBase):
    """Conversation cache configuration."""

    type: Literal["noop", "memory", "sqlite", "postgres"] | None = None
    memory: Optional[InMemoryCacheConfig] = None
    sqlite: Optional[SQLiteDatabaseConfiguration] = None
    postgres: Optional[PostgreSQLDatabaseConfiguration] = None

    @model_validator(mode="after")
    def check_cache_configuration(self) -> Self:
        """Check conversation cache configuration."""
        # if any backend config is provided, type must be explicitly selected
        if self.type is None:
            if any([self.memory, self.sqlite, self.postgres]):
                raise ValueError(
                    "Conversation cache type must be set when backend configuration is provided"
                )
            # no type selected + no configuration is expected and fully supported
            return self
        match self.type:
            case constants.CACHE_TYPE_MEMORY:
                if self.memory is None:
                    raise ValueError("Memory cache is selected, but not configured")
                # no other DBs configuration allowed
                if any([self.sqlite, self.postgres]):
                    raise ValueError("Only memory cache config must be provided")
            case constants.CACHE_TYPE_SQLITE:
                if self.sqlite is None:
                    raise ValueError("SQLite cache is selected, but not configured")
                # no other DBs configuration allowed
                if any([self.memory, self.postgres]):
                    raise ValueError("Only SQLite cache config must be provided")
            case constants.CACHE_TYPE_POSTGRES:
                if self.postgres is None:
                    raise ValueError("PostgreSQL cache is selected, but not configured")
                # no other DBs configuration allowed
                if any([self.memory, self.sqlite]):
                    raise ValueError("Only PostgreSQL cache config must be provided")
        return self


class ByokRag(ConfigurationBase):
    """BYOK RAG configuration."""

    rag_id: constr(min_length=1)  # type:ignore
    rag_type: constr(min_length=1) = constants.DEFAULT_RAG_TYPE  # type:ignore
    embedding_model: constr(min_length=1) = (  # type:ignore
        constants.DEFAULT_EMBEDDING_MODEL
    )
    embedding_dimension: PositiveInt = constants.DEFAULT_EMBEDDING_DIMENSION
    vector_db_id: constr(min_length=1)  # type:ignore
    db_path: FilePath


class QuotaLimiterConfiguration(ConfigurationBase):
    """Configuration for one quota limiter."""

    type: Literal["user_limiter", "cluster_limiter"]
    name: str
    initial_quota: NonNegativeInt
    quota_increase: NonNegativeInt
    period: str


class QuotaSchedulerConfiguration(BaseModel):
    """Quota scheduler configuration."""

    period: PositiveInt = 1


class QuotaHandlersConfiguration(ConfigurationBase):
    """Quota limiter configuration."""

    sqlite: Optional[SQLiteDatabaseConfiguration] = None
    postgres: Optional[PostgreSQLDatabaseConfiguration] = None
    limiters: list[QuotaLimiterConfiguration] = Field(default_factory=list)
    scheduler: QuotaSchedulerConfiguration = Field(
        default_factory=QuotaSchedulerConfiguration
    )
    enable_token_history: bool = False


class ContextPreloadingTool(ConfigurationBase):
    """Configuration for a single context preloading tool."""

    tool_name: str
    mcp_server: str
    label: Optional[str] = None  # Optional label for the tool output
    empty_message: Optional[str] = None  # Message to display when result is empty


class AgentContextPreloading(ConfigurationBase):
    """Agent context preloading configuration."""

    enabled: bool = False
    intro_message: str = "Here is contextual information for this session:"
    tools: list[ContextPreloadingTool] = Field(default_factory=list)


class Configuration(ConfigurationBase):
    """Global service configuration."""

    name: str
    service: ServiceConfiguration
    llama_stack: LlamaStackConfiguration
    user_data_collection: UserDataCollection
    database: DatabaseConfiguration = Field(default_factory=DatabaseConfiguration)
    mcp_servers: list[ModelContextProtocolServer] = Field(default_factory=list)
    authentication: AuthenticationConfiguration = Field(
        default_factory=AuthenticationConfiguration
    )
    authorization: Optional[AuthorizationConfiguration] = None
    customization: Optional[Customization] = None
    inference: InferenceConfiguration = Field(default_factory=InferenceConfiguration)
    conversation_cache: ConversationCacheConfiguration = Field(
        default_factory=ConversationCacheConfiguration
    )
    byok_rag: list[ByokRag] = Field(default_factory=list)
    quota_handlers: QuotaHandlersConfiguration = Field(
        default_factory=QuotaHandlersConfiguration
    )
    agent_context_preloading: AgentContextPreloading = Field(
        default_factory=AgentContextPreloading
    )

    def dump(self, filename: str = "configuration.json") -> None:
        """Dump actual configuration into JSON file."""
        with open(filename, "w", encoding="utf-8") as fout:
            fout.write(self.model_dump_json(indent=4))
