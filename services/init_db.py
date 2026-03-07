# init_db.py
from services.backend.database import engine
from services.backend import models

print("🗑️  Dropping all tables...")
models.Base.metadata.drop_all(bind=engine)
print("✅ Tables dropped successfully!")

print("🔄 Creating new tables with updated schema...")
models.Base.metadata.create_all(bind=engine)
print("✅ Database created successfully!")
print("🎉 All done! Your database now has the correct schema.")