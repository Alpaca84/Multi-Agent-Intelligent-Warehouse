import asyncio
import asyncpg
import os
import bcrypt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def reset_password():
    try:
        conn = await asyncpg.connect(
            host="timescaledb",
            user="warehouse",
            password=os.environ.get("POSTGRES_PASSWORD", "changeme"),
            database="warehouse",
        )
        print("Connected to DB")

        # Check if admin exists
        row = await conn.fetchrow(
            "SELECT id, username, hashed_password FROM users WHERE username = 'admin'"
        )
        if not row:
            print("User 'admin' NOT FOUND. Creating it...")
            password = "VantagePoint2025!"
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode(
                "utf-8"
            )
            await conn.execute(
                """
                INSERT INTO users (username, email, full_name, hashed_password, role, status)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
                "admin",
                "admin@warehouse.com",
                "System Administrator",
                hashed_password,
                "admin",
                "active",
            )
            print(f"User 'admin' created with password: {password}")
        else:
            print(f"User 'admin' found (ID: {row['id']}). Resetting password...")
            password = "VantagePoint2025!"
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode(
                "utf-8"
            )

            await conn.execute(
                "UPDATE users SET hashed_password = $1 WHERE username = 'admin'",
                hashed_password,
            )
            print(f"Password for 'admin' updated to: {password}")

        await conn.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(reset_password())
