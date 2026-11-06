/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";

patch(PaymentScreen.prototype, {
    async addNewPaymentLine(paymentMethod) {
        const line = await super.addNewPaymentLine(...arguments);
        if (paymentMethod && paymentMethod.name) {
            const nameLower = paymentMethod.name.toLowerCase();
            if (nameLower.includes("movil") || nameLower.includes("móvil") || nameLower.includes("pago m") || nameLower.includes("pago móvil")) {
                const selectedLine = (line && typeof line === "object") ? line : (this.selectedPaymentLine || this.currentOrder?.get_selected_paymentline());
                if (selectedLine) {
                    await this.promptPagoMovilDetails(selectedLine);
                }
            }
        }
        return line;
    },

    async promptPagoMovilDetails(line) {
        try {
            const rate = this.pos?.config?.x_ves_rate || 0.0;
            const amountUSD = line.amount || this.currentOrder?.getTotalDue() || 0;
            const totalBsStr = rate > 0 
                ? `Bs. ${(amountUSD * rate).toLocaleString('es-VE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` 
                : `$ ${amountUSD.toFixed(2)}`;

            const bankList = [
                { id: 'BDV (0102)', label: 'Banco de Venezuela (0102)', item: 'BDV (0102)' },
                { id: 'Banesco (0134)', label: 'Banesco (0134)', item: 'Banesco (0134)' },
                { id: 'Mercantil (0105)', label: 'Banco Mercantil (0105)', item: 'Mercantil (0105)' },
                { id: 'Provincial (0108)', label: 'Banco Provincial (0108)', item: 'Provincial (0108)' },
                { id: 'BNC (0191)', label: 'BNC Banco Nacional de Crédito (0191)', item: 'BNC (0191)' },
                { id: 'Bancamiga (0172)', label: 'Bancamiga (0172)', item: 'Bancamiga (0172)' },
                { id: 'Bancaribe (0114)', label: 'Bancaribe (0114)', item: 'Bancaribe (0114)' },
                { id: 'Exterior (0115)', label: 'Banco Exterior (0115)', item: 'Exterior (0115)' },
                { id: 'Banplus (0174)', label: 'Banplus (0174)', item: 'Banplus (0174)' },
                { id: 'Plaza (0138)', label: 'Banco Plaza (0138)', item: 'Plaza (0138)' },
                { id: 'BFC (0151)', label: 'Banco Fondo Común (0151)', item: 'BFC (0151)' },
                { id: 'Bicentenario (0175)', label: 'Banco Bicentenario (0175)', item: 'Bicentenario (0175)' },
                { id: 'BANFANB (0177)', label: 'BANFANB (0177)', item: 'BANFANB (0177)' },
                { id: 'Sofitasa (0137)', label: 'Banco Sofitasa (0137)', item: 'Sofitasa (0137)' },
                { id: 'Otro Banco', label: 'Otro Banco', item: 'Otro Banco' },
            ];

            // 1. Solicitar Banco de Origen
            const selectedBank = await makeAwaitable(this.dialog, SelectionPopup, {
                title: `📱 Pago Móvil — Monto: ${totalBsStr}`,
                subtitle: "Seleccione el Banco Emisor:",
                list: bankList,
            });

            if (!selectedBank) return;

            // 2. Solicitar Número de Referencia
            const refNum = await makeAwaitable(this.dialog, NumberPopup, {
                title: `📱 Referencia de Pago Móvil`,
                subtitle: `Banco: ${selectedBank} | Monto: ${totalBsStr}`,
                startingValue: "",
            });

            if (refNum) {
                const info = `Pago Móvil - Ref: ${refNum} (${selectedBank}) [${totalBsStr}]`;
                if (typeof line.update === "function") {
                    line.update({ ticket: info, payment_ref: info });
                } else {
                    line.ticket = info;
                    line.payment_ref = info;
                }
            }
        } catch (e) {
            console.error("Error al registrar datos de Pago Móvil en POS:", e);
        }
    }
});
