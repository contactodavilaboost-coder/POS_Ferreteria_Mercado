import odoo
import sys

db_name = sys.argv[1] if len(sys.argv) > 1 else 'said_express'
print(f"Starting SQL cleanup on {db_name}...")
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', db_name])
db = odoo.sql_db.db_connect(db_name)
registry = odoo.modules.registry.Registry.new(db_name)

with registry.cursor() as cr:
    # 1. Clear reconciliations & commissions
    cr.execute("DELETE FROM account_partial_reconcile;")
    cr.execute("DELETE FROM sale_commission;")
    
    # 2. Clear payments & moves
    cr.execute("DELETE FROM account_payment;")
    cr.execute("DELETE FROM account_move_line;")
    cr.execute("DELETE FROM account_move;")
    
    # 3. Clear stock valuation, quants, moves, pickings
    cr.execute("DELETE FROM stock_valuation_layer;")
    cr.execute("DELETE FROM stock_quant;")
    cr.execute("DELETE FROM stock_move_line;")
    cr.execute("DELETE FROM stock_move;")
    cr.execute("DELETE FROM stock_picking;")
    
    # 4. Clear sales & purchases
    cr.execute("DELETE FROM sale_order_line;")
    cr.execute("DELETE FROM sale_order;")
    cr.execute("DELETE FROM purchase_order_line;")
    cr.execute("DELETE FROM purchase_order;")
    
    # 5. Reset sequence counters
    cr.execute("UPDATE ir_sequence SET number_next = 1 WHERE code IN ('sale.order', 'purchase.order', 'stock.picking');")
    cr.execute("UPDATE ir_sequence SET number_next = 1 WHERE name ILIKE '%invoice%' OR name ILIKE '%factura%' OR code ILIKE '%account.move%';")
    
    cr.commit()
    print(f"Cleaned {db_name} successfully!")
