# CRM Lead Qualification — Odoo 17 Custom Module

A production-ready Odoo 17 module that implements a structured two-department sales workflow, separating **Lead Qualification** from **Closing** with role-based access control, a custom transfer wizard, and a real-time OWL manager dashboard.

---

## 🚀 Features

### Role-Based Security
| Role | Access |
|---|---|
| **Administrator** | Full access to everything |
| **Manager** | View all leads, assign/reassign, full reporting |
| **Sales Agent** | Own assigned leads only — read-only after transfer |
| **Closer** | Only transferred Hot Leads assigned to them |

### Two-Stage Sales Pipeline
- **Lead Qualification Team** — 7 stages: New Lead → Assigned → Attempting Contact → Contacted → Follow-Up → Qualified → Hot Lead
- **Closing Team** — 4 stages: Transferred to Closing Team → Customer Setup → Active Customer → Lost

### Smart Workflow
- Lead auto-moves to **"Assigned"** stage when manager assigns a Sales Agent
- Agent qualifies lead through stages and transfers via a **custom wizard** (picks the closer)
- After transfer: lead disappears from agent's active pipeline
- Agent retains **read-only "My Qualified Leads"** dashboard to track outcomes
- Manager can also **directly assign referral leads** to Closing Team (bypasses qualification)

### OWL Manager Dashboard
Built with Odoo 17's OWL framework and Chart.js:
- **KPI Cards** — Active Cold Leads, Hot Leads Generated, Won, Lost, Conversion Rate
- **Pipeline Stage Chart** — Bar chart of leads per qualification stage
- **Agent Performance Table** — Per-agent breakdown with conversion rates
- **Closing Team Performance** — Win rate per closer

---

## 📦 Installation

1. Copy the `crm_lead_qualification` folder to your Odoo `custom_addons` directory
2. Restart the Odoo server
3. Go to **Settings → Apps → Update Apps List**
4. Search for **"CRM Lead Qualification"** and click **Install**

---

## ⚙️ Configuration

After installation:

1. Go to **Settings → Users**
2. Assign each user their role under **Access Rights → Lead Qualification**:
   - Department Head / Admin → **Administrator**
   - Team Lead → **Manager**
   - Sales Reps → **Sales Agent**
   - Deal Closers → **Closer**

---

## 🔧 Technical Stack

- **Backend:** Python, Odoo 17 ORM
- **Frontend:** OWL Framework, XML QWeb
- **Security:** Custom `ir.rule` record rules, `res.groups`
- **Dashboard:** OWL Component + Chart.js (CDN)
- **Database:** PostgreSQL

---

## 📁 Module Structure

```
crm_lead_qualification/
├── controllers/        # HTTP JSON controller for dashboard data
├── models/             # crm.lead extension
├── wizard/             # Hot Lead transfer wizard
├── security/           # Groups + record rules + model access
├── data/               # Teams and stages data
├── views/              # Agent, Closer, Manager views + menus
├── report/             # Pivot/graph reporting views
└── static/             # OWL dashboard component + CSS
```

---

## 👩‍💻 Author

**Laiba Waseem**
Odoo 17 Developer | BSCS — Virtual University of Pakistan

## 📄 License

LGPL-3
