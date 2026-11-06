/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class KamaleonTouchSales extends Component {
    static template = "kamaleon_erp.TouchSales";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");

        this.state = useState({
            // Pantalla: 'welcome' | 'catalog' | 'orders'
            screen: "welcome",
            loading: true,
            confirming: false,
            partners: [],
            pricelists: [],
            categories: [],
            products: [],
            productPrices: {},
            volumeRules: {},
            partnerSearch: "",
            selectedPartnerId: null,
            selectedPartnerName: "",
            selectedPartnerBlocked: false,
            selectedPartnerBlockedInfo: "",
            selectedPricelistId: null,
            selectedCategoryId: "all",
            searchQuery: "",
            cart: [],
            confirmedOrder: null,
            showMobileCart: false,
            orderNote: "",
            // Sección Mis Pedidos
            orders: [],
            ordersLoading: false,
            orderFilter: "all", // 'all' | 'to_invoice' | 'invoiced' | 'cancel'
            orderSearch: "",
            expandedOrderId: null,
            // Sección Mis Clientes (Directorio Solo Vista)
            clientSearch: "",
            clientFilter: "all", // 'all' | 'credit_ok' | 'credit_blocked' | 'has_phone'
            viewingPartner: null, // Objeto de cliente para modal de Solo Vista
        });

        onWillStart(async () => {
            await Promise.all([
                this.loadInitData(),
                this.loadSellerOrders(),
            ]);
        });
    }

    async switchScreen(targetScreen) {
        this.state.screen = targetScreen;
        if (targetScreen === "orders") {
            await this.loadSellerOrders();
        }
    }

    async loadSellerOrders() {
        this.state.ordersLoading = true;
        try {
            const orders = await this.orm.call("kamaleon.touch.sales", "get_seller_orders", []);
            this.state.orders = orders || [];
        } catch (error) {
            console.error("Error cargando pedidos:", error);
            this.notification.add("No se pudieron cargar los pedidos.", { type: "danger" });
        } finally {
            this.state.ordersLoading = false;
        }
    }

    onOrderSearchInput(ev) {
        this.state.orderSearch = ev.target.value;
    }

    setOrderFilter(filter) {
        this.state.orderFilter = filter;
    }

    toggleOrderDetails(orderId) {
        if (this.state.expandedOrderId === orderId) {
            this.state.expandedOrderId = null;
        } else {
            this.state.expandedOrderId = orderId;
        }
    }

    get filteredOrders() {
        let list = this.state.orders || [];
        if (this.state.orderFilter !== "all") {
            list = list.filter(o => o.calc_status === this.state.orderFilter);
        }
        const q = (this.state.orderSearch || "").toLowerCase().trim();
        if (q) {
            list = list.filter(o =>
                (o.name && o.name.toLowerCase().includes(q)) ||
                (o.partner_name && o.partner_name.toLowerCase().includes(q)) ||
                (o.partner_vat && o.partner_vat.toLowerCase().includes(q)) ||
                (o.note && o.note.toLowerCase().includes(q)) ||
                (o.invoices && o.invoices.some(inv => inv.name && inv.name.toLowerCase().includes(q)))
            );
        }
        return list;
    }

    getOrderStatusCount(status) {
        if (!this.state.orders) return 0;
        if (status === "all") return this.state.orders.length;
        return this.state.orders.filter(o => o.calc_status === status).length;
    }

    async loadInitData() {
        this.state.loading = true;
        try {
            console.log("Cargando datos del Cotizador Touch...");
            const data = await this.orm.call("kamaleon.touch.sales", "get_touch_init_data", []);
            console.log("Cotizador Touch init data received:", data);
            if (data && data.error) {
                console.warn("Cotizador Touch Data Warning:", data.error);
            }
            this.state.partners = (data && data.partners) || [];
            this.state.pricelists = (data && data.pricelists) || [];
            this.state.categories = (data && data.categories) || [];
            this.state.products = (data && data.products) || [];
            this.state.productPrices = (data && data.product_prices) || {};
            this.state.volumeRules = (data && data.volume_rules) || {};

            for (let prod of this.state.products) {
                prod.computed_price = this.state.productPrices[prod.id] !== undefined ? this.state.productPrices[prod.id] : prod.lst_price;
                prod.volume_rules = this.state.volumeRules[prod.id] || [];
            }

            console.log(`Partners cargados en estado: ${this.state.partners.length}`);

            if (this.state.pricelists.length > 0) {
                this.state.selectedPricelistId = this.state.pricelists[0].id;
                await this.updatePricelistPrices();
            }
            if (data && data.is_vendedor_touch) {
                document.body.classList.add("o_vendedor_touch_mode");
            } else {
                document.body.classList.remove("o_vendedor_touch_mode");
            }
        } catch (error) {
            console.error("Error cargando Cotizador Touch:", error);
        } finally {
            this.state.loading = false;
        }
    }

    // ── Welcome & Clients screen ────────────────────────────────────

    get filteredPartners() {
        const q = (this.state.partnerSearch || "").toLowerCase().trim();
        if (!q) return this.state.partners;
        return this.state.partners.filter(p =>
            (p.name && p.name.toLowerCase().includes(q)) ||
            (p.vat && p.vat.toLowerCase().includes(q)) ||
            (p.vat_display && p.vat_display.toLowerCase().includes(q)) ||
            (p.phone && p.phone.toLowerCase().includes(q)) ||
            (p.mobile && p.mobile.toLowerCase().includes(q)) ||
            (p.address && p.address.toLowerCase().includes(q)) ||
            (p.route_name && p.route_name.toLowerCase().includes(q))
        );
    }

    onPartnerSearchInput(ev) {
        this.state.partnerSearch = ev.target.value;
    }

    // ── Mis Clientes (Directorio Solo Vista) ──────────────────────────
    onClientSearchInput(ev) {
        this.state.clientSearch = ev.target.value;
    }

    setClientFilter(filter) {
        this.state.clientFilter = filter;
    }

    viewPartnerDetails(partner, ev = null) {
        if (ev && typeof ev.stopPropagation === "function") {
            ev.stopPropagation();
        }
        this.state.viewingPartner = partner;
    }

    closePartnerDetails() {
        this.state.viewingPartner = null;
    }

    startQuotationForPartner(partner) {
        this.closePartnerDetails();
        this.selectPartner(partner);
        if (!this.state.selectedPartnerBlocked) {
            this.proceedToCatalog();
        } else {
            this.switchScreen('welcome');
            this.notification.add(
                `Cliente bloqueado por crédito: ${partner.x_blocked_invoice_info || 'Mora superior a 3 días'}`,
                { type: 'warning' }
            );
        }
    }

    get filteredClients() {
        let list = this.state.partners || [];
        if (this.state.clientFilter === "credit_ok") {
            list = list.filter(p => !p.x_is_credit_blocked || p.x_credit_blocked_override);
        } else if (this.state.clientFilter === "credit_blocked") {
            list = list.filter(p => p.x_is_credit_blocked && !p.x_credit_blocked_override);
        } else if (this.state.clientFilter === "has_phone") {
            list = list.filter(p => Boolean(p.phone || p.mobile));
        }
        const q = (this.state.clientSearch || "").toLowerCase().trim();
        if (q) {
            list = list.filter(p =>
                (p.name && p.name.toLowerCase().includes(q)) ||
                (p.vat && p.vat.toLowerCase().includes(q)) ||
                (p.vat_display && p.vat_display.toLowerCase().includes(q)) ||
                (p.phone && p.phone.toLowerCase().includes(q)) ||
                (p.mobile && p.mobile.toLowerCase().includes(q)) ||
                (p.address && p.address.toLowerCase().includes(q)) ||
                (p.route_name && p.route_name.toLowerCase().includes(q))
            );
        }
        return list;
    }

    getClientFilterCount(filter) {
        if (!this.state.partners) return 0;
        if (filter === "all") return this.state.partners.length;
        if (filter === "credit_ok") return this.state.partners.filter(p => !p.x_is_credit_blocked || p.x_credit_blocked_override).length;
        if (filter === "credit_blocked") return this.state.partners.filter(p => p.x_is_credit_blocked && !p.x_credit_blocked_override).length;
        if (filter === "has_phone") return this.state.partners.filter(p => Boolean(p.phone || p.mobile)).length;
        return 0;
    }

    async selectPartner(partner) {
        this.state.selectedPartnerId = partner.id;
        this.state.selectedPartnerName = partner.name;

        const isBlocked = partner.x_is_credit_blocked && !partner.x_credit_blocked_override;
        this.state.selectedPartnerBlocked = isBlocked;
        this.state.selectedPartnerBlockedInfo = partner.x_blocked_invoice_info || "";

        if (isBlocked) {
            this.notification.add(
                `⛔ CLIENTE BLOQUEADO POR MOROSIDAD: ${partner.name} posee facturas con más de 3 días sin cancelar (${partner.x_blocked_invoice_info || 'Mora'}). Requiere autorización de Administración.`,
                { type: "danger", sticky: true }
            );
        }

        if (partner.property_product_pricelist) {
            const plistId = partner.property_product_pricelist[0];
            if (this.state.pricelists.some(pl => pl.id === plistId)) {
                this.state.selectedPricelistId = plistId;
            }
        }
        await this.updatePricelistPrices();
    }

    async onPricelistChange(ev) {
        this.state.selectedPricelistId = parseInt(ev.target.value) || null;
        await this.updatePricelistPrices();
    }

    async updatePricelistPrices() {
        if (!this.state.selectedPricelistId) return;
        try {
            const data = await this.orm.call(
                "kamaleon.touch.sales",
                "get_pricelist_prices",
                [this.state.selectedPricelistId, this.state.selectedPartnerId]
            );
            if (data) {
                const prices = data.prices || data;
                this.state.productPrices = prices;
                this.state.volumeRules = data.volume_rules || {};
                for (let prod of this.state.products) {
                    prod.computed_price = prices[prod.id] !== undefined ? prices[prod.id] : prod.lst_price;
                    prod.volume_rules = this.state.volumeRules[prod.id] || [];
                }
                for (let item of this.state.cart) {
                    item.price = this.getPriceForQty(item.product, item.qty);
                }
            }
        } catch (error) {
            console.error("Error cargando precios de lista:", error);
        }
    }

    getPriceForQty(product, qty = 1) {
        if (!product) return 0.0;
        const rules = this.state.volumeRules && this.state.volumeRules[product.id];
        if (rules && rules.length > 0) {
            let bestPrice = null;
            for (let r of rules) {
                if (qty >= r.min_qty) {
                    bestPrice = r.price;
                }
            }
            if (bestPrice !== null) return bestPrice;
        }
        return product.computed_price !== undefined ? product.computed_price : (product.lst_price || 0.0);
    }

    getProductPrice(product) {
        return this.getPriceForQty(product, 1);
    }

    async proceedToCatalog() {
        if (!this.state.selectedPartnerId) {
            this.notification.add("Selecciona un cliente para continuar.", { type: "warning" });
            return;
        }

        if (this.state.selectedPartnerBlocked) {
            this.notification.add(
                `⛔ CLIENTE BLOQUEADO: No se puede cotizar a ${this.state.selectedPartnerName} por poseer facturas vencidas (> 3 días). Solicite permiso a Administración.`,
                { type: "danger", sticky: true }
            );
            return;
        }

        await this.updatePricelistPrices();
        this.state.screen = "catalog";
        this.state.showMobileCart = false;
    }

    backToWelcome() {
        this.state.screen = "welcome";
        this.state.cart = [];
        this.state.confirmedOrder = null;
        this.state.showMobileCart = false;
    }

    toggleMobileCart() {
        this.state.showMobileCart = !this.state.showMobileCart;
    }

    // ── Catalog screen ───────────────────────────────────────────────

    onCategorySelect(categId) {
        this.state.selectedCategoryId = categId;
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
    }

    get filteredProducts() {
        let prods = this.state.products;
        if (this.state.selectedCategoryId !== "all") {
            prods = prods.filter(p => p.categ_id && p.categ_id[0] === this.state.selectedCategoryId);
        }
        const q = this.state.searchQuery.toLowerCase().trim();
        if (q) {
            prods = prods.filter(p =>
                (p.name && p.name.toLowerCase().includes(q)) ||
                (p.default_code && p.default_code.toLowerCase().includes(q)) ||
                (p.barcode && p.barcode.toLowerCase().includes(q))
            );
        }
        return prods;
    }

    getCartItem(productId) {
        return this.state.cart.find(item => item.product.id === productId);
    }

    getProductQty(productId) {
        const item = this.getCartItem(productId);
        return item ? item.qty : 0;
    }

    addToCart(product, delta = 1) {
        let item = this.getCartItem(product.id);
        if (item) {
            item.qty += delta;
            if (item.qty <= 0) {
                this.removeFromCart(product.id);
            } else {
                item.price = this.getPriceForQty(item.product, item.qty);
            }
        } else if (delta > 0) {
            const price = this.getPriceForQty(product, delta);
            this.state.cart.push({ product, qty: delta, price: price });
        }
    }

    updateCartQty(productId, qty) {
        const parsed = parseFloat(qty);
        if (isNaN(parsed) || parsed <= 0) {
            this.removeFromCart(productId);
        } else {
            const item = this.getCartItem(productId);
            if (item) {
                item.qty = parsed;
                item.price = this.getPriceForQty(item.product, parsed);
            }
        }
    }

    removeFromCart(productId) {
        this.state.cart = this.state.cart.filter(item => item.product.id !== productId);
    }

    clearCart() {
        this.state.cart = [];
        this.state.confirmedOrder = null;
    }

    get cartTotal() {
        return this.state.cart.reduce((sum, item) => sum + item.qty * item.price, 0);
    }

    get selectedPricelistName() {
        const pl = this.state.pricelists.find(p => p.id === this.state.selectedPricelistId);
        return pl ? pl.name : "—";
    }

    onOrderNoteInput(ev) {
        this.state.orderNote = ev.target.value;
    }

    async confirmOrder() {
        if (this.state.cart.length === 0) {
            this.notification.add("La cesta está vacía.", { type: "warning" });
            return;
        }
        this.state.confirming = true;
        try {
            const lines = this.state.cart.map(item => ({
                product_id: item.product.id,
                qty: item.qty,
                price_unit: item.price,
            }));
            const res = await this.orm.call("kamaleon.touch.sales", "create_and_confirm_touch_order", [
                this.state.selectedPartnerId,
                this.state.selectedPricelistId,
                lines,
                this.state.orderNote,
            ]);
            this.state.confirmedOrder = res;
            this.state.cart = [];
            this.state.orderNote = "";
            this.notification.add(`¡Pedido ${res.order_name} confirmado!`, { type: "success" });
            // Recargar lista de pedidos automáticamente
            await this.loadSellerOrders();
        } catch (error) {
            console.error("Error al confirmar pedido:", error);
            this.notification.add(error.message || "Error al confirmar el pedido.", { type: "danger" });
        } finally {
            this.state.confirming = false;
        }
    }

    openOrderView(orderId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "sale.order",
            res_id: orderId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    newOrder() {
        this.state.confirmedOrder = null;
        this.state.cart = [];
        this.state.orderNote = "";
        this.state.showMobileCart = false;
    }
}

registry.category("actions").add("kamaleon_touch_sales", KamaleonTouchSales);
