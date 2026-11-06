/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { onMounted, onWillUnmount } from "@odoo/owl";

/**
 * Detecta si el usuario está enfocado en un campo de texto / input para no interferir
 */
function isEditableElement(target) {
    const el = target || document.activeElement;
    if (!el) return false;
    const tag = (el.tagName || "").toUpperCase();
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
        return true;
    }
    if (el.isContentEditable) {
        return true;
    }
    return false;
}

/**
 * Muestra u oculta la ventana flotante de ayuda de atajos de teclado
 */
export function toggleShortcutsModal() {
    let modal = document.getElementById("kamaleon-pos-shortcuts-modal");
    if (!modal) {
        modal = createShortcutsModalElement();
        document.body.appendChild(modal);
    }
    const isVisible = modal.style.display !== "none";
    modal.style.display = isVisible ? "none" : "flex";
}

/**
 * Crea el elemento DOM del modal de atajos con estética Glassmorphism Emerald
 */
function createShortcutsModalElement() {
    const modal = document.createElement("div");
    modal.id = "kamaleon-pos-shortcuts-modal";
    modal.style.cssText = `
        position: fixed;
        inset: 0;
        background: rgba(4, 10, 24, 0.78);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        z-index: 99999;
        display: none;
        align-items: center;
        justify-content: center;
        padding: 20px;
        animation: fadeIn 0.2s ease-out;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    `;

    modal.innerHTML = `
        <div style="
            background: #0B132B;
            border: 1px solid rgba(16, 185, 129, 0.35);
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7), 0 0 30px rgba(16, 185, 129, 0.15);
            border-radius: 18px;
            max-width: 760px;
            width: 100%;
            overflow: hidden;
            color: #F8FAFC;
        ">
            <!-- Header -->
            <div style="
                background: linear-gradient(135deg, rgba(6, 78, 59, 0.6) 0%, rgba(15, 23, 42, 0.9) 100%);
                padding: 18px 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-bottom: 1px solid rgba(16, 185, 129, 0.25);
            ">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 26px;">⌨️</span>
                    <div>
                        <h3 style="margin: 0; font-size: 20px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.01em;">
                            Atajos de Teclado del Punto de Venta
                        </h3>
                        <p style="margin: 2px 0 0 0; font-size: 13px; color: #34D399; font-weight: 500;">
                            Control total sin tocar el ratón / mouse
                        </p>
                    </div>
                </div>
                <button id="kamaleon-close-shortcuts-btn" style="
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    color: #CBD5E1;
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                    font-weight: bold;
                    transition: all 0.2s;
                ">&times;</button>
            </div>

            <!-- Body -->
            <div style="padding: 24px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; max-height: 75vh; overflow-y: auto;">
                
                <!-- Columna 1: Carrito y Ventas -->
                <div style="background: rgba(15, 23, 42, 0.6); padding: 16px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.07);">
                    <div style="font-size: 13px; font-weight: 800; color: #10B981; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                        <span>🛒</span> Carrito &amp; Búsqueda
                    </div>
                    
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Buscar producto</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #38BDF8; font-family: monospace;">F2</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #38BDF8;">Navegar productos</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #38BDF8; font-family: monospace;">← ↑ ↓ →</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #34D399;">Agregar al carrito</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #34D399; font-family: monospace;">Enter</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Seleccionar Cliente</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #38BDF8; font-family: monospace;">F3</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Ir a Cobrar / Pagar</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #34D399; font-family: monospace;">F4</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #FCA5A5;">Cancelar / Vaciar Orden</span>
                            <kbd style="background: #450A0A; border: 1px solid #EF4444; border-bottom: 2px solid #B91C1C; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #FCA5A5; font-family: monospace;">F6</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #6EE7B7;">🍈 Verduras Surtidas (Bs.)</span>
                            <kbd style="background: #064E3B; border: 1px solid #10B981; border-bottom: 2px solid #047857; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #6EE7B7; font-family: monospace;">F7</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Cantidad (+ / -)</span>
                            <div style="display: flex; gap: 4px;">
                                <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #E2E8F0; font-family: monospace;">+</kbd>
                                <span style="color: #64748B;">/</span>
                                <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #E2E8F0; font-family: monospace;">-</kbd>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Eliminar producto</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #F87171; font-family: monospace;">Supr / Del</kbd>
                        </div>
                    </div>
                </div>

                <!-- Columna 2: Pagos y Caja -->
                <div style="background: rgba(15, 23, 42, 0.6); padding: 16px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.07);">
                    <div style="font-size: 13px; font-weight: 800; color: #38BDF8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                        <span>💳</span> Pantalla de Pagos
                    </div>
                    
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Efectivo</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #FBBF24; font-family: monospace;">E</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #34D399;">💵 Billete $ (Vuelto Bs.)</span>
                            <kbd style="background: #064E3B; border: 1px solid #10B981; border-bottom: 2px solid #047857; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #6EE7B7; font-family: monospace;">D</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Tarjeta / Punto</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #FBBF24; font-family: monospace;">T</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Pago Móvil</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #FBBF24; font-family: monospace;">M</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Zelle / Banco</span>
                            <div style="display: flex; gap: 4px;">
                                <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #FBBF24; font-family: monospace;">Z</kbd>
                                <span style="color: #64748B;">/</span>
                                <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #FBBF24; font-family: monospace;">B</kbd>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Validar &amp; Facturar</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #34D399; font-family: monospace;">F8</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #C4B5FD;">🖨️ Imprimir Boleta</span>
                            <kbd style="background: #2E1065; border: 1px solid #8B5CF6; border-bottom: 2px solid #7C3AED; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #DDD6FE; font-family: monospace;">F10 / P</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Siguiente Venta / Orden</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #38BDF8; font-family: monospace;">F9</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Volver al Carrito</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #CBD5E1; font-family: monospace;">Esc</kbd>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13.5px; color: #E2E8F0;">Ver esta Guía de Atajos</span>
                            <kbd style="background: #1E293B; border: 1px solid #475569; border-bottom: 2px solid #334155; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #10B981; font-family: monospace;">F1</kbd>
                        </div>
                    </div>
                </div>

            </div>

            <!-- Footer -->
            <div style="
                background: rgba(15, 23, 42, 0.85);
                padding: 12px 24px;
                border-top: 1px solid rgba(255, 255, 255, 0.08);
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-size: 12px;
                color: #94A3B8;
            ">
                <span>💡 Tip: Presiona <kbd style="background: #334155; padding: 2px 6px; border-radius: 4px; color: #F1F5F9;">Esc</kbd> en cualquier momento para cerrar esta ventana o cancelar popups.</span>
                <span style="color: #10B981; font-weight: 600;">Zais Express C.A — POS Rápido</span>
            </div>
        </div>
    `;

    // Evento de cierre en la X y al hacer click en el fondo
    const closeBtn = modal.querySelector("#kamaleon-close-shortcuts-btn");
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            modal.style.display = "none";
        });
    }
    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.style.display = "none";
        }
    });

    return modal;
}

/**
 * Agrega una marca de agua estilizada como atajo de teclado a un elemento del DOM
 */
function addWatermarkBadge(element, keyText, colorClass, position = "top-right") {
    if (!element) return;

    // Verificar si ya tiene este watermark para evitar duplicados
    const existing = element.querySelector(`.kamaleon-shortcut-watermark[data-key='${keyText}']`);
    if (existing) return;

    // Asegurar posicionamiento relativo en el contenedor
    try {
        const style = window.getComputedStyle(element);
        if (style.position === "static" || !style.position) {
            element.style.position = "relative";
        }
    } catch (e) {
        element.style.position = "relative";
    }

    const badge = document.createElement("span");
    badge.className = `kamaleon-shortcut-watermark ${colorClass} pos-${position}`;
    badge.setAttribute("data-key", keyText);
    badge.textContent = keyText;

    element.appendChild(badge);
}

/**
 * Escanea la interfaz activa del POS e inyecta las marcas de agua de los atajos en cada botón
 */
export function applyPosShortcutWatermarks() {
    // 1. Botón Pagar (F4)
    const payBtns = document.querySelectorAll(".pay-order-button, .button.pay, .btn-pay, .pay-button, .actionpad .pay");
    payBtns.forEach(btn => {
        addWatermarkBadge(btn, "F4", "kamaleon-watermark-emerald", "top-right");
    });

    // 2. Buscador de productos (F2)
    const searchBars = document.querySelectorAll(".pos-search-bar, .search-box, .search-bar-portal");
    searchBars.forEach(sb => {
        addWatermarkBadge(sb, "F2", "kamaleon-watermark-blue", "inside-search");
    });

    // 3. Botón de Selección de Cliente (F3)
    const customerBtns = document.querySelectorAll(".set-partner, button.partner-button, .partner-icon, .btn-customer, button[title*='Cliente']");
    customerBtns.forEach(btn => {
        addWatermarkBadge(btn, "F3", "kamaleon-watermark-blue", "top-right");
    });

    // 4. Cancelar Orden (F6)
    const cancelBtns = document.querySelectorAll(".order-selector .selected .delete-order, .order-button.selected .close-order, .order-button.selected .delete, button.delete-order");
    cancelBtns.forEach(btn => {
        addWatermarkBadge(btn, "F6", "kamaleon-watermark-red", "top-right");
    });
    const activeOrderTab = document.querySelector(".order-button.selected, .order-selector .selected");
    if (activeOrderTab && !cancelBtns.length) {
        addWatermarkBadge(activeOrderTab, "F6", "kamaleon-watermark-red", "top-right");
    }

    // 5. Tarjeta de "Verduras Surtidas" (F7)
    const productCards = document.querySelectorAll("article.product-card, .product-card, .product");
    productCards.forEach(card => {
        const text = (card.textContent || "").toUpperCase();
        if ((text.includes("VERDURA") && text.includes("SURTID")) || text.includes("SURTID") || text.includes("MIX VERDURA")) {
            addWatermarkBadge(card, "🍈 F7", "kamaleon-watermark-emerald", "bottom-right");
        }
    });

    // 6. Métodos de Pago en Pantalla de Pago (E, T, M, Z, B)
    const paymentMethods = document.querySelectorAll(".paymentmethods .paymentmethod, .payment-methods .button, .payment-method, .payment-buttons .btn");
    paymentMethods.forEach(btn => {
        const text = (btn.textContent || "").toLowerCase();
        if (text.includes("efectivo") || text.includes("cash")) {
            addWatermarkBadge(btn, "E", "kamaleon-watermark-amber", "top-right");
        } else if (text.includes("tarjeta") || text.includes("punto") || text.includes("debito") || text.includes("débito") || text.includes("crédito") || text.includes("card")) {
            addWatermarkBadge(btn, "T", "kamaleon-watermark-amber", "top-right");
        } else if (text.includes("movil") || text.includes("móvil") || text.includes("pm")) {
            addWatermarkBadge(btn, "M", "kamaleon-watermark-amber", "top-right");
        } else if (text.includes("zelle")) {
            addWatermarkBadge(btn, "Z", "kamaleon-watermark-amber", "top-right");
        } else if (text.includes("banco") || text.includes("transferencia") || text.includes("transf") || text.includes("bank")) {
            addWatermarkBadge(btn, "B", "kamaleon-watermark-amber", "top-right");
        }
    });

    // 7. Botón Validar Pago (F8)
    const validateBtns = document.querySelectorAll(".payment-screen .button.next, .validate-order-button, .button.validate, .btn-validate");
    validateBtns.forEach(btn => {
        addWatermarkBadge(btn, "F8", "kamaleon-watermark-emerald", "top-right");
    });

    // 8. Botón Imprimir Boleta (F10)
    const printBtns = document.querySelectorAll(".receipt-screen .button.print, .pos-receipt-container button.print, button.print-receipt, .btn-print, .receipt-screen button[title*='Imprimir']");
    printBtns.forEach(btn => {
        addWatermarkBadge(btn, "F10", "kamaleon-watermark-purple", "top-right");
    });

    // 9. Botón Siguiente Orden (F9)
    const nextBtns = document.querySelectorAll(".receipt-screen .button.next, .next-order-button, button.order-done, .btn-next-order");
    nextBtns.forEach(btn => {
        addWatermarkBadge(btn, "F9", "kamaleon-watermark-blue", "top-right");
    });

    // 10. Botón Volver / Atrás (Esc)
    const backBtns = document.querySelectorAll(".payment-screen .button.back, .partnerlist-screen .button.back, .receipt-screen .button.back, .back-button");
    backBtns.forEach(btn => {
        addWatermarkBadge(btn, "Esc", "kamaleon-watermark-gray", "top-left");
    });
}

let watermarkInterval = null;
let watermarkObserver = null;

export function initShortcutWatermarks() {
    applyPosShortcutWatermarks();

    if (!watermarkInterval) {
        watermarkInterval = setInterval(() => {
            applyPosShortcutWatermarks();
        }, 500);
    }

    if (!watermarkObserver && typeof MutationObserver !== "undefined") {
        const root = document.querySelector(".pos, #pos-root, body") || document.body;
        if (root) {
            watermarkObserver = new MutationObserver(() => {
                applyPosShortcutWatermarks();
            });
            watermarkObserver.observe(root, { childList: true, subtree: true });
        }
    }
}

export function stopShortcutWatermarks() {
    if (watermarkInterval) {
        clearInterval(watermarkInterval);
        watermarkInterval = null;
    }
    if (watermarkObserver) {
        watermarkObserver.disconnect();
        watermarkObserver = null;
    }
}

// Iniciar proactivamente
if (typeof window !== "undefined") {
    setTimeout(initShortcutWatermarks, 600);

    // Evitar que el foco de flechas del teclado se cruce con clics directos del mouse o táctil
    if (!window.__kamaleon_product_click_listener_set) {
        window.__kamaleon_product_click_listener_set = true;
        document.addEventListener("pointerdown", (e) => {
            if (e.target && e.target.closest && e.target.closest(".product-card, .product, article.product-card")) {
                document.querySelectorAll(".kamaleon-pos-product-focused").forEach(c => {
                    c.classList.remove("kamaleon-pos-product-focused");
                    c.style.transform = "";
                });
            }
        }, true);
    }
}

/**
 * Patch del Navbar para registrar el Listener Global de Teclado del POS
 */
let navbarInstance = null;
let lastDeleteTimestamp = 0;

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);
        navbarInstance = this;

        this._onPosKeyDown = this.handlePosKeyboardShortcuts.bind(this);
        window.addEventListener("keydown", this._onPosKeyDown, true);

        initShortcutWatermarks();

        onWillUnmount(() => {
            window.removeEventListener("keydown", this._onPosKeyDown, true);
            stopShortcutWatermarks();
            if (navbarInstance === this) {
                navbarInstance = null;
            }
        });
    },

    toggleShortcutsGuide() {
        toggleShortcutsModal();
    },

    handlePosKeyboardShortcuts(event) {
        const key = event.key;
        const code = event.code;
        const isEditing = isEditableElement(event.target);
        const modal = document.getElementById("kamaleon-pos-shortcuts-modal");
        const isShortcutsModalOpen = modal && modal.style.display !== "none";

        // Protección contra auto-repetición de teclas (tecla sostenida accidentalmente)
        if (event.repeat) {
            if (["Delete", "F4", "F6", "F7", "F8", "F9", "F10", "Enter", " "].includes(key) ||
                ["e", "t", "m", "z", "b", "d"].includes((key || "").toLowerCase())) {
                event.preventDefault();
                event.stopPropagation();
                return;
            }
        }

        // ==========================================================
        // 1. F1: Mostrar / Ocultar Guía de Atajos de Teclado
        // ==========================================================
        if (key === "F1" || (event.altKey && (key === "h" || key === "H"))) {
            event.preventDefault();
            event.stopPropagation();
            toggleShortcutsModal();
            return;
        }

        // Si el modal de atajos está abierto, Escape lo cierra de inmediato
        if (isShortcutsModalOpen) {
            if (key === "Escape") {
                event.preventDefault();
                event.stopPropagation();
                modal.style.display = "none";
                return;
            }
        }

        // ==========================================================
        // 2. Escape: Cerrar popups, cancelar búsqueda o volver atrás
        // ==========================================================
        if (key === "Escape") {
            // Si hay un popup/dialog de Odoo abierto, cerrarlo
            const closeBtn = document.querySelector(".modal .btn-close, .modal button.cancel, .dialog-cancel, .popup .button.cancel");
            if (closeBtn) {
                event.preventDefault();
                event.stopPropagation();
                closeBtn.click();
                return;
            }

            // Si está escribiendo en el buscador, limpiar y desenfocar
            if (isEditing) {
                event.target.blur();
                return;
            }

            // Si está en la pantalla de pago o de cliente, volver al carrito
            const backBtn = document.querySelector(".payment-screen .button.back, .partnerlist-screen .button.back, button.back, .back-button");
            if (backBtn) {
                event.preventDefault();
                event.stopPropagation();
                backBtn.click();
                return;
            }
            return;
        }

        // ==========================================================
        // 3. F2: Enfocar Búsqueda de Productos
        // ==========================================================
        if (key === "F2") {
            event.preventDefault();
            event.stopPropagation();
            const searchInput = document.querySelector(".pos-search-bar input, .search-box input, input.search, input[placeholder*='Buscar'], input[placeholder*='Search']");
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
            return;
        }

        // ==========================================================
        // 4. F3: Seleccionar / Cambiar Cliente
        // ==========================================================
        if (key === "F3") {
            event.preventDefault();
            event.stopPropagation();
            const customerBtn = document.querySelector(".set-partner, button.partner-button, .partner-icon, .btn-customer, button[title*='Cliente']");
            if (customerBtn) {
                customerBtn.click();
            } else if (this.pos && typeof this.pos.showScreen === "function") {
                this.pos.showScreen("PartnerListScreen");
            }
            return;
        }

        // ==========================================================
        // 5. F6: Cancelar / Eliminar Orden Actual
        // ==========================================================
        if (key === "F6") {
            event.preventDefault();
            event.stopPropagation();
            this._triggerCancelOrder();
            return;
        }

        // ==========================================================
        // 6. F7: Producto Rápido "Verduras Surtidas" (Monto Abierto en Bs)
        // ==========================================================
        if (key === "F7") {
            event.preventDefault();
            event.stopPropagation();
            this._triggerVerdurasSurtidas();
            return;
        }

        // ==========================================================
        // 6. F4: Ir a la Pantalla de Pago (Cobrar)
        // ==========================================================
        if (key === "F4") {
            event.preventDefault();
            event.stopPropagation();
            this._triggerGoToPayment();
            return;
        }

        // ==========================================================
        // 7. F8: Validar Pago en PaymentScreen
        // ==========================================================
        if (key === "F8") {
            event.preventDefault();
            event.stopPropagation();
            this._triggerValidatePayment();
            return;
        }

        // ==========================================================
        // 8. F9: Siguiente Orden (ReceiptScreen o Nueva Orden)
        // ==========================================================
        if (key === "F9") {
            event.preventDefault();
            event.stopPropagation();
            this._triggerNextOrder();
            return;
        }

        // ==========================================================
        // 9. F10: Imprimir Boleta / Recibo
        // ==========================================================
        if (key === "F10") {
            event.preventDefault();
            event.stopPropagation();
            this._triggerPrintReceipt();
            return;
        }

        // ==========================================================
        // SI EL USUARIO ESTÁ ESCRIBIENDO EN UN INPUT
        // ==========================================================
        if (isEditing) {
            // Manejo ergonómico del buscador de productos del POS:
            const isSearchBar = event.target.matches?.(".pos-search-bar input, .search-box input, input.search, input[placeholder*='Buscar'], input[placeholder*='Search']");
            if (isSearchBar) {
                // Flecha Abajo en el buscador -> pasar el control al grid de productos
                if (key === "ArrowDown") {
                    event.preventDefault();
                    event.target.blur();
                    this._navigateProductGrid("ArrowDown");
                    return;
                }
                // Enter en el buscador -> agregar el primer producto encontrado SOLO si hay al menos 4 caracteres
                // (y si es código numérico, al menos 5 dígitos para evitar meter 7up por el prefijo nacional 759)
                if (key === "Enter") {
                    const searchVal = (event.target.value || "").trim();
                    const isNumeric = /^\d+$/.test(searchVal);
                    const minLength = isNumeric ? 5 : 4;

                    if (searchVal.length >= minLength) {
                        const firstCard = document.querySelector(".product-list article.product-card, .products-widget article.product-card, article.product-card, .product-list .product");
                        if (firstCard) {
                            event.preventDefault();
                            event.target.blur();
                            firstCard.click();
                            return;
                        }
                    } else {
                        // Si tiene menos de 4 caracteres (o es solo el prefijo 759), solo desenfocar sin meter nada accidental
                        event.target.blur();
                        return;
                    }
                }
            }
            return;
        }

        // ==========================================================
        // 10. Atajos contextuales cuando NO se está escribiendo texto
        // ==========================================================

        // A) En la pantalla de Recibo (ReceiptScreen):
        // Validación estricta: NO usar selectores estáticos que persisten en el DOM tras salir
        const isReceiptScreen = (this.pos?.mainScreen?.name === "ReceiptScreen") ||
            (Boolean(document.querySelector(".pos .receipt-screen:not(.d-none), .receipt-screen:not([style*='display: none'])")) &&
             !document.querySelector(".product-screen, .pos-content .product-screen"));

        if (isReceiptScreen) {
            // Solo Ctrl+P o 'P' dispara impresión aquí. NUNCA Enter para no interferir con siguiente orden ni foco
            if ((event.ctrlKey && key.toLowerCase() === "p") || key.toLowerCase() === "p") {
                event.preventDefault();
                event.stopPropagation();
                this._triggerPrintReceipt();
                return;
            }
        }

        // B) En la pantalla de Pago (PaymentScreen):
        const isPaymentScreen = Boolean(document.querySelector(".payment-screen"));
        if (isPaymentScreen) {
            const letter = (key || "").toLowerCase();

            // Tecla 'D': Pago con Billete en Dólares ($) -> Calcular Vuelto en Bs.
            if (letter === "d" && !event.ctrlKey && !event.altKey) {
                event.preventDefault();
                event.stopPropagation();
                if (typeof event.stopImmediatePropagation === "function") {
                    event.stopImmediatePropagation();
                }
                if (window.__kamaleon_pos && typeof window.__kamaleon_pos.promptCustomUsdBill === "function") {
                    window.__kamaleon_pos.promptCustomUsdBill();
                } else {
                    const usdBtn = document.getElementById("kamaleon-pos-custom-usd-btn");
                    if (usdBtn) usdBtn.click();
                }
                return;
            }

            const validPaymentLetters = ["e", "t", "m", "z", "b"];

            // Teclas de letras para seleccionar métodos de pago (E: Efectivo, T: Tarjeta, M: Pago Móvil, Z: Zelle, B: Banco)
            if (validPaymentLetters.includes(letter) && !event.ctrlKey && !event.altKey) {
                const targetMethodBtn = this._findPaymentMethodButton(letter);
                if (targetMethodBtn) {
                    event.preventDefault();
                    event.stopPropagation();
                    if (typeof event.stopImmediatePropagation === "function") {
                        event.stopImmediatePropagation();
                    }
                    targetMethodBtn.click();
                    return;
                }
            }
        }

        // C) En la pantalla de Carrito / Productos (ProductScreen):
        const isProductScreen = (this.pos?.mainScreen?.name === "ProductScreen") || (!isPaymentScreen && !isReceiptScreen);
        if (isProductScreen) {
            // Flechas del teclado (← ↑ ↓ →): Navegar por los cuadritos del grid de productos
            if (key === "ArrowRight" || key === "ArrowLeft" || key === "ArrowDown" || key === "ArrowUp") {
                event.preventDefault();
                event.stopPropagation();
                this._navigateProductGrid(key);
                return;
            }

            // Enter: Seleccionar y agregar el producto resaltado con flechas al carrito
            if (key === "Enter") {
                if (this._selectFocusedProduct()) {
                    event.preventDefault();
                    event.stopPropagation();
                    return;
                }
            }

            // Tecla 'C' -> Cambiar cliente
            if (key.toLowerCase() === "c") {
                event.preventDefault();
                event.stopPropagation();
                const customerBtn = document.querySelector(".set-partner, button.partner-button, .partner-icon, .btn-customer");
                if (customerBtn) customerBtn.click();
                return;
            }

            // '+' o NumpadAdd: Incrementar cantidad de la línea seleccionada en el carrito
            if (key === "+" || code === "NumpadAdd") {
                event.preventDefault();
                event.stopPropagation();
                this._adjustSelectedLineQty(1);
                return;
            }

            // '-' o NumpadSubtract: Disminuir cantidad de la línea seleccionada en el carrito
            if (key === "-" || code === "NumpadSubtract") {
                event.preventDefault();
                event.stopPropagation();
                this._adjustSelectedLineQty(-1);
                return;
            }

            // 'Delete' / 'Supr': Eliminar únicamente la línea seleccionada con protección estricta
            // NOTA: 'Backspace' se deja nativo para Odoo POS para que reduzca la cantidad o pase a 0
            // exactamente igual a presionar el botón ⌫ de la pantalla, sin afectar productos adyacentes.
            if (key === "Delete") {
                const now = Date.now();
                if (now - lastDeleteTimestamp < 600) {
                    event.preventDefault();
                    event.stopPropagation();
                    return;
                }
                lastDeleteTimestamp = now;

                event.preventDefault();
                event.stopPropagation();
                if (typeof event.stopImmediatePropagation === "function") {
                    event.stopImmediatePropagation();
                }
                this._removeSelectedLine();
                return;
            }
        }
    },

    /**
     * Navega a la pantalla de Pago
     */
    _triggerGoToPayment() {
        const order = this.pos?.get_order();
        const lines = order?.get_orderlines ? order.get_orderlines() : (order?.lines || []);
        if (!lines || lines.length === 0) {
            if (this.notification) {
                this.notification.add("Agregue al menos un producto al pedido antes de pagar.", { type: "warning" });
            }
            return;
        }

        const payBtn = document.querySelector(".pay-order-button, .button.pay, .btn-pay, .pay-button");
        if (payBtn) {
            payBtn.click();
        } else if (this.pos && typeof this.pos.showScreen === "function") {
            this.pos.showScreen("PaymentScreen");
        }
    },

    /**
     * Busca el botón del método de pago correspondiente según su inicial (E, T, M, Z, B)
     */
    _findPaymentMethodButton(letter) {
        const paymentMethods = Array.from(document.querySelectorAll(".paymentmethods .paymentmethod, .payment-methods .button, .payment-method, .payment-buttons .btn"));
        if (!paymentMethods.length) return null;

        let keywords = [];
        if (letter === "e") keywords = ["efectivo", "cash"];
        else if (letter === "t") keywords = ["tarjeta", "punto", "debito", "débito", "credito", "crédito", "card"];
        else if (letter === "m") keywords = ["movil", "móvil", "pago movil", "pago móvil", "pm"];
        else if (letter === "z") keywords = ["zelle"];
        else if (letter === "b") keywords = ["banco", "transferencia", "transf", "bank"];

        // 1. Coincidencia por palabra clave
        for (const btn of paymentMethods) {
            const text = (btn.textContent || "").toLowerCase();
            if (keywords.some(kw => text.includes(kw))) {
                return btn;
            }
        }

        // 2. Coincidencia por primera letra
        for (const btn of paymentMethods) {
            const text = (btn.textContent || "").trim().toLowerCase();
            if (text.startsWith(letter)) {
                return btn;
            }
        }

        return null;
    },

    /**
     * Valida el pago en PaymentScreen
     */
    _triggerValidatePayment() {
        const validateBtn = document.querySelector(".payment-screen .button.next.highlight, .validate-order-button, .button.validate, button[title*='Validar'], .btn-validate");
        if (validateBtn) {
            validateBtn.click();
        }
    },

    /**
     * Pasa a la siguiente orden
     */
    _triggerNextOrder() {
        const nextBtn = document.querySelector(".receipt-screen .button.next, .next-order-button, button.order-done, .btn-next-order, button.button.next");
        if (nextBtn) {
            nextBtn.click();
            nextBtn.blur();
        } else if (this.pos && typeof this.pos.add_new_order === "function") {
            this.pos.add_new_order();
        }

        if (document.activeElement && typeof document.activeElement.blur === "function") {
            document.activeElement.blur();
        }

        // Limpiar cualquier foco residual en tarjetas de productos para evitar productos fantasma
        document.querySelectorAll(".kamaleon-pos-product-focused").forEach(c => {
            c.classList.remove("kamaleon-pos-product-focused");
            c.style.transform = "";
        });
    },

    /**
     * Ajusta la cantidad de la línea seleccionada (+1 / -1)
     * 
     * IMPORTANTE: NO usar line.set_quantity() directamente en Odoo 18 POS porque
     * dispara el numberBuffer interno que luego sobreescribe el valor a 0.
     * La forma correcta es usar los botones nativos del POS o manipular el
     * numberBuffer de forma apropiada.
     */
    _adjustSelectedLineQty(delta) {
        const order = this.pos?.get_order();
        if (!order) return;
        const line = order.get_selected_orderline ? order.get_selected_orderline() : null;
        if (!line) return;

        // Obtener la cantidad actual
        const currentQty = typeof line.get_quantity === "function" ? line.get_quantity() : (line.qty || 1);
        const newQty = currentQty + delta;

        if (newQty <= 0) {
            this._removeSelectedLine();
            return;
        }

        // ESTRATEGIA: Buscar y hacer click en el botón nativo +/- del POS
        // Esto respeta el flujo interno de Odoo sin interferir con el numberBuffer
        if (delta > 0) {
            const plusBtn = document.querySelector(
                ".product-screen .numpad .button[data-action='increment'], " +
                ".numpad-button.increment, " +
                ".order-line .add-unit, " +
                "button[title*='Agregar'], button[title*='Incrementar']"
            );
            if (plusBtn) {
                plusBtn.click();
                return;
            }
        } else {
            const minusBtn = document.querySelector(
                ".product-screen .numpad .button[data-action='decrement'], " +
                ".numpad-button.decrement, " +
                ".order-line .remove-unit, " +
                "button[title*='Reducir'], button[title*='Disminuir']"
            );
            if (minusBtn) {
                minusBtn.click();
                return;
            }
        }

        // Ajuste directo y limpio de la cantidad en la línea del pedido
        try {
            if (typeof line.set_quantity === "function") {
                line.set_quantity(String(newQty));
            } else if (typeof line.setQuantity === "function") {
                line.setQuantity(String(newQty));
            } else {
                line.qty = newQty;
            }
        } catch (e) {
            console.warn("[POS Shortcuts] Error ajustando cantidad:", e);
        }
    },

    /**
     * Elimina la línea seleccionada del carrito
     */
    _removeSelectedLine() {
        const order = this.pos?.get_order();
        if (!order) return;
        const line = order.get_selected_orderline ? order.get_selected_orderline() : null;
        if (!line) return;

        if (typeof order.removeOrderline === "function") {
            order.removeOrderline(line);
        } else if (typeof order.remove_orderline === "function") {
            order.remove_orderline(line);
        } else if (typeof line.set_quantity === "function") {
            line.set_quantity(0);
        }
    },

    /**
     * Cancela y vacía o elimina la orden actual (Atajo F6)
     */
    async _triggerCancelOrder() {
        const order = this.pos?.get_order();
        if (!order) {
            if (this.notification) {
                this.notification.add("No hay ninguna orden activa para cancelar.", { type: "info" });
            }
            return;
        }

        const lines = order.get_orderlines ? order.get_orderlines() : (order.lines || []);
        const hasLines = lines && lines.length > 0;

        // Si la orden ya está vacía
        if (!hasLines) {
            if (this.notification) {
                this.notification.add("El pedido actual ya está vacío.", { type: "info" });
            }
            return;
        }

        // Buscar botón de eliminar nativo del POS primero
        const nativeDeleteBtn = document.querySelector(
            ".order-selector .selected .delete-order, " +
            ".order-button.selected .close-order, " +
            ".order-button.selected .delete, " +
            ".order-button.selected button[aria-label*='Delete'], " +
            ".order-button.selected button[title*='Eliminar'], " +
            ".ticket-screen .discard-button, " +
            "button.delete-order"
        );

        if (nativeDeleteBtn) {
            nativeDeleteBtn.click();
            return;
        }

        // Confirmación para evitar borrados accidentales de pedidos cargados
        const confirmed = window.confirm("¿Está seguro de que desea CANCELAR y vaciar la orden actual?");
        if (!confirmed) return;

        try {
            if (typeof this.pos.removeOrder === "function") {
                this.pos.removeOrder(order);
            } else if (typeof this.pos.remove_order === "function") {
                this.pos.remove_order(order);
            } else {
                // Remover todas las líneas una a una
                const linesCopy = [...lines];
                for (const l of linesCopy) {
                    if (typeof order.removeOrderline === "function") {
                        order.removeOrderline(l);
                    } else if (typeof order.remove_orderline === "function") {
                        order.remove_orderline(l);
                    }
                }
            }

            // Si no quedó ninguna orden seleccionada, crear una nueva en blanco
            if (!this.pos.get_order() && typeof this.pos.add_new_order === "function") {
                this.pos.add_new_order();
            }

            // Si estaba en pantalla de pago, volver a productos
            if (this.pos && typeof this.pos.showScreen === "function") {
                this.pos.showScreen("ProductScreen");
            }

            if (this.notification) {
                this.notification.add("🗑️ Orden cancelada exitosamente.", { type: "warning" });
            }
        } catch (err) {
            console.error("[POS Shortcuts] Error cancelando orden:", err);
        }
    },

    /**
     * Selecciona inmediatamente el producto 'Verduras surtidas' y abre el popup
     * de monto en Bolívares (Atajo F7)
     */
    async _triggerVerdurasSurtidas() {
        try {
            // Si estamos en pantalla de pago o recibo, volver a productos
            if (this.pos && typeof this.pos.showScreen === "function") {
                const isPayment = Boolean(document.querySelector(".payment-screen"));
                const isReceipt = Boolean(document.querySelector(".receipt-screen"));
                if (isPayment || isReceipt) {
                    this.pos.showScreen("ProductScreen");
                }
            }

            // 1. Intentar hacer click en la tarjeta visible en pantalla
            const cards = Array.from(document.querySelectorAll(".product-card, .product, article.product-card"));
            const verdurasCard = cards.find(el => {
                const text = (el.textContent || "").toUpperCase();
                return (text.includes("VERDURA") && text.includes("SURTID")) || text.includes("SURTID") || text.includes("MIX VERDURA");
            });

            if (verdurasCard) {
                verdurasCard.click();
                return;
            }

            // 2. Si no está visible en el DOM (otra página/categoría), buscar en memoria del POS
            let product = null;
            if (window.__kamaleon_pos && typeof window.__kamaleon_pos.findVerdurasSurtidasProduct === "function") {
                product = window.__kamaleon_pos.findVerdurasSurtidasProduct(this.pos);
            } else {
                product = this._findVerdurasProductFallback();
            }

            if (product) {
                const dialog = this.env?.services?.dialog;
                const pos = this.pos || this.env?.services?.pos;
                const notif = this.notification || this.env?.services?.notification;

                if (window.__kamaleon_pos && typeof window.__kamaleon_pos.promptOpenPriceBsForProduct === "function") {
                    await window.__kamaleon_pos.promptOpenPriceBsForProduct(pos, dialog, notif, product);
                } else if (typeof this.promptOpenPriceBs === "function") {
                    await this.promptOpenPriceBs(product);
                }
            } else {
                if (this.notification) {
                    this.notification.add("⚠️ Producto 'Verduras surtidas' no encontrado en el catálogo del POS.", { type: "warning" });
                }
            }
        } catch (err) {
            console.error("[POS Shortcuts] Error en atajo Verduras Surtidas:", err);
        }
    },

    /**
     * Búsqueda de respaldo de 'Verduras surtidas' en el objeto pos
     */
    _findVerdurasProductFallback() {
        if (!this.pos) return null;
        let prods = [];
        if (this.pos.models && this.pos.models['product.product']) {
            const m = this.pos.models['product.product'];
            prods = typeof m.getAll === 'function' ? m.getAll() : (m.records || []);
        } else if (this.pos.db && this.pos.db.product_by_id) {
            prods = Object.values(this.pos.db.product_by_id);
        }
        return prods.find(p => {
            const n = (p.display_name || p.name || "").toUpperCase();
            return (n.includes("VERDURA") && n.includes("SURTID")) || n.includes("SURTID") || p.x_open_price_ves;
        }) || null;
    },

    /**
     * Navega por los "cuadritos" de productos en el grid del POS usando las flechas del teclado
     */
    _navigateProductGrid(key) {
        const cards = Array.from(document.querySelectorAll(
            ".product-list article.product-card, " +
            ".products-widget article.product-card, " +
            "article.product-card, " +
            ".product-list .product-card, " +
            ".product-list .product, " +
            ".product-item"
        )).filter(el => {
            return el.offsetParent !== null && el.offsetWidth > 0;
        });

        if (!cards.length) return;

        let currentIndex = cards.findIndex(c => c.classList.contains("kamaleon-pos-product-focused"));

        if (currentIndex === -1) {
            // Primer toque de flecha: enfocar la primera tarjeta
            currentIndex = 0;
        } else {
            const cols = this._getGridColumnsCount(cards);
            if (key === "ArrowRight") {
                currentIndex = Math.min(cards.length - 1, currentIndex + 1);
            } else if (key === "ArrowLeft") {
                currentIndex = Math.max(0, currentIndex - 1);
            } else if (key === "ArrowDown") {
                currentIndex = Math.min(cards.length - 1, currentIndex + cols);
            } else if (key === "ArrowUp") {
                currentIndex = Math.max(0, currentIndex - cols);
            }
        }

        // Remover foco anterior y asignar al nuevo
        cards.forEach(c => c.classList.remove("kamaleon-pos-product-focused"));
        const target = cards[currentIndex];
        if (target) {
            target.classList.add("kamaleon-pos-product-focused");
            target.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "smooth" });
        }
    },

    /**
     * Calcula dinámicamente cuántas columnas tiene la cuadrícula según el ancho de pantalla
     */
    _getGridColumnsCount(cards) {
        if (!cards || cards.length < 2) return 1;
        const firstTop = cards[0].getBoundingClientRect().top;
        for (let i = 1; i < cards.length; i++) {
            const currentTop = cards[i].getBoundingClientRect().top;
            if (Math.abs(currentTop - firstTop) > 15) {
                return i;
            }
        }
        return cards.length;
    },

    /**
     * Selecciona y agrega al carrito el producto actualmente enfocado con las flechas
     */
    _selectFocusedProduct() {
        const focusedCard = document.querySelector(".kamaleon-pos-product-focused");
        if (focusedCard) {
            focusedCard.click();
            // IMPORTANTE: Desmarcar inmediatamente para que no quede 'pegado' el foco en ese producto
            focusedCard.classList.remove("kamaleon-pos-product-focused");
            focusedCard.style.transform = "";
            return true;
        }
        return false;
    },

    /**
     * Dispara la impresión de la boleta / recibo (Atajo F10 o P)
     */
    _triggerPrintReceipt() {
        // 1. Buscar botón de imprimir en la pantalla de recibo
        const printBtn = document.querySelector(
            ".receipt-screen .button.print, " +
            ".receipt-screen button.print, " +
            ".pos-receipt-container button.print, " +
            "button.print-receipt, " +
            ".button.print, " +
            ".btn-print, " +
            "button[title*='Imprimir'], " +
            ".print-button"
        );

        if (printBtn) {
            printBtn.click();
            printBtn.blur();
            if (document.activeElement && typeof document.activeElement.blur === "function") {
                document.activeElement.blur();
            }
            if (this.notification) {
                this.notification.add("🖨️ Imprimiendo boleta...", { type: "info" });
            }
            return;
        }

        // 2. Si la pantalla de recibo está realmente activa en el DOM, usar window.print()
        const isReceiptActive = (this.pos?.mainScreen?.name === "ReceiptScreen") ||
            Boolean(document.querySelector(".pos .receipt-screen:not(.d-none), .receipt-screen:not([style*='display: none'])"));
        if (isReceiptActive) {
            window.print();
            if (document.activeElement && typeof document.activeElement.blur === "function") {
                document.activeElement.blur();
            }
            return;
        }

        // 3. Si aún no está en la pantalla de recibo
        if (this.notification) {
            this.notification.add("La boleta se puede imprimir en la pantalla de recibo tras validar el pago (F8).", { type: "warning" });
        }
    },
});
