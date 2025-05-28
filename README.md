# 🧪 Laboratory Stock Control System

This is a simple web-based inventory management system for laboratory items, built using **Flask** and **SQLite**. It allows users to track item quantities, types, and expiration dates, with visual warnings for low stock or soon-to-expire products.

---

## 🚀 Features

* 🔐 **User authentication** (username + password)
* 📋 **Add/Edit/Delete** inventory items
* 📦 **Track product types**, quantities, and expiration dates
* 🟡 **Visual alerts**:

  * Red = expired
  * Yellow = expiring soon
  * Orange = low quantity
    
* 🔍 **Filtering and sorting** by name, type, or status
* 📄 **CSV export** with applied filters
* 📱 Responsive web interface

---

## 🖼️ Screenshots

### 💻 Dashboard

![Dashboard Screenshot](/dashboard.PNG)

### 📥 Add New Item

![Add Item Screenshot](/add_item.png)

### 📥 Add New Item

![Login Screenshot](/login.PNG)

---

## 🧰 Technologies Used

* **Python 3**
* **Flask**
* **SQLite**
* **HTML/CSS (Jinja2 templates)**
* **Bootstrap (optionally for UI styling)**

---

## 🗂️ Database

Two tables are used:

1. `usuarios` — for user login
2. `stock` — for inventory items

Example schema for stock items:

```sql
CREATE TABLE stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    tipo TEXT,
    quantidade INTEGER,
    validade TEXT
);
```

---

## 🔐 Default Login

> You can create a user by running `criar_utilizador_admin()` from the code manually:

```python
username = 'admin2'
password = '4321'
```

---

## 🏁 How to Run

### 🧪 Local Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/lab-stock-control.git
cd lab-stock-control

# (Optional) Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask werkzeug

# Run the app
python app.py
```

Then visit: `http://localhost:5000`

---

## 📤 Export to CSV

Click the **"Export"** button on the main page to download a filtered `.csv` of the stock data. Filenames reflect the filters applied, e.g.:

```
stock_nome-Ethanol_tipo-Chemicals_produtosvalidadelimite.csv
```

---

## 📦 Folder Structure

```
├── app.py
├── stock.db               # SQLite database
├── templates/             # HTML files (Jinja2)
│   ├── index.html
│   ├── login.html
│   ├── add.html
│   └── edit.html
└── README.md
```

---

## 🔒 Security Notes

* Passwords are hashed using `werkzeug.security`.
* Make sure to keep `secret_key` safe in production.
* Always run behind HTTPS in real deployments.

---

## 📄 License

This project is open-source. Use it freely in your lab or classroom environment.

---

