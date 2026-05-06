#!/bin/bash
echo "Running DB migrations..."

docker exec -it ims_postgres psql -U ims_user -d ims_db -c "
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS is_auto_assigned BOOLEAN DEFAULT FALSE;
ALTER TABLE incidents ALTER COLUMN severity TYPE VARCHAR(10);
ALTER TABLE incidents ALTER COLUMN status TYPE VARCHAR(50);
"

echo "Migrations complete."
