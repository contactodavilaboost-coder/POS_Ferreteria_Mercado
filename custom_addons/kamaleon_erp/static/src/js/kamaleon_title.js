/** @odoo-module **/

import { registry } from "@web/core/registry";
import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";

/* Configurar título del navegador */
export const kamaleonTitleService = {
    dependencies: ["title"],
    start(env, { title }) {
        title.setParts({ z_title: "Ferretería Mercado" });
    },
};

registry.category("services").add("kamaleon_title", kamaleonTitleService, { force: true });

/* Abrir la cuadrícula de tarjetas de módulos automáticamente al iniciar sesión o ir al inicio */
patch(WebClient.prototype, {
    async _loadDefaultApp() {
        // Abrir el menú principal de tarjetas (App Switcher) por defecto
        this.env.bus.trigger("APPS_MENU:STATE_CHANGED", true);
    },
});
