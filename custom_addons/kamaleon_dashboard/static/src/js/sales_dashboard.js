/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class SalesDashboardAction extends Component {
    static template = "kamaleon_dashboard.SalesDashboardAction";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        
        this.purchasesVsSalesCanvas = useRef("purchasesVsSalesCanvas");
        this.salesTrendCanvas = useRef("salesTrendChartCanvas");
        this.collectionCanvas = useRef("collectionChartCanvas");
        this.agingCanvas = useRef("agingChartCanvas");
        this.topClientsCanvas = useRef("topClientsChartCanvas");
        this.top50Canvas = useRef("top50ChartCanvas");
        this.routesCanvas = useRef("routesChartCanvas");
        this.sellersCanvas = useRef("sellersChartCanvas");
        this.fillRateCanvas = useRef("fillRateChartCanvas");

        const today = new Date();
        const firstDayOfYear = `${today.getFullYear()}-01-01`;
        const lastDay = today.toISOString().split('T')[0];

        this.state = useState({
            dateFrom: firstDayOfYear,
            dateTo: lastDay,
            currentPreset: 'all',
            kpis: {
                total_sales: 0,
                total_purchases: 0,
                total_invoiced: 0,
                total_collected: 0,
                total_orders: 0,
                avg_ticket: 0,
                collection_rate: 0,
                fill_rate: 0,
                total_overdue: 0,
                overdue_count: 0,
                low_stock_count: 0,
                total_inv_cost: 0,
                total_inv_sale: 0,
            },
            data: null,
            low_stock_products: [],
            overdue_invoices: [],
            isLoading: true,
        });

        this.chartInstances = {};
        this.renderAttempts = 0;

        onWillStart(async () => {
            await this.loadChartJsLibrary();
            await this.fetchAnalyticsData();
        });

        onMounted(() => {
            this.scheduleRender(150);
        });

        onWillUnmount(() => {
            this.destroyAllCharts();
        });
    }

    async loadChartJsLibrary() {
        if (window.Chart) return;
        return new Promise((resolve) => {
            const script = document.createElement("script");
            script.src = "/kamaleon_erp/static/lib/chart.js";
            script.onload = () => {
                console.log("[Kamaleon ERP] Local Chart.js loaded successfully");
                resolve();
            };
            script.onerror = () => {
                console.warn("[Kamaleon ERP] Local Chart.js failed, loading from CDN fallback...");
                const cdnScript = document.createElement("script");
                cdnScript.src = "https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js";
                cdnScript.onload = () => {
                    console.log("[Kamaleon ERP] CDN Chart.js loaded successfully");
                    resolve();
                };
                cdnScript.onerror = (err) => {
                    console.error("[Kamaleon ERP] Failed to load Chart.js:", err);
                    resolve();
                };
                document.head.appendChild(cdnScript);
            };
            document.head.appendChild(script);
        });
    }

    async fetchAnalyticsData(preset = null) {
        this.state.isLoading = true;
        try {
            const data = await this.orm.call(
                "kamaleon.sales.dashboard",
                "get_dashboard_analytics_data",
                [this.state.dateFrom, this.state.dateTo, preset || this.state.currentPreset]
            );
            if (data) {
                this.state.kpis = data.kpis || this.state.kpis;
                this.state.data = data;
                this.state.dateFrom = data.date_from || this.state.dateFrom;
                this.state.dateTo = data.date_to || this.state.dateTo;
                this.state.low_stock_products = data.low_stock_products || [];
                this.state.overdue_invoices = data.overdue_invoices || [];
                this.scheduleRender(100);
            }
        } catch (error) {
            console.error("[Kamaleon ERP] Error fetching sales analytics data:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async onPresetClick(preset) {
        this.state.currentPreset = preset;
        await this.fetchAnalyticsData(preset);
    }

    async onDateChange() {
        this.state.currentPreset = null;
        await this.fetchAnalyticsData();
    }

    formatNumber(num) {
        return (num || 0).toLocaleString("es-VE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    openOverdueInvoices() {
        const todayStr = (this.state.data && this.state.data.today) || new Date().toISOString().split('T')[0];
        const domain = [
            ['move_type', '=', 'out_invoice'],
            ['state', '=', 'posted'],
            ['payment_state', 'in', ['not_paid', 'partial', 'in_payment']],
            ['amount_residual', '>', 0],
            ['invoice_date_due', '!=', false],
            ['invoice_date_due', '<', todayStr],
        ];

        if (this.state.data && this.state.data.rz_partner_ids && this.state.data.rz_partner_ids.length > 0) {
            domain.push(['partner_id', 'not in', this.state.data.rz_partner_ids]);
        }

        this.action.doAction({
            name: "Cartera Vencida — Cuentas por Cobrar en Mora",
            type: 'ir.actions.act_window',
            res_model: 'account.move',
            views: [
                [false, 'list'],
                [false, 'form'],
            ],
            domain: domain,
            context: {
                search_default_posted: 1,
            }
        });
    }

    openInvoice(invoiceId) {
        if (!invoiceId) return;
        this.action.doAction({
            name: "Factura",
            type: "ir.actions.act_window",
            res_model: "account.move",
            res_id: invoiceId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    destroyChart(key) {
        if (this.chartInstances[key]) {
            try {
                this.chartInstances[key].destroy();
            } catch (e) {
                console.warn(`[Kamaleon ERP] Error destroying chart ${key}:`, e);
            }
            delete this.chartInstances[key];
        }
    }

    destroyAllCharts() {
        for (const key of Object.keys(this.chartInstances)) {
            this.destroyChart(key);
        }
    }

    scheduleRender(delay = 150) {
        setTimeout(() => {
            this.renderAllCharts();
        }, delay);
    }

    getChartConstructor() {
        return window.Chart || (typeof Chart !== "undefined" ? Chart : null);
    }

    renderAllCharts() {
        if (!this.state.data) return;

        const ChartLib = this.getChartConstructor();
        if (!ChartLib) {
            if (this.renderAttempts < 5) {
                this.renderAttempts++;
                console.warn(`[Kamaleon ERP] Chart.js not ready yet. Retrying (${this.renderAttempts}/5)...`);
                this.scheduleRender(250);
            } else {
                console.error("[Kamaleon ERP] Chart.js could not be loaded.");
            }
            return;
        }

        const data = this.state.data;

        // 0. Compras vs Ventas
        try {
            this.renderPurchasesVsSalesChart(ChartLib, data.purchases_vs_sales);
        } catch (e) { console.error("[Chart] Error in PurchasesVsSales:", e); }

        // 1. Tendencia de Ventas del Mes
        try {
            this.destroyChart("salesTrend");
            if (this.salesTrendCanvas.el && data.sales_trend) {
                const ctx = this.salesTrendCanvas.el.getContext("2d");
                this.chartInstances.salesTrend = new ChartLib(ctx, {
                    type: "line",
                    data: {
                        labels: data.sales_trend.labels || [],
                        datasets: [{
                            label: "Ventas ($)",
                            data: data.sales_trend.data || [],
                            borderColor: "#34d399",
                            backgroundColor: "rgba(52, 211, 153, 0.15)",
                            borderWidth: 3,
                            fill: true,
                            tension: 0.35,
                            pointBackgroundColor: "#059669",
                            pointRadius: 4,
                        }]
                    },
                    options: this.getCommonChartOptions()
                });
            }
        } catch (e) { console.error("[Chart] Error in SalesTrend:", e); }

        // 2. Cobranza Exitosa del Mes
        try {
            this.destroyChart("collection");
            if (this.collectionCanvas.el && data.collection) {
                const ctx = this.collectionCanvas.el.getContext("2d");
                this.chartInstances.collection = new ChartLib(ctx, {
                    type: "doughnut",
                    data: {
                        labels: data.collection.labels || [],
                        datasets: [{
                            data: data.collection.data || [],
                            backgroundColor: ["#3b82f6", "#10b981", "#ef4444"],
                            borderWidth: 0,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom', labels: { color: '#ffffff', font: { size: 12 } } },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ` $${(ctx.raw || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`
                                }
                            }
                        }
                    }
                });
            }
        } catch (e) { console.error("[Chart] Error in Collection:", e); }

        // 3. Cartera Vencida por Antigüedad
        try {
            this.destroyChart("aging");
            if (this.agingCanvas.el && data.aging_receivables) {
                const ctx = this.agingCanvas.el.getContext("2d");
                this.chartInstances.aging = new ChartLib(ctx, {
                    type: "bar",
                    data: {
                        labels: data.aging_receivables.labels || [],
                        datasets: [{
                            label: "Monto Pendiente ($)",
                            data: data.aging_receivables.data || [],
                            backgroundColor: data.aging_receivables.colors || ["#10b981", "#3b82f6", "#f59e0b", "#ef4444"],
                            borderRadius: 8,
                        }]
                    },
                    options: {
                        ...this.getCommonChartOptions(),
                        onClick: () => {
                            this.openOverdueInvoices();
                        }
                    }
                });
            }
        } catch (e) { console.error("[Chart] Error in Aging:", e); }

        // 4. Top 30 Clientes VIP
        try {
            this.destroyChart("topClients");
            if (this.topClientsCanvas.el && data.top_clients) {
                const ctx = this.topClientsCanvas.el.getContext("2d");
                this.chartInstances.topClients = new ChartLib(ctx, {
                    type: "bar",
                    data: {
                        labels: data.top_clients.labels || [],
                        datasets: [{
                            label: "Compras Totales ($)",
                            data: data.top_clients.data || [],
                            backgroundColor: "rgba(56, 189, 248, 0.85)",
                            borderRadius: 6,
                            categoryPercentage: 0.85,
                            barPercentage: 0.9,
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                ticks: {
                                    color: "#94a3b8",
                                    callback: (val) => '$' + (val || 0).toLocaleString('en-US', {minimumFractionDigits: 0})
                                },
                                grid: { color: "rgba(255,255,255,0.05)" }
                            },
                            y: {
                                ticks: { color: "#ffffff", font: { size: 11, weight: 'bold' } },
                                grid: { display: false }
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ` Compras: $${(ctx.raw || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`
                                }
                            }
                        }
                    }
                });
            }
        } catch (e) { console.error("[Chart] Error in TopClients:", e); }

        // 5. Top 50 Productos Más Vendidos
        try {
            this.destroyChart("top50");
            if (this.top50Canvas.el && data.top_50_products) {
                const ctx = this.top50Canvas.el.getContext("2d");
                this.chartInstances.top50 = new ChartLib(ctx, {
                    type: "bar",
                    data: {
                        labels: data.top_50_products.labels || [],
                        datasets: [{
                            label: "Unidades Vendidas",
                            data: data.top_50_products.qty_data || [],
                            backgroundColor: "rgba(52, 211, 153, 0.8)",
                            borderRadius: 5,
                            categoryPercentage: 0.85,
                            barPercentage: 0.9,
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                            y: {
                                ticks: { color: "#ffffff", font: { size: 10, weight: 'bold' } },
                                grid: { display: false }
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ` Vendidos: ${(ctx.raw || 0).toLocaleString()} uds`
                                }
                            }
                        }
                    }
                });
            }
        } catch (e) { console.error("[Chart] Error in Top50:", e); }

        // 6. Ventas por Ruta
        try {
            this.destroyChart("routes");
            if (this.routesCanvas.el && data.routes) {
                const ctx = this.routesCanvas.el.getContext("2d");
                this.chartInstances.routes = new ChartLib(ctx, {
                    type: "bar",
                    data: {
                        labels: data.routes.labels || [],
                        datasets: [{
                            label: "Monto ($)",
                            data: data.routes.data || [],
                            backgroundColor: "rgba(99, 102, 241, 0.85)",
                            borderRadius: 8,
                        }]
                    },
                    options: this.getCommonChartOptions()
                });
            }
        } catch (e) { console.error("[Chart] Error in Routes:", e); }

        // 7. Ventas por Vendedor
        try {
            this.destroyChart("sellers");
            if (this.sellersCanvas.el) {
                const ctx = this.sellersCanvas.el.getContext("2d");
                this.chartInstances.sellers = new ChartLib(ctx, {
                    type: "bar",
                    data: {
                        labels: (data.sellers && data.sellers.labels) || [],
                        datasets: [{
                            label: "Monto ($)",
                            data: (data.sellers && data.sellers.data) || [],
                            backgroundColor: "rgba(168, 85, 247, 0.85)",
                            borderRadius: 8,
                        }]
                    },
                    options: this.getCommonChartOptions()
                });
            }
        } catch (e) { console.error("[Chart] Error in Sellers:", e); }

        // 8. Fill Rate - Pedido vs Entregado (en $)
        try {
            this.destroyChart("fillRate");
            if (this.fillRateCanvas.el && data.fill_rate) {
                const ctx = this.fillRateCanvas.el.getContext("2d");
                const ordVal = (data.fill_rate && data.fill_rate.ordered) || 0;
                const delVal = (data.fill_rate && data.fill_rate.delivered) || 0;
                const pct = (data.fill_rate && data.fill_rate.percent) || 0;
                this.chartInstances.fillRate = new ChartLib(ctx, {
                    type: "bar",
                    data: {
                        labels: [
                            `Monto Solicitado ($ ${this.formatNumber(ordVal)})`,
                            `Monto Entregado ($ ${this.formatNumber(delVal)})`
                        ],
                        datasets: [{
                            label: `Monto en Dólares ($) — Fill Rate: ${pct}%`,
                            data: [ordVal, delVal],
                            backgroundColor: ["#f59e0b", "#10b981"],
                            borderRadius: 8,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true,
                                labels: { color: '#ffffff', font: { weight: 'bold' } }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `${context.dataset.label.split(' — ')[0]}: $${(context.raw || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                            y: {
                                ticks: {
                                    color: "#ffffff",
                                    callback: function(value) { return '$' + (value || 0).toLocaleString(); }
                                },
                                grid: { color: "rgba(255,255,255,0.08)" }
                            }
                        }
                    }
                });
            }
        } catch (e) { console.error("[Chart] Error in FillRate:", e); }
    }

    renderPurchasesVsSalesChart(ChartLib, data) {
        const canvas = this.purchasesVsSalesCanvas.el;
        if (!canvas || !data) return;

        this.destroyChart("purchasesVsSales");
        const ctx = canvas.getContext("2d");

        this.chartInstances.purchasesVsSales = new ChartLib(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Ventas Facturadas ($)',
                        data: data.sales_data || [],
                        backgroundColor: 'rgba(16, 185, 129, 0.85)',
                        borderColor: '#10b981',
                        borderWidth: 1,
                        borderRadius: 6,
                    },
                    {
                        label: 'Compras Facturadas ($)',
                        data: data.purchases_data || [],
                        backgroundColor: 'rgba(59, 130, 246, 0.85)',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        borderRadius: 6,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: '#e2e8f0', font: { family: 'Inter, sans-serif', weight: 'bold' } }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + (context.raw || 0).toLocaleString('en-US', {minimumFractionDigits: 2});
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    y: {
                        ticks: {
                            color: '#94a3b8',
                            callback: function(value) { return '$' + (value || 0).toLocaleString(); }
                        },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    }
                }
            }
        });
    }

    getCommonChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                y: { ticks: { color: "#ffffff" }, grid: { color: "rgba(255,255,255,0.08)" } }
            },
            plugins: { legend: { labels: { color: "#ffffff" } } }
        };
    }
}

registry.category("actions").add("kamaleon_sales_dashboard_action", SalesDashboardAction);
