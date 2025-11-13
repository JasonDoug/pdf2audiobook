from __future__ import with_statement

import os
import sys
from logging.config import fileConfig

from sqlalchemy import Column, Integer, MetaData, Table, engine_from_config, pool
from sqlalchemy.dialects import postgresql

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get the DATABASE_URL from environment variables
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.models import Base

target_metadata = Base.metadata


# Custom function to handle ENUM types more gracefully
def check_and_create_enums(connection):
    """Check if ENUM types exist and create them if they don't"""
    enum_types = {
        "producttype": ["subscription", "one_time"],
        "subscriptiontier": ["free", "pro", "enterprise"],
        "voiceprovider": ["openai", "google", "aws_polly", "azure", "eleven_labs"],
        "conversionmode": ["full", "summary_explanation"],
        "jobstatus": ["pending", "processing", "completed", "failed"],
    }

    for enum_name, enum_values in enum_types.items():
        try:
            # Check if enum exists
            result = connection.execute(
                "SELECT 1 FROM pg_type WHERE typname = %s", (enum_name,)
            ).fetchone()

            if not result:
                # Create enum type
                values_str = "', '".join(enum_values)
                connection.execute(f"CREATE TYPE {enum_name} AS ENUM ('{values_str}')")
                print(f"Created ENUM type: {enum_name}")
        except Exception as e:
            print(f"Error handling enum {enum_name}: {e}")
            # Continue even if enum creation fails
            pass


# other values from the config, defined by the needs of env.py,
# can be acquired:-
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Check and create ENUM types before running migrations
        check_and_create_enums(connection)

        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
