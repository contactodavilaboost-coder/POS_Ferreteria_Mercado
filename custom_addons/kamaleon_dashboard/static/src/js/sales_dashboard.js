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
        this.paymentMethodsCanvas = useRef("paymentMethodsChartCanvas");
        this.cashierCanvas = useRef("cashierChartCanvas");
        this.top50Canvas = useRef("top50ChartCanvas");
        this.topClientsCanvas = useRef("topClientsChartCanvas");

        const today = new Date();
        const firstDayOfYear = `${today.getFullYear()}-01-01`;
        const lastDay = today.toISOString().split('T')[0];

        this.state = useState({
            dateFrom: firstDayOfYear,
            dateTo: lastDay,
            currentPreset: 'month',
            kpis: {
                total_sales: 0,
                total_orders: 0,
                avg_ticket: 0,
                total_purchases: 0,
                total_inv_cost: 0,
                total_inv_sale: 0,
                low_stock_count: 0,
                total_collected: 0,
                collection_rate: 0,
            },
            data: null,
            low_stock_products: [],
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
            script.src = "/kamaleon_dashboard/static/lib/chart.js";
            script.onload = () => {
                console.log("[Ferretería Mercado] Local Chart.js loaded successfully");
                resolve();
            };
            script.onerror = () => {
                console.warn("[Ferretería Mercado] Local Chart.js failed, loading from CDN fallback...");
                const cdnScript = document.createElement("script");
                cdnScript.src = "https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js";
                cdnScript.onload = () => {
                    console.log("[Ferretería Mercado] CDN Chart.js loaded successfully");
                    resolve();
                };
                cdnScript.onerror = (err) => {
                    console.error("[Ferretería Mercado] Failed to load Chart.js:", err);
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
                this.scheduleRender(100);
            }
        } catch (error) {
            console.error("[Ferretería Mercado] Error fetching POS analytics data:", error);
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

    openPosOrders() {
        this.action.doAction({
            name: "Pedidos de Punto de Venta",
            type: 'ir.actions.act_window',
            res_model: 'pos.order',
            views: [
                [false, 'list'],
                [false, 'form'],
            ],
            target: 'current',
        });
    }

    openPurchases() {
        this.action.doAction({
            name: "Órdenes de Compra",
            type: 'ir.actions.act_window',
            res_model: 'purchase.order',
            views: [
                [false, 'list'],
                [false, 'form'],
            ],
            target: 'current',
        });
    }

    openInventoryQuants() {
        this.action.doAction({
            name: "Valoración de Stock en Almacén",
            type: 'ir.actions.act_window',
            res_model: 'stock.quant',
            views: [
                [false, 'list'],
                [false, 'pivot'],
            ],
            domain: [['location_id.usage', '=', 'internal']],
            target: 'current',
        });
    }

    openLowStockProducts() {
        this.action.doAction({
            name: "Artículos con Stock Crítico",
            type: 'ir.actions.act_window',
            res_model: 'product.product',
            views: [
                [false, 'list'],
                [false, 'form'],
            ],
            domain: [['qty_available', '<=', 5], ['type', '=', 'consu']],
            target: 'current',
        });
    }

    destroyChart(key) {
        if (this.chartInstances[key]) {
            try {
                this.chartInstances[key].destroy();
            } catch (e) {
                console.warn(`[Ferretería Mercado] Error destroying chart ${key}:`, e);
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
                console.warn(`[Ferretería Mercado] Chart.js not ready yet. Retrying (${this.renderAttempts}/5)...`);
                this.scheduleRender(250);
            } else {
                console.error("[Ferretería Mercado] Chart.js could not be loaded.");
            }
            return;
        }

        const data = this.state.data;

        // 1. Compras vs Ventas
        try {
            this.renderPurchasesVsSalesChart(ChartLib, data.purchases_vs_sales);
        } catch (e) { console.error("[Chart] Error in PurchasesVsSales:", e); }

        // 2. Tendencia Diaria de Ventas POS
        try {
            this.destroyChart("salesTrend");
            if (this.salesTrendCanvas.el && data.sales_trend) {
                const ctx = this.salesTrendCanvas.el.getContext("2d");
                this.chartInstances.salesTrend = new ChartLib(ctx, {
                    type: "line",
                    data: {
                        labels: data.sales_trend.labels || [],
                        datasets: [{
                            label: "Ventas POS ($)",
                            data: data.sales_trend.values || [],
                            borderColor: "#38bdf8",
                            backgroundColor: "rgba(56, 189, 248, 0.15)",
                            borderWidth: 3,
                            fill: true,
                            tension: 0.35,
                            pointBackgroundColor: "#0284c7",
                            pointRadius: 4,
                        }]
                    },
                    options: this.getCommonChartOptions()
                });
            }
        } catch (e) { console.error("[Chart] Error in SalesTrend:", e); }

        // 3. Distribución de Métodos de Pago POS
        try {
            this.destroyChart("paymentMethods");
            if (this.paymentMethodsCanvas.el && data.payment_methods) {
                const ctx = this.paymentMethodsCanvas.el.getContext("2d");
                this.chartInstances.paymentMethods = new ChartLib(ctx, {
                    type: "doughnut",
                    data: {
                        labels: data.payment_methods.labels || [],
                        datasets: [{
                            data: data.payment_methods.values || [],
                            backgroundColor: ["#10b981", "#38bdf8", "#f59e0b", "#8b5cf6", "#ec4899", "#64748b"],
                            borderWidth: 0,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom', labels: { color: '#f8fafc', font: { size: 12 } } },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ` $${(ctx.raw || 0).toLocaleString('es-VE', {minimumFractionDigits: 2})}`
                                }
                            }
                        }
                    }
                });
            }
        } catch (e) { console.error("[Chart] Error in PaymentMethods:", e); }

        // 4. Rendimiento por Caja / Cajero
        try {
            this.destroyChart("cashierSales");
            if (this.cashierCanvas.el && data.cashier_sales) {
                const ctx = this.cashierCanvas.el.getContext("2d");
                this.chartInstances.cashierSales = new ChartLib(ctx, {
                    type: "bar",
                    data: {
                        labels: data.cashier_sales.labels || [],
                        datasets: [{
                            label: "Total Ventas ($)",
                            data: data.cashier_sales.values || [],
                            backgroundColor: "rgba(148, 163, 184, 0.85)",
                            borderColor: "#94a3b8",
                            borderWidth: 1,
                            borderRadius: 6,
                        }]
                    },
                    options: this.getCommonChartOptions()
                });
            }
        } catch (e) { console.error("[Chart] Error in CashierSales:", e); }

        // 5. Top 50 Artículos de Ferretería
        try {
            this.destroyChart("top50");
            if (this.top50Canvas.el && data.top_products) {
                const ctx = this.top50Canvas.el.getContext("2d");
                const labels = data.top_products.map(p => p.name);
                const values = data.top_products.map(p => p.qty);

                this.chartInstances.top50 = new ChartLib(ctx, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [{
                            label: "Unidades Despachadas",
                            data: values,
                            backgroundColor: "rgba(56, 189, 248, 0.85)",
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
                                    label: (ctx) => ` Despachados: ${(ctx.raw || 0).toLocaleString()} uds`
                                }
                            }
                        }
                    }
                });
            }
        } catch (e) { console.error("[Chart] Error in Top50:", e); }

        // 6. Top Clientes de Mostrador
        try {
            this.destroyChart("topClients");
            if (this.topClientsCanvas.el && data.top_clients) {
                const ctx = this.topClientsCanvas.el.getContext("2d");
                const labels = data.top_clients.map(c => c.name);
                const values = data.top_clients.map(c => c.total);

                this.chartInstances.topClients = new ChartLib(ctx, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [{
                            label: "Compras Totales ($)",
                            data: values,
                            backgroundColor: "rgba(129, 140, 248, 0.85)",
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
                                    callback: (val) => '$' + (val || 0).toLocaleString('es-VE', {minimumFractionDigits: 0})
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
                                    label: (ctx) => ` Compras: $${(ctx.raw || 0).toLocaleString('es-VE', {minimumFractionDigits: 2})}`
                                }
                            }
                        }
                    }
                });
            }
        } catch (e) { console.error("[Chart] Error in TopClients:", e); }
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
                        label: 'Ventas POS ($)',
                        data: data.sales || [],
                        backgroundColor: 'rgba(56, 189, 248, 0.85)',
                        borderColor: '#38bdf8',
                        borderWidth: 1,
                        borderRadius: 6,
                    },
                    {
                        label: 'Compras Ferretería ($)',
                        data: data.purchases || [],
                        backgroundColor: 'rgba(245, 158, 11, 0.85)',
                        borderColor: '#f59e0b',
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
                        labels: { color: '#f8fafc', font: { family: 'Inter, sans-serif', weight: 'bold' } }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + (context.raw || 0).toLocaleString('es-VE', {minimumFractionDigits: 2});
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
