/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";

/**
 * Convierte strings con coma o punto a float exacto sin redondear
 */
export function parseLocaleFloat(val) {
    if (val === undefined || val === null || val === "") return 0.0;
    const str = String(val).trim().replace(',', '.');
    const num = parseFloat(str);
    return isNaN(num) ? 0.0 : num;
}

/**
 * Formatea la tasa de cambio con hasta 4 decimales exactos
 */
export function formatRate(rate) {
    if (!rate || isNaN(rate)) return "0.00";
    const num = parseFloat(rate);
    return num.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
}

/**
 * Formatea montos en Bolívares (VES) respetando hasta 3 decimales
 */
export function formatBs(amountUSD, rate, symbol = "Bs.") {
    if (!rate || isNaN(amountUSD)) return "";
    const totalBs = (amountUSD || 0) * rate;
    return `${symbol} ${totalBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 3 })}`;
}

/**
 * Patch de la Barra Superior (Navbar) para mostrar y editar la Tasa del Día con decimales exactos
 */
patch(Navbar.prototype, {
    get currentVesRate() {
        return this.pos.config.x_ves_rate || 0.0;
    },

    get formattedVesRate() {
        return formatRate(this.pos.config.x_ves_rate);
    },

    get isDualCurrencyEnabled() {
        return Boolean(this.pos.config.x_enable_dual_currency && this.pos.config.x_ves_rate > 0);
    },

    get isPosAdmin() {
        return Boolean(
            this.env?.services?.user?.isSystem ||
            this.env?.services?.user?.isAdmin ||
            this.pos?.user?.role === "admin"
        );
    },

    async onClickUpdateVesRate() {
        try {
            // RESTRICCIÓN: Solo los Administradores pueden cambiar la tasa del día
            if (!this.isPosAdmin) {
                const notif = this.env?.services?.notification || this.notification;
                if (notif) {
                    notif.add("Acceso denegado: Solo el Administrador puede modificar la tasa del día.", {
                        type: "danger",
                    });
                }
                return;
            }

            const currentVal = this.pos.config.x_ves_rate ? String(this.pos.config.x_ves_rate) : "";
            const newRateStr = await makeAwaitable(this.dialog, NumberPopup, {
                title: "Actualizar Tasa del Día BCV / VES (Bs/$)",
                subtitle: "Ingrese la tasa exacta con decimales (ej: 65.450)",
                startingValue: currentVal,
            });

            if (newRateStr !== undefined && newRateStr !== null && newRateStr !== "") {
                const newRate = parseLocaleFloat(newRateStr);
                if (newRate > 0) {
                    this.pos.config.x_ves_rate = newRate;
                    await this.pos.data.call("pos.config", "set_ves_rate", [
                        this.pos.config.id,
                        newRate,
                    ]);
                    const notif = this.env?.services?.notification || this.notification;
                    if (notif) {
                        notif.add(`Tasa del día actualizada a ${formatRate(newRate)} Bs/$`, {
                            type: "success",
                        });
                    }
                }
            }
        } catch (err) {
            console.error("Error al actualizar tasa en POS:", err);
        }
    },
});

/**
 * Detecta si un producto es de monto abierto en Bolívares (comodín / mix / verduras surtidas)
 */
export function isOpenPriceProduct(product) {
    if (!product) return false;
    if (product.x_open_price_ves) return true;
    const name = (product.display_name || product.name || "").toUpperCase();
    if (name.includes("SURTID") || name.includes("MIX VERDURA")) return true;
    return false;
}

/**
 * Busca de forma segura el producto 'Verduras surtidas' en la memoria del POS
 */
export function findVerdurasSurtidasProduct(pos) {
    if (!pos) return null;
    let allProducts = [];
    if (pos.models && pos.models['product.product']) {
        if (typeof pos.models['product.product'].getAll === 'function') {
            allProducts = pos.models['product.product'].getAll();
        } else if (Array.isArray(pos.models['product.product'].records)) {
            allProducts = pos.models['product.product'].records;
        } else if (Array.isArray(pos.models['product.product'])) {
            allProducts = pos.models['product.product'];
        }
    }
    if (!allProducts.length && pos.db && pos.db.product_by_id) {
        allProducts = Object.values(pos.db.product_by_id);
    }
    if (!allProducts.length && pos.data && pos.data.models && pos.data.models['product.product']) {
        const pModel = pos.data.models['product.product'];
        allProducts = typeof pModel.getAll === 'function' ? pModel.getAll() : (pModel.records || []);
    }

    // 1. Prioridad: coincide con "VERDURA" y "SURTID"
    let match = allProducts.find(p => {
        const name = (p.display_name || p.name || "").toUpperCase();
        return name.includes("VERDURA") && name.includes("SURTID");
    });
    if (match) return match;

    // 2. Prioridad: coincide con "SURTID" o "MIX VERDURA"
    match = allProducts.find(p => {
        const name = (p.display_name || p.name || "").toUpperCase();
        return name.includes("SURTID") || name.includes("MIX VERDURA");
    });
    if (match) return match;

    // 3. Prioridad: producto con flag x_open_price_ves
    match = allProducts.find(p => Boolean(p.x_open_price_ves));
    return match || null;
}

/**
 * Abre el popup de ingreso de monto en Bolívares, calcula el REF en USD y agrega el producto a la orden
 */
export async function promptOpenPriceBsForProduct(pos, dialog, notification, product, onAddFallback = null) {
    try {
        if (!pos) return;
        let order = pos.get_order();
        if (!order && typeof pos.add_new_order === "function") {
            pos.add_new_order();
            order = pos.get_order();
        }

        const rate = pos.config?.x_ves_rate || (pos.company && pos.company.x_ves_rate) || 65.0;
        const rateStr = formatRate(rate);

        const payload = await makeAwaitable(dialog, NumberPopup, {
            title: `🍈 ${product.display_name || product.name || "Verduras Surtidas"}`,
            subtitle: `Ingrese el monto a cobrar en Bolívares (Tasa: ${rateStr} Bs/$):`,
            startingValue: "",
        });

        if (!payload) return;

        const valStr = typeof payload === "object" ? (payload.payload || payload.value) : payload;
        const amountBs = parseLocaleFloat(valStr);
        if (!amountBs || isNaN(amountBs) || amountBs <= 0) return;

        const priceUSD = rate > 0 ? (amountBs / rate) : amountBs;

        // 1. Agregar el producto al carrito
        let line = null;
        const countBefore = (order.lines ? order.lines.length : 0) || (typeof order.get_orderlines === "function" ? order.get_orderlines().length : 0);

        if (typeof onAddFallback === "function") {
            try {
                await onAddFallback();
            } catch (e) {
                console.warn("[POS Open Price Bs] onAddFallback error:", e);
            }
        }

        let currentOrder = pos.get_order() || order;
        let currentLines = currentOrder.lines || (typeof currentOrder.get_orderlines === "function" ? currentOrder.get_orderlines() : []);
        let countAfter = currentLines.length || 0;

        // Si onAddFallback no agregó la línea, usar métodos directos del POS
        if (countAfter === countBefore) {
            if (typeof pos.addLineToCurrentOrder === "function") {
                line = await pos.addLineToCurrentOrder({ product_id: product });
            } else if (typeof currentOrder.addLineToCurrentOrder === "function") {
                line = await currentOrder.addLineToCurrentOrder({ product_id: product });
            } else if (typeof currentOrder.add_product === "function") {
                line = await currentOrder.add_product(product, {
                    price: priceUSD,
                    quantity: 1,
                    merge: false,
                });
            }
        }

        // 2. Obtener la línea creada
        currentOrder = pos.get_order() || order;
        if (!line && currentOrder) {
            if (typeof currentOrder.get_selected_orderline === "function") {
                line = currentOrder.get_selected_orderline();
            }
            if (!line && currentOrder.lines) {
                const linesArr = Array.isArray(currentOrder.lines) ? currentOrder.lines : Array.from(currentOrder.lines);
                if (linesArr.length > 0) {
                    line = linesArr[linesArr.length - 1];
                }
            }
            if (!line && typeof currentOrder.get_orderlines === "function") {
                const linesArr = currentOrder.get_orderlines();
                if (linesArr && linesArr.length > 0) {
                    line = linesArr[linesArr.length - 1];
                }
            }
        }

        // 3. Fijar el precio unitario exacto en USD (REF) y fijar modo manual
        if (line) {
            if (typeof line.set_unit_price === "function") {
                line.set_unit_price(priceUSD);
            } else {
                line.price_unit = priceUSD;
            }
            line.price_type = "manual";
            if (typeof line.set_quantity === "function") {
                line.set_quantity(1);
            } else {
                line.qty = 1;
            }
        }

        if (notification) {
            const formattedBs = amountBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            notification.add(
                `✅ ${product.display_name || product.name || "Verduras Surtidas"}: Bs. ${formattedBs} agregado al pedido`,
                { type: "success" }
            );
        }
    } catch (err) {
        console.error("[POS Open Price Bs] Error:", err);
    }
}

// Exponer en window para integración con keyboard shortcuts
if (typeof window !== "undefined") {
    window.__kamaleon_pos = window.__kamaleon_pos || {};
    window.__kamaleon_pos.findVerdurasSurtidasProduct = findVerdurasSurtidasProduct;
    window.__kamaleon_pos.promptOpenPriceBsForProduct = promptOpenPriceBsForProduct;
    window.__kamaleon_pos.isOpenPriceProduct = isOpenPriceProduct;
}

/**
 * Patch de ProductCard para mostrar el precio en Bolívares y permitir Monto Abierto en Bs.
 */
patch(ProductCard.prototype, {
    get priceInBs() {
        if (isOpenPriceProduct(this.props.product)) {
            return "🍈 Monto en Bs.";
        }
        const rate = this.env.services.pos?.config?.x_ves_rate;
        const enabled = this.env.services.pos?.config?.x_enable_dual_currency;
        if (!enabled || !rate || !this.props.product) return "";
        const priceUSD = this.props.product.get_price(this.env.services.pos?.get_order()?.pricelist_id, 1);
        return formatBs(priceUSD, rate, this.env.services.pos?.config?.x_secondary_currency_symbol || "Bs.");
    },

    async onCardClick(event) {
        if (isOpenPriceProduct(this.props.product)) {
            if (event && typeof event.stopPropagation === "function") {
                event.stopPropagation();
            }
            await this.promptOpenPriceBs(this.props.product, event);
            return;
        }
        if (typeof this.props.onClick === "function") {
            this.props.onClick(event);
        }
    },

    async promptOpenPriceBs(product, event) {
        const dialog = this.env.services.dialog;
        const pos = this.env.services.pos;
        const notification = this.env.services.notification;
        await promptOpenPriceBsForProduct(
            pos,
            dialog,
            notification,
            product,
            typeof this.props.onClick === "function" ? () => this.props.onClick(event || product) : null
        );
    },
});

/**
 * Patch de OrderWidget para mostrar el Total en Bolívares debajo del Total en USD
 */
patch(OrderWidget.prototype, {
    get totalInBs() {
        const pos = this.env.services.pos;
        if (!pos?.config?.x_enable_dual_currency || !pos?.config?.x_ves_rate) return "";
        const order = pos.get_order();
        if (!order) return "";
        const totalUSD = order.get_total_with_tax();
        return formatBs(totalUSD, pos.config.x_ves_rate, pos.config.x_secondary_currency_symbol || "Bs.");
    },
});

/**
 * ============================================================
 * ESTRATEGIA DE PAGO: BOLÍVARES PUROS + CALCULADORA EFECTIVO $
 * ============================================================
 * Los montos de pago se guardan en Bolívares directamente.
 * NO se divide por la tasa → NO hay error de redondeo USD.
 * El display muestra el valor tal cual (ya está en Bs).
 * La única multiplicación × tasa es para el TOTAL del pedido
 * (que Odoo almacena en USD → convertimos a Bs para comparar).
 * ============================================================
 */

/**
 * Helper: total del pedido en Bs
 */
function orderTotalBs(order, rate) {
    if (!order || !rate) return 0;
    return ((order.getTotalDue ? order.getTotalDue() : 0)) * rate;
}

/**
 * Helper: suma pagado en Bs (todas las líneas excepto `skipLine`)
 */
function sumPaidBs(order, skipLine) {
    return (order.payment_ids || []).reduce((acc, l) => {
        if (l === skipLine) return acc;
        const amt = typeof l.get_amount === "function" ? l.get_amount() : (l.amount || 0);
        return acc + amt;
    }, 0);
}

/**
 * Patch de PaymentScreen
 */
patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        const order = this.currentOrder;
        this.usdCalcState = useState({
            usdReceived: order?.x_usd_received || 0,
            usdCharged: order?.x_usd_charged || 0,
            changeUsd: order?.x_usd_change_usd || 0,
            changeBs: order?.x_usd_change_bs || 0,
        });
        if (typeof window !== "undefined") {
            window.__kamaleon_pos = window.__kamaleon_pos || {};
            window.__kamaleon_pos.promptCustomUsdBill = () => this.onClickCustomUsdBill();
        }
    },

    /** Total del pedido convertido a Bs para la cabecera */
    get totalDueInBs() {
        const pos = this.pos;
        if (!pos?.config?.x_enable_dual_currency || !pos?.config?.x_ves_rate) return "";
        const order = this.currentOrder;
        if (!order) return "";
        return formatBs(order.getTotalDue(), pos.config.x_ves_rate,
            pos.config.x_secondary_currency_symbol || "Bs.");
    },

    /** Indica si hay un cálculo de billete en dólares activo en la orden actual */
    get hasUsdCashCalc() {
        const recv = this.usdCalcState?.usdReceived || this.currentOrder?.x_usd_received || 0;
        return recv > 0;
    },

    get usdReceivedFormatted() {
        const val = this.usdCalcState?.usdReceived || this.currentOrder?.x_usd_received || 0;
        return `$ ${val.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    },

    get usdChargedFormatted() {
        const val = this.usdCalcState?.usdCharged || this.currentOrder?.x_usd_charged || 0;
        return `$ ${val.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    },

    get usdChangeUsdFormatted() {
        const val = this.usdCalcState?.changeUsd || this.currentOrder?.x_usd_change_usd || 0;
        return `$ ${val.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    },

    get usdChangeBsFormatted() {
        const symbol = this.pos?.config?.x_secondary_currency_symbol || "Bs.";
        const val = this.usdCalcState?.changeBs || this.currentOrder?.x_usd_change_bs || 0;
        return `${symbol} ${val.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    },

    /**
     * Calcula el vuelto en Bolívares cuando el cliente entrega un billete en Dólares ($),
     * manteniendo el registro contable de la venta por el monto neto en Bs.
     */
    async applyUsdCashBill(usdAmount) {
        const order = this.currentOrder;
        const pos = this.pos;
        const rate = pos?.config?.x_ves_rate || 0;
        if (!order || !rate || !usdAmount || usdAmount <= 0) return;

        const totalBs = Math.round(orderTotalBs(order, rate) * 100) / 100;

        // 1. Buscar o crear la línea de pago en Efectivo
        let lines = order.payment_ids || [];
        let cashLine = lines.find((l) => {
            const mName = (l.payment_method_id?.name || l.payment_method?.name || l.name || "").toLowerCase();
            return mName.includes("efectivo") || mName.includes("cash") || mName.includes("divisa");
        });

        if (!cashLine && lines.length === 1) {
            cashLine = lines[0];
        }

        if (!cashLine) {
            const methods = this.payment_methods_from_config || pos.payment_methods || [];
            let cashMethod = methods.find((m) => {
                const n = (m.name || "").toLowerCase();
                return n.includes("efectivo") || n.includes("cash") || n.includes("divisa");
            }) || methods[0];

            if (cashMethod) {
                await this.addNewPaymentLine(cashMethod);
                lines = order.payment_ids || [];
                cashLine = lines[lines.length - 1] || null;
            }
        }

        // 2. Calcular cuánto debe cubrir el billete en $ (descontando otros pagos como Pago Móvil/Punto)
        const otherPaidBs = cashLine ? sumPaidBs(order, cashLine) : sumPaidBs(order, null);
        let dueForCashBs = Math.max(0, Math.round((totalBs - otherPaidBs) * 100) / 100);
        if (dueForCashBs <= 0) {
            dueForCashBs = totalBs;
        }

        const usdGivenBs = Math.round(usdAmount * rate * 100) / 100;
        let lineAmountBs = dueForCashBs;
        let usdCharged = Math.round((dueForCashBs / rate) * 100) / 100;
        let changeBs = 0;
        let changeUsd = 0;

        if (usdGivenBs >= dueForCashBs) {
            // El billete cubre el total pendiente: registramos solo el neto de la venta y calculamos el vuelto en Bs
            lineAmountBs = dueForCashBs;
            usdCharged = Math.round((dueForCashBs / rate) * 100) / 100;
            changeBs = Math.max(0, Math.round((usdGivenBs - dueForCashBs) * 100) / 100);
            changeUsd = Math.max(0, Math.round((usdAmount - usdCharged) * 100) / 100);
        } else {
            // Pago parcial en dólares (ej: cuenta de $25 y entrega un billete de $20, el resto lo paga en Bs)
            lineAmountBs = usdGivenBs;
            usdCharged = usdAmount;
            changeBs = 0;
            changeUsd = 0;
        }

        if (cashLine) {
            if (typeof cashLine.set_amount === "function") {
                cashLine.set_amount(lineAmountBs);
            } else {
                cashLine.amount = lineAmountBs;
            }
            const symbol = pos?.config?.x_secondary_currency_symbol || "Bs.";
            const noteInfo = `Efectivo (Recibido: ${symbol} ${usdGivenBs.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} | Vuelto: ${symbol} ${changeBs.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })})`;
            if (typeof cashLine.update === "function") {
                cashLine.update({ ticket: noteInfo, payment_ref: noteInfo });
            } else {
                cashLine.ticket = noteInfo;
                cashLine.payment_ref = noteInfo;
            }
        }

        // 3. Guardar en la orden y en el estado reactivo para pantalla y boleta
        order.x_usd_received = usdAmount;
        order.x_usd_received_bs = usdGivenBs;
        order.x_usd_charged = usdCharged;
        order.x_usd_change_usd = changeUsd;
        order.x_usd_change_bs = changeBs;

        if (this.usdCalcState) {
            this.usdCalcState.usdReceived = usdAmount;
            this.usdCalcState.usdCharged = usdCharged;
            this.usdCalcState.changeUsd = changeUsd;
            this.usdCalcState.changeBs = changeBs;
        }
    },

    async onClickUsdBill(amount) {
        await this.applyUsdCashBill(Number(amount));
    },

    async onClickCustomUsdBill() {
        try {
            const order = this.currentOrder;
            const rate = this.pos?.config?.x_ves_rate || 0;
            if (!order || !rate) return;

            const dueUsd = order.getTotalDue ? order.getTotalDue() : 0;
            const dueBsStr = formatBs(dueUsd, rate, this.pos?.config?.x_secondary_currency_symbol || "Bs.");

            const payload = await makeAwaitable(this.dialog, NumberPopup, {
                title: "💵 Pago con Dólares en Efectivo ($)",
                subtitle: `Total a cobrar: $${dueUsd.toFixed(2)} (${dueBsStr}) — Ingrese el monto en $ recibido:`,
                startingValue: "",
            });

            if (payload !== undefined && payload !== null && payload !== "") {
                const valStr = typeof payload === "object" ? (payload.payload || payload.value) : payload;
                const usdVal = parseLocaleFloat(valStr);
                if (usdVal > 0) {
                    await this.applyUsdCashBill(usdVal);
                }
            }
        } catch (err) {
            console.error("[POS USD Cash Calc] Error:", err);
        }
    },

    onClearUsdBill() {
        const order = this.currentOrder;
        if (order) {
            order.x_usd_received = 0;
            order.x_usd_received_bs = 0;
            order.x_usd_charged = 0;
            order.x_usd_change_usd = 0;
            order.x_usd_change_bs = 0;
        }
        if (this.usdCalcState) {
            this.usdCalcState.usdReceived = 0;
            this.usdCalcState.usdCharged = 0;
            this.usdCalcState.changeUsd = 0;
            this.usdCalcState.changeBs = 0;
        }
    },

    /**
     * Intercepta la creación de una nueva línea de pago para fijar
     * el monto inicial en Bolívares (total restante en Bs).
     * Usamos el count antes/después para identificar la línea nueva.
     */
    async addNewPaymentLine(paymentMethod) {
        const order = this.currentOrder;
        const countBefore = (order?.payment_ids || []).length;

        const result = await super.addNewPaymentLine(...arguments);

        const pos = this.pos;
        const rate = pos?.config?.x_ves_rate;
        if (pos?.config?.x_enable_dual_currency && rate > 0 && order) {
            const lines = order.payment_ids || [];

            // Identificar la línea recién creada
            let newLine = null;
            if (lines.length > countBefore) {
                // Caso normal: se agregó al final
                newLine = lines[lines.length - 1];
            } else if (typeof order.get_selected_paymentline === "function") {
                newLine = order.get_selected_paymentline();
            } else if (order.selected_paymentline) {
                newLine = order.selected_paymentline;
            }

            if (newLine) {
                const totalBs  = orderTotalBs(order, rate);
                const paidBs   = sumPaidBs(order, newLine);
                const remainBs = Math.max(0, Math.round((totalBs - paidBs) * 100) / 100);

                // Guardar Bs directamente (sin dividir por tasa)
                if (typeof newLine.set_amount === "function") {
                    newLine.set_amount(remainBs);
                } else {
                    newLine.amount = remainBs;
                }
            }
        }
        return result;
    },

    /**
     * El cajero tipea Bolívares en el numpad.
     * Se guarda el valor TAL CUAL — sin dividir por tasa.
     * Así 5 → Bs. 5,00 y 5000 → Bs. 5.000,00 (sin error de redondeo).
     */
    updateSelectedPaymentline(amount = false) {
        const pos = this.pos;
        const rate = pos?.config?.x_ves_rate;
        if (pos?.config?.x_enable_dual_currency && rate > 0) {
            let inputBs = amount;
            if (inputBs === false) {
                const bufVal = this.numberBuffer.get();
                if (bufVal === null)   inputBs = null;
                else if (bufVal === "") inputBs = 0;
                else                   inputBs = this.numberBuffer.getFloat();
            }
            if (inputBs !== null && inputBs !== undefined) {
                // Pasamos el valor en Bs directamente — no hay conversión
                return super.updateSelectedPaymentline(inputBs);
            }
        }
        return super.updateSelectedPaymentline(...arguments);
    },
});

/**
 * Patch de PaymentScreenStatus:
 * Restante y Cambio calculados en Bs (totalBs - pagadoBs, o el vuelto calculado del billete en $).
 */
patch(PaymentScreenStatus.prototype, {
    get changeText() {
        const pos = this.env.services.pos;
        const rate = pos?.config?.x_ves_rate;
        if (pos?.config?.x_enable_dual_currency && rate > 0) {
            const order  = this.props.order;
            const symbol = pos.config.x_secondary_currency_symbol || "Bs.";
            const totalBs  = orderTotalBs(order, rate);
            const paidBs   = sumPaidBs(order, null);
            const usdChangeBs = order?.x_usd_change_bs || 0;
            const changeBs = Math.max(0, paidBs - totalBs, usdChangeBs);
            return `${symbol} ${changeBs.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
        return super.changeText;
    },

    get remainingText() {
        const pos = this.env.services.pos;
        const rate = pos?.config?.x_ves_rate;
        if (pos?.config?.x_enable_dual_currency && rate > 0) {
            const order    = this.props.order;
            const symbol   = pos.config.x_secondary_currency_symbol || "Bs.";
            const totalBs  = orderTotalBs(order, rate);
            const paidBs   = sumPaidBs(order, null);
            const remaining = Math.max(0, totalBs - paidBs);
            if (remaining < 0.005) return `${symbol} 0,00`;
            return `${symbol} ${remaining.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
        return super.remainingText;
    },
});

/**
 * Patch de PaymentScreenPaymentLines:
 * Los montos ya están en Bs — mostrar directo, sin multiplicar.
 */
patch(PaymentScreenPaymentLines.prototype, {
    formatPaymentLineAmount(line) {
        const pos  = this.pos;
        const rate = pos?.config?.x_ves_rate;
        if (pos?.config?.x_enable_dual_currency && rate > 0) {
            const symbol   = pos.config.x_secondary_currency_symbol || "Bs.";
            const amountBs = typeof line.get_amount === "function" ? line.get_amount() : (line.amount || 0);
            return `${symbol} ${amountBs.toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
        return this.env.utils.formatCurrency(line.get_amount());
    },
});

/**
 * Patch de PosOrder para imprimir la boleta / recibo exclusivamente en Bolívares
 */
patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);
        const rate = this.config.x_ves_rate;
        const printInBs = this.config.x_print_receipt_in_bs && rate > 0;
        const symbol = this.config.x_secondary_currency_symbol || "Bs.";

        result.ves_rate = rate;
        result.ves_rate_formatted = formatRate(rate);
        result.is_receipt_in_bs = printInBs;
        result.secondary_symbol = symbol;

        // Datos de monto recibido y vuelto exclusivamente en Bolívares para la boleta
        const usdReceived = this.x_usd_received || 0;
        const usdReceivedBs = this.x_usd_received_bs || Math.round(usdReceived * (rate || 1) * 100) / 100;
        const usdChangeBs = this.x_usd_change_bs || 0;
        result.has_usd_cash_calc = Boolean(usdReceived > 0);
        if (result.has_usd_cash_calc) {
            result.usd_received_bs_formatted = `${symbol} ${usdReceivedBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            result.usd_change_bs_formatted = `${symbol} ${usdChangeBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }

        if (printInBs) {
            // Conversión de Líneas de Pedido a Bolívares exactos
            if (result.orderlines) {
                result.orderlines = result.orderlines.map((l) => {
                    const lineCopy = { ...l };
                    if (typeof lineCopy.price === "number") {
                        lineCopy.price = `${symbol} ${(lineCopy.price * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                    } else if (typeof lineCopy.price === "string" && !lineCopy.price.includes(symbol)) {
                        const num = parseLocaleFloat(lineCopy.price);
                        if (num) {
                            lineCopy.price = `${symbol} ${(num * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                        }
                    }
                    if (typeof lineCopy.unitPrice === "number") {
                        lineCopy.unitPrice = `${symbol} ${(lineCopy.unitPrice * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                    } else if (typeof lineCopy.unitPrice === "string" && !lineCopy.unitPrice.includes(symbol)) {
                        const num = parseLocaleFloat(lineCopy.unitPrice);
                        if (num) {
                            lineCopy.unitPrice = `${symbol} ${(num * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                        }
                    }
                    return lineCopy;
                });
            }

            // Conversión de Totales y Subtotales a Bolívares
            if (result.taxTotals) {
                result.taxTotals = {
                    ...result.taxTotals,
                    order_total_formatted_bs: `${symbol} ${((result.taxTotals.order_sign || 1) * (result.taxTotals.order_total || 0) * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                };
                if (result.taxTotals.subtotals) {
                    result.taxTotals.subtotals = result.taxTotals.subtotals.map((st) => ({
                        ...st,
                        base_amount_bs: `${symbol} ${(st.base_amount_currency * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                        tax_amount_bs: `${symbol} ${(st.tax_amount_currency * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                    }));
                }
            }

            // Conversión de Líneas de Pago a Bolívares
            if (result.paymentlines) {
                result.paymentlines = result.paymentlines.map((p) => ({
                    ...p,
                    amount_bs: `${symbol} ${(p.amount * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                }));
            }

            // Conversión de Cambio / Vuelto a Bolívares
            if (usdChangeBs > 0) {
                result.order_change_bs = `${symbol} ${usdChangeBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                result.order_change = usdChangeBs;
            } else if (result.order_change) {
                result.order_change_bs = `${symbol} ${(result.order_change * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            }

            result.amount_total_bs = `${symbol} ${(result.amount_total * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
            result.label_total = "TOTAL (Bs.)";
        }

        // ======================================================================
        // BOLETA EXCLUSIVA RZ MARQUET (Formato r* ... z* SOLO lo de la imagen)
        // ======================================================================
        const companyName = (this.config.company_id && this.config.company_id.name) ||
                            (this.pos && this.pos.company && this.pos.company.name) || "";
        const isRz = Boolean(
            this.config.x_rz_receipt ||
            companyName.toUpperCase().includes("RZ")
        );
        result.is_rz_receipt = isRz;

        if (isRz) {
            const partner = this.get_partner ? this.get_partner() : null;
            result.rz_partner_name = partner ? (partner.name || "") : "";
            result.rz_partner_vat = partner ? (partner.vat || partner.identification_id || partner.x_cedula || "") : "";

            const rzRate = rate > 0 ? rate : 1.0;
            let rawLines = [];
            if (typeof this.get_orderlines === "function") {
                rawLines = this.get_orderlines();
            }
            if (!rawLines || !rawLines.length) {
                rawLines = result.orderlines || [];
            }

            result.rz_lines = rawLines.map((ol) => {
                let qty = 1;
                let name = "";
                let rawUnit = 0;
                let rawTotal = 0;

                if (typeof ol.get_quantity === "function") {
                    qty = ol.get_quantity();
                    const prod = ol.get_product ? ol.get_product() : null;
                    name = prod ? (prod.display_name || prod.name) : (ol.productName || "");
                    rawUnit = ol.get_unit_price ? ol.get_unit_price() : 0;
                    rawTotal = ol.get_price_with_tax ? ol.get_price_with_tax() : (ol.get_display_price ? ol.get_display_price() : rawUnit * qty);
                } else {
                    qty = ol.qty || 1;
                    name = ol.productName || ol.product_name || "";
                    rawUnit = typeof ol.unitPrice === "number" ? ol.unitPrice : (parseLocaleFloat(ol.unitPrice) || 0);
                    rawTotal = typeof ol.price === "number" ? ol.price : (parseLocaleFloat(ol.price) || (rawUnit * qty));
                }

                const qtyStr = `${Number.isInteger(qty) ? qty : qty.toFixed(2)}x`;
                const unitBs = rawUnit * rzRate;
                const totalBs = rawTotal * rzRate;
                const unitFormatted = unitBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                const totalFormatted = totalBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                const showUnitDetail = Math.abs(qty - 1) > 0.001;
                const qtyClean = Number.isInteger(qty) ? qty : qty.toFixed(2);
                const unitDetailStr = `(${qtyClean} x ${unitFormatted})`;

                return {
                    id: ol.id || Math.random(),
                    qty_str: qtyStr,
                    name: name,
                    price_unit_bs: unitFormatted,
                    price_subtotal_bs: totalFormatted,
                    show_unit_detail: showUnitDetail,
                    unit_detail_str: unitDetailStr,
                };
            });

            let rawOrderTotal = 0;
            if (typeof this.get_total_with_tax === "function") {
                rawOrderTotal = this.get_total_with_tax();
            } else {
                rawOrderTotal = typeof result.amount_total === "number" ? result.amount_total : (parseLocaleFloat(result.amount_total) || 0);
            }
            const totalBs = rawOrderTotal * rzRate;
            result.rz_total_bs = totalBs.toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        return result;
    },
});
