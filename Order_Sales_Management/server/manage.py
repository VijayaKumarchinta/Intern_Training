import click
from app import create_app
from app.constants import Role
from app.extensions import db, hash_password
from app.models import User

app = create_app()

@app.cli.command("create-admin")
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--name", default="Administrator")
def create_admin(email, password, name):
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        click.echo("Invalid email")
        return
    if not password or len(password) < 8:
        click.echo("Password must be at least 8 characters")
        return
    if User.query.filter(db.func.lower(User.email) == email).first():
        click.echo("Email already registered")
        return
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=name,
        role=Role.ADMIN.value,
        is_verified=True,
    )
    db.session.add(user)
    db.session.commit()
    click.echo(f"Admin created: id={user.id} email={user.email}")