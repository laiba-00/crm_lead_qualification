/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillStart, useState } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class ManagerDashboard extends Component {
    static template = "crm_lead_qualification.ManagerDashboard";

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            kpis: {
                total_leads: 0,
                total_hot_leads: 0,
                total_won: 0,
                total_lost: 0,
                conversion_rate: 0,
            },
            agent_performance: [],
            pipeline_data: [],
            closer_performance: [],
            loading: true,
            chart_loaded: false,
        });

        onWillStart(async () => {
            // Load Chart.js from CDN
            await loadJS("https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js");
            await this.loadDashboardData();
        });

        onMounted(() => {
            if (this.state.pipeline_data.length) {
                this.renderPipelineChart();
            }
        });
    }

    async loadDashboardData() {
        try {
            const data = await this.rpc(
                "/crm_lead_qualification/dashboard_data", {}
            );
            this.state.kpis = data.kpis;
            this.state.agent_performance = data.agent_performance;
            this.state.pipeline_data = data.pipeline_data;
            this.state.closer_performance = data.closer_performance;
            this.state.loading = false;
        } catch (error) {
            console.error("Dashboard data load error:", error);
            this.state.loading = false;
        }
    }

    renderPipelineChart() {
        const canvas = document.getElementById("pipelineChart");
        if (!canvas || !this.state.pipeline_data.length) return;
        if (typeof Chart === "undefined") return;

        // Destroy existing chart if any
        const existing = Chart.getChart(canvas);
        if (existing) existing.destroy();

        const labels = this.state.pipeline_data.map(d => d.stage);
        const counts = this.state.pipeline_data.map(d => d.count);

        new Chart(canvas, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Leads",
                    data: counts,
                    backgroundColor: [
                        "#7C3AED", "#8B5CF6", "#A78BFA",
                        "#C4B5FD", "#DDD6FE", "#6D28D9", "#5B21B6"
                    ],
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 },
                    }
                }
            }
        });
    }

    async refreshDashboard() {
        this.state.loading = true;
        await this.loadDashboardData();
        this.renderPipelineChart();
    }
}

registry.category("actions").add(
    "crm_lead_qualification.manager_dashboard",
    ManagerDashboard
);