BEGIN;

ALTER TABLE "FactCreditCardItems"
    ADD COLUMN IF NOT EXISTS category INTEGER;
ALTER TABLE "FactPurchases"
    ADD COLUMN IF NOT EXISTS credit_card_id INTEGER;

-- Preserva as conciliacoes antigas: purchase_id representava a categoria 12.
UPDATE "FactPurchases" AS purchase
SET credit_card_id = card_item.id
FROM "FactCreditCardItems" AS card_item
WHERE card_item.purchase_id = purchase.id
  AND purchase.credit_card_id IS NULL;

UPDATE "FactCreditCardItems"
SET category = 12
WHERE purchase_id IS NOT NULL
  AND category IS NULL;

ALTER TABLE "FactSupplierPayments"
    ADD COLUMN IF NOT EXISTS credit_card_id INTEGER;
ALTER TABLE "FactTaxes"
    ADD COLUMN IF NOT EXISTS credit_card_id INTEGER;
ALTER TABLE "FactFixos"
    ADD COLUMN IF NOT EXISTS credit_card_id INTEGER;
ALTER TABLE "FactEmployeePayrolls"
    ADD COLUMN IF NOT EXISTS credit_card_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_credit_card_items_category') THEN
        ALTER TABLE "FactCreditCardItems"
            ADD CONSTRAINT fk_credit_card_items_category
            FOREIGN KEY (category) REFERENCES "DimTransactionCategories"(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_supplier_payments_credit_card') THEN
        ALTER TABLE "FactSupplierPayments"
            ADD CONSTRAINT fk_supplier_payments_credit_card
            FOREIGN KEY (credit_card_id) REFERENCES "FactCreditCardItems"(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_purchases_credit_card') THEN
        ALTER TABLE "FactPurchases"
            ADD CONSTRAINT fk_purchases_credit_card
            FOREIGN KEY (credit_card_id) REFERENCES "FactCreditCardItems"(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_taxes_credit_card') THEN
        ALTER TABLE "FactTaxes"
            ADD CONSTRAINT fk_taxes_credit_card
            FOREIGN KEY (credit_card_id) REFERENCES "FactCreditCardItems"(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_fixos_credit_card') THEN
        ALTER TABLE "FactFixos"
            ADD CONSTRAINT fk_fixos_credit_card
            FOREIGN KEY (credit_card_id) REFERENCES "FactCreditCardItems"(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_payroll_credit_card') THEN
        ALTER TABLE "FactEmployeePayrolls"
            ADD CONSTRAINT fk_payroll_credit_card
            FOREIGN KEY (credit_card_id) REFERENCES "FactCreditCardItems"(id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_credit_card_items_category ON "FactCreditCardItems" (category);
CREATE INDEX IF NOT EXISTS ix_purchases_credit_card ON "FactPurchases" (credit_card_id);
CREATE INDEX IF NOT EXISTS ix_supplier_payments_credit_card ON "FactSupplierPayments" (credit_card_id);
CREATE INDEX IF NOT EXISTS ix_taxes_credit_card ON "FactTaxes" (credit_card_id);
CREATE INDEX IF NOT EXISTS ix_fixos_credit_card ON "FactFixos" (credit_card_id);
CREATE INDEX IF NOT EXISTS ix_payroll_credit_card ON "FactEmployeePayrolls" (credit_card_id);

ALTER TABLE "FactCreditCardItems"
    DROP CONSTRAINT IF EXISTS "FactCreditCardItems_purchase_id_fkey";
DROP INDEX IF EXISTS "ix_FactCreditCardItems_purchase_id";
ALTER TABLE "FactCreditCardItems"
    DROP COLUMN IF EXISTS purchase_id;

COMMIT;
