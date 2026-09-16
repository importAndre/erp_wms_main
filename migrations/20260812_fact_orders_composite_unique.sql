BEGIN;

ALTER TABLE "FactOrders"
DROP CONSTRAINT IF EXISTS "FactOrders_order_id_key";

ALTER TABLE "FactOrders"
DROP CONSTRAINT IF EXISTS uq_fact_orders_company_order_sku;

ALTER TABLE "FactOrders"
ADD CONSTRAINT uq_fact_orders_company_order_sku
UNIQUE (company_id, order_id, sku);

COMMIT;
