#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ORM for index server."""
import logging
from time import sleep
from peewee import OperationalError, CharField, IntegerField, BigIntegerField, Model
from playhouse.db_url import connect
from pacifica.uniqueid.config import get_config

SCHEMA_MAJOR = 1
SCHEMA_MINOR = 0
DB = connect(get_config().get('database', 'peewee_url'))


class OrmSync:
    """
    Special module for syncing the orm.

    This module should incorporate a schema migration strategy.

    The supported versions migrating forward must be in a versions array
    containing tuples for major and minor versions.

    The version tuples are directly translated to method names in the
    ``OrmSync`` class for the update between those versions.

    Example Version Control::

        class OrmSync:
            versions = [
                (0, 1),
                (0, 2),
                (1, 0),
                (1, 1)
            ]
            def update_0_1_to_0_2():
                pass
            def update_0_2_to_1_0():
                pass


    The body of an update method should follow peewee migration practices.
    http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#migrate
    """

    versions = [
        (0, 0),
        (1, 0)
    ]

    @staticmethod
    def dbconn_blocking():
        """Wait for the db connection."""
        dbcon_attempts = get_config().getint('database', 'connect_attempts')
        dbcon_wait = get_config().getint('database', 'connect_wait')
        while dbcon_attempts:
            try:
                UniqueIndex.database_connect()
                return
            except OperationalError:
                # couldnt connect, potentially wait and try again
                sleep(dbcon_wait)
                dbcon_attempts -= 1
        raise OperationalError('Failed database connect retry.')

    @classmethod
    def update_0_0_to_1_0(cls):
        """Update by adding the boolean column."""
        if not UniqueIndex.table_exists():
            UniqueIndex.create_table()

    @classmethod
    def update_tables(cls):
        """Update the database to the current version."""
        verlist = cls.versions
        db_ver = UniqueIndexSystem.get_version()
        if verlist.index(verlist[-1]) == verlist.index(db_ver):
            # we have the current version don't update
            return db_ver
        with UniqueIndex.atomic():
            for db_ver in verlist[verlist.index(db_ver):-1]:
                next_db_ver = verlist[verlist.index(db_ver)+1]
                method_name = 'update_{}_to_{}'.format(
                    '{}_{}'.format(*db_ver),
                    '{}_{}'.format(*next_db_ver)
                )
                getattr(cls, method_name)()
            UniqueIndexSystem.drop_table()
            UniqueIndexSystem.create_table()
            return UniqueIndexSystem.get_or_create_version()


class UniqueIndexBase(Model):
    """UniqueIndex base model for database setup."""

    # pylint: disable=too-few-public-methods
    class Meta:
        """Map to the database connected above."""

        database = DB
        only_save_dirty = True
    # pylint: enable=too-few-public-methods


class UniqueIndexSystem(UniqueIndexBase):
    """UniqueIndex Schema Version Model."""

    part = CharField(primary_key=True)
    value = IntegerField(default=-1)

    @classmethod
    def get_or_create_version(cls):
        """Set or create the current version of the schema."""
        if not cls.table_exists():
            return (0, 0)
        major, _created = cls.get_or_create(part='major', value=SCHEMA_MAJOR)
        minor, _created = cls.get_or_create(part='minor', value=SCHEMA_MINOR)
        return (major, minor)

    @classmethod
    def get_version(cls):
        """Get the current version as a tuple."""
        if not cls.table_exists():
            return (0, 0)
        return (cls.get(part='major').value, cls.get(part='minor').value)

    @classmethod
    def is_equal(cls):
        """Check to see if schema version matches code version."""
        major, minor = cls.get_version()
        return major == SCHEMA_MAJOR and minor == SCHEMA_MINOR

    @classmethod
    def is_safe(cls):
        """Check to see if the schema version is safe for the code."""
        major, _minor = cls.get_version()
        return major == SCHEMA_MAJOR


class UniqueIndex(UniqueIndexBase):
    """Auto-generated by pwiz maps a python record to a mysql table."""

    idid = CharField(primary_key=True, db_column='id')
    index = BigIntegerField(db_column='index')

    @classmethod
    def atomic(cls):
        """Get the atomic context or decorator."""
        # pylint: disable=no-member
        return cls._meta.database.atomic()
        # pylint: enable=no-member

    @classmethod
    def database_connect(cls):
        """
        Make sure database is connected.

        Trying to connect a second time doesnt cause any problems.
        """
        peewee_logger = logging.getLogger('peewee')
        peewee_logger.debug('Connecting to database.')
        # pylint: disable=no-member
        if not cls._meta.database.is_closed():  # pragma no cover
            cls._meta.database.close()
        cls._meta.database.connect()
        # pylint: enable=no-member

    @classmethod
    def database_close(cls):
        """
        Close the database connection.

        Closing already closed database throws an error so catch it and continue on.
        """
        peewee_logger = logging.getLogger('peewee')
        peewee_logger.debug('Closing database connection.')
        # pylint: disable=no-member
        if not cls._meta.database.is_closed():  # pragma no cover
            cls._meta.database.close()
        # pylint: enable=no-member


def update_index(id_range, id_mode):
    """Update the index for a mode and returns a unique start and stop index."""
    index = -1
    with UniqueIndex.atomic():
        if id_range and id_mode and id_range > 0:
            record = UniqueIndex.get_or_create(
                idid=id_mode, defaults={'index': 1})[0]
            index = int(record.index)
            record.index = index + id_range
            record.save()
        else:
            index = -1
            id_range = int(-1)
    return (index, id_range)
