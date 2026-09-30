BEGIN;

ALTER TABLE "FactSupplierOrderItems"
ADD COLUMN IF NOT EXISTS order_price NUMERIC(14, 2);

UPDATE "FactSupplierOrderItems"
SET order_price = 0
WHERE order_price IS NULL;

ALTER TABLE "FactSupplierOrderItems"
ALTER COLUMN order_price SET NOT NULL;

COMMIT;
