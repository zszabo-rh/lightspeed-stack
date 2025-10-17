"""User and cluster quota scheduler runner."""

from typing import Any
from threading import Thread
from time import sleep

import sqlite3
import psycopg2

import constants
from log import get_logger
from models.config import (
    Configuration,
    QuotaHandlersConfiguration,
    QuotaLimiterConfiguration,
    PostgreSQLDatabaseConfiguration,
    SQLiteDatabaseConfiguration,
)

logger = get_logger(__name__)


CREATE_QUOTA_TABLE = """
    CREATE TABLE IF NOT EXISTS quota_limits (
        id              text NOT NULL,
        subject         char(1) NOT NULL,
        quota_limit     int NOT NULL,
        available       int,
        updated_at      timestamp with time zone,
        revoked_at      timestamp with time zone,
        PRIMARY KEY(id, subject)
    );
    """


INCREASE_QUOTA_STATEMENT = """
    UPDATE quota_limits
       SET available=available+%s, revoked_at=NOW()
     WHERE subject=%s
       AND revoked_at < NOW() - INTERVAL %s ;
    """

RESET_QUOTA_STATEMENT = """
    UPDATE quota_limits
       SET available=%s, revoked_at=NOW()
     WHERE subject=%s
       AND revoked_at < NOW() - INTERVAL %s ;
    """


def quota_scheduler(config: QuotaHandlersConfiguration) -> bool:
    """Quota scheduler task."""
    if config is None:
        logger.warning("Quota limiters are not configured, skipping")
        return False

    if config.sqlite is None and config.postgres is None:
        logger.warning("Storage for quota limiter is not set, skipping")
        return False

    if len(config.limiters) == 0:
        logger.warning("No limiters are setup, skipping")
        return False

    connection = connect(config)
    if connection is None:
        logger.warning("Can not connect to database, skipping")
        return False

    init_tables(connection)
    period = config.scheduler.period

    logger.info(
        "Quota scheduler started in separated thread with period set to %d seconds",
        period,
    )

    while True:
        logger.info("Quota scheduler sync started")
        for limiter in config.limiters:
            try:
                quota_revocation(connection, limiter)
            except Exception as e:
                logger.error("Quota revoke error: %s", e)
        logger.info("Quota scheduler sync finished")
        sleep(period)
    # unreachable code
    connection.close()
    return True


def quota_revocation(
    connection: Any, quota_limiter: QuotaLimiterConfiguration
) -> None:
    """Quota revocation mechanism."""
    logger.info(
        "Quota revocation mechanism for limiter '%s' of type '%s'",
        quota_limiter.name,
        quota_limiter.type,
    )

    if quota_limiter.type is None:
        raise Exception("Limiter type not set, skipping revocation")

    if quota_limiter.period is None:
        raise Exception("Limiter period not set, skipping revocation")

    subject_id = get_subject_id(quota_limiter.type)

    if quota_limiter.quota_increase is not None:
        increase_quota(
            connection, subject_id, quota_limiter.quota_increase, quota_limiter.period
        )

    if quota_limiter.initial_quota is not None and quota_limiter.initial_quota > 0:
        reset_quota(
            connection, subject_id, quota_limiter.initial_quota, quota_limiter.period
        )


def increase_quota(
    connection: Any, subject_id: str, increase_by: int, period: str
) -> None:
    """Increase quota by specified amount."""
    logger.info(
        "Increasing quota for subject '%s' by %d when period %s is reached",
        subject_id,
        increase_by,
        period,
    )

    update_statement = INCREASE_QUOTA_STATEMENT

    with connection.cursor() as cursor:
        cursor.execute(
            update_statement,
            (
                increase_by,
                subject_id,
                period,
            ),
        )
        logger.info("Changed %d rows in database", cursor.rowcount)


def reset_quota(connection: Any, subject_id: str, reset_to: int, period: str) -> None:
    """Reset quota to specified amount."""
    logger.info(
        "Reseting quota for subject '%s' to %d when period %s is reached",
        subject_id,
        reset_to,
        period,
    )

    update_statement = RESET_QUOTA_STATEMENT

    with connection.cursor() as cursor:
        cursor.execute(
            update_statement,
            (
                reset_to,
                subject_id,
                period,
            ),
        )
        logger.info("Changed %d rows in database", cursor.rowcount)


def get_subject_id(limiter_type: str) -> str:
    """Get subject ID based on quota limiter type."""
    match limiter_type:
        case constants.USER_QUOTA_LIMITER:
            return "u"
        case constants.CLUSTER_QUOTA_LIMITER:
            return "c"
        case _:
            return "?"


def connect(config: QuotaHandlersConfiguration) -> Any:
    """Initialize connection to database."""
    logger.info("Initializing connection to quota limiter database")
    if config.postgres is not None:
        return connect_pg(config.postgres)
    if config.sqlite is not None:
        return connect_sqlite(config.sqlite)


def connect_pg(config: PostgreSQLDatabaseConfiguration) -> Any:
    """Initialize connection to PostgreSQL database."""
    logger.info("Connecting to PostgreSQL storage")
    connection = psycopg2.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password.get_secret_value(),
        dbname=config.db,
        sslmode=config.ssl_mode,
        # sslrootcert=config.ca_cert_path,
        gssencmode=config.gss_encmode,
    )
    if connection is not None:
        connection.autocommit = True
    return connection

def connect_sqlite(config: SQLiteDatabaseConfiguration) -> None:
    """Initialize connection to database."""
    logger.info("Connecting to SQLite storage")
    # make sure the connection will have known state
    # even if SQLite is not alive
    connection = None
    try:
        connection = sqlite3.connect(database=config.db_path)
    except sqlite3.Error as e:
        if connection is not None:
            connection.close()
        logger.exception("Error initializing SQLite cache:\n%s", e)
        raise
    connection.autocommit = True
    return connection


def init_tables(connection: Any) -> None:
    """Initialize tables used by quota limiter."""
    logger.info("Initializing tables for quota limiter")
    cursor = connection.cursor()
    cursor.execute(CREATE_QUOTA_TABLE)
    cursor.close()
    connection.commit()


def start_quota_scheduler(configuration: Configuration) -> None:
    """Start user and cluster quota scheduler in separate thread."""
    logger.info("Starting quota scheduler")
    thread = Thread(
        target=quota_scheduler,
        daemon=True,
        args=(configuration.quota_handlers,),
    )
    thread.start()
