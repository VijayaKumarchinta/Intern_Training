import psycopg2

from utils.logger import logger

from database.connection import (
    db,
    DatabaseError,
    ConflictError,
)

class MachineService:
    def add_machine(self, machine_name):
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {db.schema}.machines (machine_name)
                    VALUES (%s)
                    RETURNING id, machine_name
                    """,
                    (machine_name,),
                )
                row = cursor.fetchone()

            machine = {"machine_id": row[0], "machine_name": row[1]}
            logger.info("Machine created: machine_id=%s machine_name=%s", row[0], row[1])
            return machine

        except psycopg2.errors.UniqueViolation:
            logger.warning("Machine creation conflict: machine_name=%s already exists", machine_name)
            raise ConflictError(
                f"A machine named '{machine_name}' already exists."
            ) from None

        except DatabaseError:
            raise

        except Exception as error:
            raise DatabaseError(f"Failed to add machine: {error}") from error

    def get_all_machines(self):
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, machine_name
                    FROM {db.schema}.machines
                    ORDER BY id
                    """
                )
                rows = cursor.fetchall()

            machines = [
                {"machine_id": row[0], "machine_name": row[1]} for row in rows
            ]
            logger.info("Machines retrieved: count=%s", len(machines))
            return machines

        except Exception as error:
            raise DatabaseError(f"Failed to retrieve machines: {error}") from error

    def get_machine(self, machine_id):
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, machine_name
                    FROM {db.schema}.machines
                    WHERE id = %s
                    """,
                    (machine_id,),
                )
                row = cursor.fetchone()

            if not row:
                logger.warning("Machine not found: machine_id=%s", machine_id)
                return None

            machine = {"machine_id": row[0], "machine_name": row[1]}
            logger.info("Machine retrieved: machine_id=%s", machine_id)
            return machine

        except Exception as error:
            raise DatabaseError(f"Failed to retrieve machine: {error}") from error

    def update_machine(self, machine_id, machine_name):
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE {db.schema}.machines
                    SET machine_name = %s
                    WHERE id = %s
                    RETURNING id, machine_name
                    """,
                    (machine_name, machine_id),
                )
                row = cursor.fetchone()

            if not row:
                logger.warning("Machine update failed: machine_id=%s not found", machine_id)
                return None

            machine = {"machine_id": row[0], "machine_name": row[1]}
            logger.info("Machine updated: machine_id=%s machine_name=%s", row[0], row[1])
            return machine

        except psycopg2.errors.UniqueViolation:
            logger.warning(
                "Machine update conflict: machine_id=%s machine_name=%s already exists",
                machine_id, machine_name
            )
            raise ConflictError(
                f"A machine named '{machine_name}' already exists."
            ) from None

        except Exception as error:
            raise DatabaseError(f"Failed to update machine: {error}") from error

    def delete_machine(self, machine_id):
        try:
            with db.cursor() as cursor:
                cursor.execute(
                    f"""
                    DELETE FROM {db.schema}.machines
                    WHERE id = %s
                    """,
                    (machine_id,),
                )
                deleted = cursor.rowcount > 0

            if deleted:
                logger.info("Machine deleted: machine_id=%s", machine_id)
            else:
                logger.warning("Machine delete failed: machine_id=%s not found", machine_id)

            return deleted

        except Exception as error:
            raise DatabaseError(f"Failed to delete machine: {error}") from error

    def count_machines(self):
        try:
            with db.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {db.schema}.machines")
                (count,) = cursor.fetchone()

            return count

        except Exception as error:
            raise DatabaseError(f"Failed to count machines: {error}") from error

machine_service = MachineService()