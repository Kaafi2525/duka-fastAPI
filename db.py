from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings


DATABASE_URL = settings.database_url.strip().strip('"').strip("'")
connect_args = {}

if DATABASE_URL.startswith('sqlite'):
    prefix = 'sqlite:///./'
    if DATABASE_URL.startswith(prefix):
        rel_path = DATABASE_URL[len(prefix):]
        project_root = Path(__file__).resolve().parent
        db_file = (project_root / rel_path).resolve()
        DATABASE_URL = f'sqlite:///{db_file.as_posix()}'
    connect_args = {'check_same_thread': False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
